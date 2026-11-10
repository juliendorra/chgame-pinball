import {encode} from './model.mjs';

const TRACE_POLL_MS=16;

// The console keeps its own clock. Only this browser replay waits for input
// samples; independent play never forwards keyboard or play commands.
export class PlaySession{
 constructor({engine,onChange=()=>{},onError=()=>{},seed=()=>{const v=new Uint32Array(1);crypto.getRandomValues(v);return Math.max(2,v[0]);},schedule=(fn,ms)=>setTimeout(fn,ms),cancel=id=>clearTimeout(id)}){
  Object.assign(this,{engine,onChange,onError,seed,schedule,cancel});this.mode='web';this.epoch=0;
 }
 get controlsConsole(){return this.mode==='console';}
 get followsConsole(){return this.mode==='console'||this.mode==='starting'||this.mode==='error';}
 changed(){this.onChange(this);}
 send(event){
  if(!this.followsConsole||event.type==='board'){this.engine.send(event);return;}
  if(!this.controlsConsole||!this.device)return;
  if(event.type==='restart')return this.device.restart(event.seed||0);
  if(event.type==='pause')return this.device.pause(event.paused);
  if(event.type==='place')return this.device.place(event.x,event.y);
 }
 async connect(device,board,revision,separate=false){
  this.device=device;device.onReplay=event=>{if(event.session===this.session&&this.followsConsole)this.engine.consoleEvent(event);};
  if(separate||!device.capabilities?.has('TRACE')){
   this.mode='web';this.notice=separate?'':'Update Pinball on CHGame to enable console play.';
   if(device.capabilities?.has('TRACE'))await device.endFollow();this.changed();return;
  }
  return this.start(board,revision);
 }
 async start(board,revision){
  const device=this.device;if(!device)return;
  const epoch=++this.epoch;this.cancel(this.timer);this.mode='starting';this.error=null;this.notice='';
  this.session=Math.max(2,this.seed()>>>0);this.engine.setFollowing(true);this.changed();
  try{
   await device.beginFollow(encode(board),this.session,this.engine.build,revision);
   if(epoch!==this.epoch)return;
   this.mode='console';this.changed();this.poll(epoch);
  }catch(error){if(epoch===this.epoch)this.failed(error);}
 }
 poll(epoch){
  this.timer=this.schedule(async()=>{
   if(epoch!==this.epoch||!this.controlsConsole)return;
   try{await this.device.pullTrace();if(epoch===this.epoch&&this.controlsConsole)this.poll(epoch);}
   catch(error){if(epoch===this.epoch)this.failed(error);}
  },TRACE_POLL_MS);
 }
 failed(error){this.mode='error';this.error=error.message;this.cancel(this.timer);this.engine.setFollowing(true);this.device?.endFollow().catch(()=>{});this.changed();this.onError(error);}
 async separate(board,revision){
  ++this.epoch;this.cancel(this.timer);this.mode='web';this.error=null;this.notice='';
  this.engine.setFollowing(false);if(board)this.engine.send({type:'board',board,revision});this.changed();
  if(this.device)await this.device.endFollow();
 }
 async disconnect(board,revision){const device=this.device;this.device=null;if(device)device.onReplay=null;await this.separate(board,revision);if(device&&!device.stopped)await device.endFollow().catch(()=>{});}
}
