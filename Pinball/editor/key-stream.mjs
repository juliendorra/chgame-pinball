// Serialize USB press/release edges and expose every state for at least one
// hardware frame. Heartbeats still refresh the console's 500 ms dead-man timer.
export class DeviceKeyStream {
 constructor(send,failed,delay=ms=>new Promise(resolve=>setTimeout(resolve,ms))){this.send=send;this.failed=failed;this.delay=delay;this.pending=[];this.running=false;}
 push(mask){
  if(this.pending.at(-1)!==mask)this.pending.push(mask);
  if(this.pending.length>30)this.pending=[0];
  if(!this.running)this.flush();
 }
 async flush(){
  this.running=true;
  try{while(this.pending.length){await this.send(this.pending.shift());await this.delay(18);}}
  catch(e){this.pending=[];this.failed(e);}
  finally{this.running=false;}
 }
 clear(){this.pending=[];}
}
