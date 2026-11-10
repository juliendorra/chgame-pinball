// Direct browser connection to the same release protocol as the local bridge.
import {BoardCard} from './card.mjs';
import {fnv,decode} from './model.mjs';
export function parseTrace(line,build,previous=0){
 if(!/^LIVE DATA [0-9a-f]+$/.test(line)||(line.length-10)%2)throw new Error('Invalid console replay reply.');
 const bytes=unhex(line.slice(10));
 if(bytes.length<9||(bytes.length-9)%2)throw new Error('Truncated console input history.');
 const view=new DataView(bytes.buffer,bytes.byteOffset),frame=view.getUint32(0,true);
 if(view.getUint32(4,true)!==(build>>>0))throw new Error('The console and web game builds differ. Update Pinball on CHGame to use console play.');
 if(bytes[8]&1)throw new Error('Console input history overflowed. Restart console play to synchronize again.');
 if(bytes[8]&2)throw new Error('The console left the table. Restart console play to synchronize again.');
 const runs=[];let count=0;
 for(let at=9;at<bytes.length;at+=2){if(!bytes[at+1])throw new Error('Invalid console input run.');runs.push({mask:bytes[at],count:bytes[at+1]});count+=bytes[at+1];}
 if(((previous+count)>>>0)!==frame)throw new Error('Console input frames were lost. Restart console play to synchronize again.');
 return {type:'steps',frame,runs};
}
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
  for(let i=0;i<130;i++){const line=await this.line();if(line.startsWith('LIVE ERR'))throw new Error('CHGame refused '+cmd.split(' ')[0]);if(line.startsWith('LIVE BOARD '))lines.push(line);else if(line.startsWith('LIVE ')){if(cmd==='?'&&!line.startsWith('LIVE HELLO 1.4'))throw new Error('Install Pinball 1.4 or newer.');if(cmd==='?')this.capabilities=new Set(line.split(' '));if(this.following&&["C","R","Q","P"].includes(cmd.split(" ")[0])){this.trace(line);if(cmd.startsWith("Q "))this.replay({type:"pause",paused:Number(cmd.slice(2))});}return [...lines,line];}}
  throw new Error('Unrecognized CHGame reply.');
 }
 requireBoardSupport(bytes){if(bytes[7]&1&&!this.capabilities?.has('RUBBER'))throw new Error('Update Pinball on CHGame to use editable rubber slingshots, then reconnect.');}
 async transfer(bytes,lba=null){if(lba===null)this.requireBoardSupport(bytes);await this.request(lba===null?'B '+bytes.length:'W '+lba);for(let at=0;at<bytes.length;at+=32)await this.request(`D ${at} ${hex(bytes.slice(at,at+32))}`);await this.request(lba===null?'C':'F '+fnv(bytes));}
 replay(event){this.onReplay?.({...event,session:this.replaySession});}
 trace(line){const event=parseTrace(line,this.replayBuild,this.replayFrame);this.replayFrame=event.frame;this.replay(event);}
 beginFollow(bytes,seed,build,revision){return this.run(async()=>{
  if(!this.capabilities?.has('TRACE'))throw new Error('Update Pinball on CHGame to use console play. Web-only play and live edits remain available.');
  this.following=false;await this.request('Y 0');await this.request('X');await this.request('Q 1');
  try{
   await this.transfer(bytes);const reply=await this.request('Y '+seed);
   const initial=parseTrace(reply.at(-1),build,0);if(initial.frame)throw new Error('Unexpected console replay start.');
   this.replaySession=seed;this.replayBuild=build;this.replayFrame=0;this.following=true;
   this.replay({type:'reset',board:decode(bytes),seed,revision});
  }catch(error){await this.request('Y 0').catch(()=>{});await this.request('Q 0').catch(()=>{});throw error;}
 });}
 pullTrace(){return this.run(async()=>{if(this.following)this.trace((await this.request('Y 1')).at(-1));});}
 endFollow(){this.following=false;return this.run(async()=>{await this.request('K 0');if(this.capabilities?.has('TRACE'))await this.request('Y 0');});}
 upload(bytes,revision){return this.run(async()=>{await this.transfer(bytes);if(this.following)this.replay({type:'board',board:decode(bytes),revision});const returned=unhex((await this.request('T')).at(-1).slice(10));if(hex(returned)!==hex(bytes))throw new Error('CHGame RAM readback differs.');return {bytes:bytes.length,verified:true};});}
 withCard(task){return this.run(async()=>{
  const values=(await this.request('V')).at(-1).split(' ').slice(2).map(Number),paused=values[13];
  if(values.length!==15)throw new Error('Unexpected CHGame state reply');
  await this.request('X');await this.request('Q 1');
  try{
   await this.request('I');
   const card=await BoardCard.open({read:async lba=>unhex((await this.request('S '+lba)).at(-1).slice(10)),write:(lba,data)=>this.transfer(data,lba)});
   return await task(card);
  }finally{await this.request('Q '+paused);}
 });}
 inspectStorage(){return this.withCard(card=>card.inventory());}
 async save(stem,bytes,options){this.requireBoardSupport(bytes);return this.withCard(async card=>{const result=await card.saveProtected(stem,bytes,options);await this.request('L');return result;});}
 revertSd(stem,options){return this.withCard(async card=>{const result=await card.revertProtected(stem,options);await this.request('L');return result;});}
 checkpointSd(stem,options){return this.withCard(card=>card.checkpointProtected(stem,options));}
 boards(){return this.run(async()=>{const list=await this.request('L'),result=[];for(const line of list){if(!line.startsWith('LIVE BOARD '))continue;const [,index,file]=line.match(/^LIVE BOARD (\d+) (.*)$/);const reply=await this.request('G '+index);result.push({index:Number(index),file:file.trim(),data:unhex(reply.at(-1).slice(10))});}return result;});}
 keys(mask){if(this.keyBusy)return Promise.resolve();this.keyBusy=true;return this.run(()=>this.request('K '+mask)).finally(()=>this.keyBusy=false);}
 restart(seed=0){return this.run(async()=>{await this.request(seed?'R '+seed:'R');if(this.following)this.replay({type:'restart',seed});if(seed){const data=unhex((await this.request('Z')).at(-1).slice(10));if(data.length!==8||new DataView(data.buffer,data.byteOffset,4).getUint32(0,true)!==(seed>>>0))throw new Error('CHGame seed readback differs. Install Pinball 1.4.9 or newer.');}});}
 pause(paused){return this.run(()=>this.request('Q '+Number(paused)));}
 place(x,y){return this.run(async()=>{await this.request(`P ${x},${y}`);if(this.following)this.replay({type:'place',x,y});});}
 async close(){
  if(this.stopped&& !this.port)return;this.stopped=true;
  try{if(this.reader){await this.reader.cancel();this.reader.releaseLock();}}catch{}
  try{this.writer?.releaseLock();await this.port?.close();}catch{}
  this.port=null;
 }
}
export const hex=b=>Array.from(b,v=>v.toString(16).padStart(2,'0')).join('');
export const unhex=s=>Uint8Array.from(s.match(/../g)||[],v=>parseInt(v,16));
