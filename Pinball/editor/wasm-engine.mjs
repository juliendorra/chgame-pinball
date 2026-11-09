import {encode} from './model.mjs';
export const STATE_FIELDS=['id','height','objects','score','lives','ticks','xq','yq','vx','vy','left','right','shooter','launching','camera','zoom','paused','over','ramp','hold','save','lanes','target','mult','tilt','zoom_ticks','ramp_camera','pop','pop_ticks','pop_kind','shake_level','shake_window','shake_ticks','shake_x','shake_y','shake_direction','searches','ramps','kickbacks','launch_held','frame','balls','shooter_flap','seed','rng','bonus','bonus_ticks','bonus_arg','bonus_next','bonus_next_arg','effective_mult','lane_goal','lane_groups','spin_q16'];
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
 send(m){if(m.type==='keys')this.keys.push(m.mask);else if(m.type==='board')this.pending=m;else this.commands.push(m);}
 frame(now){
  if(!this.running)return;
  // Do not catch up a hidden tab with seconds of uncontrolled physics.
  this.accumulator+=this.last===null?1000/60:Math.min(100,now-this.last);this.last=now;
  const m=this.module;let changed=false;
  try{
   // The validated commit and every command run between complete physics ticks.
   if(this.pending){const p=this.pending;this.pending=null;const bytes=encode(p.board);m.HEAPU8.set(bytes,m._pb_input());if(!m._pb_apply(bytes.length))throw new Error('Game rejected this board.');this.loaded=true;changed=true;this.onApplied(p.revision);}
   for(const c of this.commands.splice(0)){
    if(c.type==='restart')m._pb_restart(c.seed||0);
    else if(c.type==='pause')m._pb_pause(!readState(m).paused);
    else if(c.type==='place')m._pb_place(c.x,c.y,0,0);
    changed=true;
   }
   while(this.accumulator>=1000/60){if(this.loaded){m._pb_step(this.keys.sample());changed=true;}this.accumulator-=1000/60;}
   if(changed&&this.loaded){const state=readState(m),at=m._pb_render(),size=m._pb_render_size();this.onFrame(state,m.HEAPU8.slice(at,at+size));}
  }catch(e){this.onError(e);}
  this.raf=requestAnimationFrame(this.frame);
 }
 release(){this.keys.clear();}
 close(){this.running=false;cancelAnimationFrame(this.raf);this.keys.clear();}
}
