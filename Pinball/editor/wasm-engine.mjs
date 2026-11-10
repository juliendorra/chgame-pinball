import {encode} from './model.mjs';
const TICK_MS=1000/60;
const REPLAY_BUFFER_MS=2*TICK_MS;
const REPLAY_CATCH_UP_TICKS=8;
export const STATE_FIELDS=['id','height','objects','score','lives','ticks','xq','yq','vx','vy','left','right','shooter','launching','camera','zoom','paused','over','ramp','hold','save','lanes','target','mult','tilt','zoom_ticks','ramp_camera','pop','pop_ticks','pop_kind','shake_level','shake_window','shake_ticks','shake_x','shake_y','shake_direction','searches','ramps','kickbacks','launch_held','frame','balls','shooter_flap','seed','rng','bonus','bonus_ticks','bonus_arg','bonus_next','bonus_next_arg','effective_mult','lane_goal','lane_groups','spin_q16','view_x','view_y','view_w','view_h'];
// Preserve sub-frame taps. Each transition is sampled for at least one tick.
export class KeyQueue {
 constructor(){this.clear();}
 clear(){this.pending=[];this.latest=this.mask=0;}
 push(mask){mask&=255;if(mask!==this.latest){this.latest=mask;this.pending.push(mask);if(this.pending.length>30)this.clear();}}
 sample(){if(this.pending.length)this.mask=this.pending.shift();return this.mask;}
}
export function readState(m){
 const at=m._pb_state()>>2,result={};STATE_FIELDS.forEach((name,i)=>result[name]=m.HEAP32[at+i]);
 result.id>>>=0;result.seed>>>=0;result.rng>>>=0;result.x=Math.trunc(result.xq/256);result.y=Math.trunc(result.yq/256);return result;
}
export class WasmEngine {
 static async create(onFrame,onApplied,onError){
  const {default:create}=await import('./engine.mjs');const module=await create();module._pb_init();
  return new WasmEngine(module,onFrame,onApplied,onError);
 }
 constructor(module,onFrame,onApplied,onError){this.module=module;this.onFrame=onFrame;this.onApplied=onApplied;this.onError=onError;this.keys=new KeyQueue();this.commands=[];this.last=null;this.accumulator=0;this.running=true;this.frame=this.frame.bind(this);this.raf=requestAnimationFrame(this.frame);}
 send(m){
  if(m.type==='keys')this.keys.push(m.mask);
  else if(m.type==='board'){
   if(this.following)this.draft=m;
   else this.pending=m;
  }else this.commands.push(m);
 }
 get build(){return this.module._pb_build()>>>0;}
 setFollowing(on){this.following=on;this.replay=[];this.appliedFrame=this.receivedFrame=0;this.nextReplayTick=null;this.pending=null;this.draft=null;this.drawnDraft=null;this.commands=[];this.keys.clear();this.last=null;this.accumulator=0;}
 consoleEvent(event){
  if(!this.following)return;
  if(event.type==='steps'){this.receivedFrame=event.frame;for(const run of event.runs)this.replay.push({type:'run',...run});}
  else this.replay.push(event);
 }
 applyBoard(board,revision){
  const m=this.module,bytes=encode(board);
  m.HEAPU8.set(bytes,m._pb_input());
  if(!m._pb_apply(bytes.length))throw new Error('Game rejected this board.');
  if(this.draft&&this.draft.revision<=revision)this.draft=null;
  this.loaded=true;
  this.onApplied(revision);
 }
 frame(now){
  if(!this.running)return;
  // Do not catch up a hidden tab with seconds of uncontrolled physics.
  this.accumulator+=this.last===null?TICK_MS:Math.min(100,now-this.last);this.last=now;
  const m=this.module;let changed=false;
  try{
   if(this.following){
    const queued=(this.receivedFrame-this.appliedFrame)>>>0;
    if(!queued)this.nextReplayTick=null;
    else if(this.nextReplayTick===null)this.nextReplayTick=now+REPLAY_BUFFER_MS;
    // Space out the received ticks at 60 Hz. Catch up faster after a long
    // USB transaction or a hidden tab, while retaining every input edge.
    const catchingUp=queued>REPLAY_CATCH_UP_TICKS;
    let budget=catchingUp?12:queued?Math.max(0,1+Math.floor((now-this.nextReplayTick+0.01)/TICK_MS)):0;
    budget=Math.min(budget,12);
    while(this.replay.length){
     const event=this.replay[0];
     if(event.type==='run'){
      if(!budget)break;
      m._pb_step(event.mask);
      this.appliedFrame=(this.appliedFrame+1)>>>0;
      this.nextReplayTick+=TICK_MS;
      --budget;
      if(--event.count===0)this.replay.shift();
     }
     else{
      this.replay.shift();
      if(event.type==='board'||event.type==='reset')this.applyBoard(event.board,event.revision);
      if(event.type==='reset'){m._pb_pause(1);m._pb_step(0);m._pb_restart(event.seed);this.appliedFrame=0;}
      else if(event.type==='restart')m._pb_restart(event.seed||0);
      else if(event.type==='pause')m._pb_pause(event.paused);
      else if(event.type==='place')m._pb_place(event.x,event.y,0,0);
     }
     changed=true;
    }
    if(catchingUp)this.nextReplayTick=now+TICK_MS;
    this.accumulator=0;
   }else{
   // The validated commit and every command run between complete physics ticks.
   if(this.pending){const p=this.pending;this.pending=null;this.applyBoard(p.board,p.revision);changed=true;}
   for(const c of this.commands.splice(0)){
    if(c.type==='restart')m._pb_restart(c.seed||0);
    else if(c.type==='pause')m._pb_pause(!readState(m).paused);
    else if(c.type==='place')m._pb_place(c.x,c.y,0,0);
    changed=true;
   }
   while(this.accumulator>=TICK_MS){if(this.loaded){m._pb_step(this.keys.sample());changed=true;}this.accumulator-=TICK_MS;}
   }
   const draft=this.draft??null;
   if(this.loaded&&(changed||draft!==(this.drawnDraft??null))){
    const state=readState(m);
    if(draft){
     const bytes=encode(draft.board);
     m.HEAPU8.set(bytes,m._pb_input());
     const at=m._pb_render_draft(bytes.length);
     if(!at)throw new Error('Game rejected this draft preview.');
     const size=(draft.board.height+24)*64+32;
     this.onFrame(state,m.HEAPU8.slice(at,at+size),draft.board);
    }else{
     const at=m._pb_render(),size=m._pb_render_size();
     this.onFrame(state,m.HEAPU8.slice(at,at+size));
    }
    this.drawnDraft=draft;
   }
  }catch(e){this.onError(e);}
  this.raf=requestAnimationFrame(this.frame);
 }
 release(){this.keys.clear();}
 close(){this.running=false;cancelAnimationFrame(this.raf);this.keys.clear();}
}
