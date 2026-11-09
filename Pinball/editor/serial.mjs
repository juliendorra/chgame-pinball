// Direct browser connection to the same release protocol as the local bridge.
import {BoardCard} from './card.mjs';
import {fnv} from './model.mjs';
export class BrowserDevice {
 async connect(){
  this.port=await navigator.serial.requestPort({filters:[{usbVendorId:0x16c0,usbProductId:0x27dd}]});
  try{await this.port.open({baudRate:115200});await this.port.setSignals({dataTerminalReady:true});this.reader=this.port.readable.getReader();this.writer=this.port.writable.getWriter();this.buffer='';this.lines=[];this.waiters=[];this.stopped=false;this.tail=Promise.resolve();this.readLoop();await this.run(()=>this.request('?'));}
  catch(e){await this.close();if(e.name==='NetworkError')throw new Error('CHGame USB is in use. Close other editor tabs or serial apps, then reconnect.');throw e;}return this;
 }
 async readLoop(){
  const text=new TextDecoder();
  try{while(!this.stopped){const {value,done}=await this.reader.read();if(done)break;this.buffer+=text.decode(value,{stream:true});let at;while((at=this.buffer.indexOf('\n'))>=0){let line=this.buffer.slice(0,at).trim();this.buffer=this.buffer.slice(at+1);const waiter=this.waiters.shift();if(waiter)waiter.resolve(line);else this.lines.push(line);}}}
  catch(e){this.readError=e;}finally{this.stopped=true;for(const w of this.waiters.splice(0))w.reject(this.readError||new Error('CHGame disconnected.'));}
 }
 line(){if(this.lines.length)return Promise.resolve(this.lines.shift());if(this.stopped)return Promise.reject(new Error('CHGame disconnected.'));return new Promise((resolve,reject)=>{let w={resolve:v=>{clearTimeout(timer);resolve(v);},reject:e=>{clearTimeout(timer);reject(e);}};let timer=setTimeout(()=>{this.waiters=this.waiters.filter(v=>v!==w);reject(new Error('CHGame did not answer. Install Pinball 1.4, then reconnect.'));},2500);this.waiters.push(w);});}
 run(fn){const p=this.tail.then(fn);this.tail=p.catch(()=>{});return p;}
 async request(cmd){
  await this.writer.write(new TextEncoder().encode('@'+cmd+'\n'));const lines=[];
  for(let i=0;i<130;i++){const line=await this.line();if(line.startsWith('LIVE ERR'))throw new Error('CHGame refused '+cmd.split(' ')[0]);if(line.startsWith('LIVE BOARD '))lines.push(line);else if(line.startsWith('LIVE ')){if(cmd==='?'&&!line.startsWith('LIVE HELLO 1.4'))throw new Error('Install Pinball 1.4 or newer.');if(cmd==='?')this.capabilities=new Set(line.split(' '));return [...lines,line];}}
  throw new Error('Unrecognized CHGame reply.');
 }
 requireBoardSupport(bytes){if(bytes[7]&1&&!this.capabilities?.has('RUBBER'))throw new Error('Update Pinball on CHGame to use editable rubber slingshots, then reconnect.');}
 async transfer(bytes,lba=null){if(lba===null)this.requireBoardSupport(bytes);await this.request(lba===null?'B '+bytes.length:'W '+lba);for(let at=0;at<bytes.length;at+=32)await this.request(`D ${at} ${hex(bytes.slice(at,at+32))}`);await this.request(lba===null?'C':'F '+fnv(bytes));}
 upload(bytes){return this.run(async()=>{await this.transfer(bytes);const returned=unhex((await this.request('T')).at(-1).slice(10));if(hex(returned)!==hex(bytes))throw new Error('CHGame RAM readback differs.');return {bytes:bytes.length,verified:true};});}
 save(stem,bytes){return this.run(async()=>{
  this.requireBoardSupport(bytes);
  const values=(await this.request('V')).at(-1).split(' ').slice(2).map(Number),paused=values[13];
  if(values.length!==15)throw new Error('Unexpected CHGame state reply');
  await this.request('X');await this.request('Q 1');
  try{
   await this.request('I');
   const card=await BoardCard.open({read:async lba=>unhex((await this.request('S '+lba)).at(-1).slice(10)),write:(lba,data)=>this.transfer(data,lba)});
   const result=await card.save(stem,bytes);await this.request('L');await this.transfer(bytes);return result;
  }finally{await this.request('Q '+paused);}
 });}
 boards(){return this.run(async()=>{const list=await this.request('L'),result=[];for(const line of list){if(!line.startsWith('LIVE BOARD '))continue;const [,index,file]=line.match(/^LIVE BOARD (\d+) (.*)$/);const reply=await this.request('G '+index);result.push({index:Number(index),file:file.trim(),data:unhex(reply.at(-1).slice(10))});}return result;});}
 keys(mask){if(this.keyBusy)return Promise.resolve();this.keyBusy=true;return this.run(()=>this.request('K '+mask)).finally(()=>this.keyBusy=false);}
 restart(seed=0){return this.run(async()=>{await this.request(seed?'R '+seed:'R');if(seed){const data=unhex((await this.request('Z')).at(-1).slice(10));if(data.length!==8||new DataView(data.buffer,data.byteOffset,4).getUint32(0,true)!==(seed>>>0))throw new Error('CHGame seed readback differs. Install Pinball 1.4.9 or newer.');}});}
 pause(paused){return this.run(()=>this.request('Q '+Number(paused)));}
 place(x,y){return this.run(()=>this.request(`P ${x},${y}`));}
 async close(){
  if(this.stopped&& !this.port)return;this.stopped=true;
  try{if(this.reader){await this.reader.cancel();this.reader.releaseLock();}}catch{}
  try{this.writer?.releaseLock();await this.port?.close();}catch{}
  this.port=null;
 }
}
export const hex=b=>Array.from(b,v=>v.toString(16).padStart(2,'0')).join('');
export const unhex=s=>Uint8Array.from(s.match(/../g)||[],v=>parseInt(v,16));
