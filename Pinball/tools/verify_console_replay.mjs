// Actual console protocol + actual WASM engine. No independently timed inputs
// are invented for the browser: compare at acknowledged pause boundaries.
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
import {BrowserDevice,unhex} from '../editor/serial.mjs';
import {WasmEngine,readState} from '../editor/wasm-engine.mjs';
import {decode,encode,copy} from '../editor/model.mjs';
const [python,port,distArg,outArg]=process.argv.slice(2);
if(!outArg)throw new Error('Use: node verify_console_replay.mjs PYTHON PORT DIST REPORT');
const dist=path.resolve(distArg),out=path.resolve(outArg);
const bridge=spawn(python,['-u','-c',String.raw`
import serial,sys,threading
s=serial.Serial(sys.argv[1],115200,timeout=.2);s.dtr=True
def send():
 for line in sys.stdin.buffer:
  s.write(line);s.flush()
threading.Thread(target=send,daemon=True).start()
while True:
 line=s.readline()
 if line:sys.stdout.buffer.write(line);sys.stdout.buffer.flush()
`,port],{stdio:['pipe','pipe','inherit']});
const lines=[],waiters=[];let stopped=false;
createInterface({input:bridge.stdout}).on('line',line=>{const waiter=waiters.shift();if(waiter)waiter.resolve(line);else lines.push(line);});
bridge.on('exit',()=>{stopped=true;for(const w of waiters.splice(0))w.reject(new Error('Serial bridge stopped'));});
const d=new BrowserDevice();d.tail=Promise.resolve();
d.writer={write:bytes=>new Promise((resolve,reject)=>bridge.stdin.write(bytes,e=>e?reject(e):resolve()))};
d.line=()=>lines.length?Promise.resolve(lines.shift()):new Promise((resolve,reject)=>{
 if(stopped)return reject(new Error('Serial bridge stopped'));
 const waiter={resolve:line=>{clearTimeout(timer);resolve(line);},reject};
 const timer=setTimeout(()=>{const at=waiters.indexOf(waiter);if(at>=0)waiters.splice(at,1);reject(new Error('Console timeout'));},3000);
 waiters.push(waiter);
});
globalThis.requestAnimationFrame=()=>1;globalThis.cancelAnimationFrame=()=>{};
const {default:create}=await import(pathToFileURL(path.join(dist,'engine.mjs')));
const wasm=fs.readdirSync(dist).find(f=>f.endsWith('.wasm'));
const m=await create({wasmBinary:fs.readFileSync(path.join(dist,wasm))});m._pb_init();
const engine=new WasmEngine(m,()=>{},()=>{},e=>{throw e;});engine.setFollowing(true);
const report={schema:1,checks:[]};let original,initial;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function drain(){while(engine.replay.length)engine.frame(performance.now());}
d.onReplay=event=>{engine.consoleEvent(event);drain();};
async function state(){return (await d.request('V')).at(-1).split(' ').slice(2).map(Number);}
async function compare(label){
 await d.pause(true);drain();const actual=await state(),web=readState(m);
 const names=['id','score','lives','ticks','xq','yq','vx','vy','left','right','shooter','camera','zoom','paused'];
 for(let i=0;i<names.length;++i)assert.equal(web[names[i]]>>>0,actual[i]>>>0,`${label}: ${names[i]}`);
 const rng=unhex((await d.request('Z')).at(-1).slice(10)),view=new DataView(rng.buffer,rng.byteOffset);
 assert.equal(web.seed,view.getUint32(0,true),label+': seed');assert.equal(web.rng,view.getUint32(4,true),label+': rng');
 report.checks.push({label,frame:engine.appliedFrame,ticks:web.ticks,score:web.score,fields:names.length+2});
 await d.pause(false);
}
try{
 report.hello=(await d.request('?')).at(-1);
 initial=await state();original=unhex((await d.request('T')).at(-1).slice(10));
 const board=decode(original);report.board=board.title;report.build=m._pb_build()>>>0;
 await d.beginFollow(original,12345,report.build,1);drain();await compare('shared reset');
 for(let phase=0;phase<3;++phase){
  for(let i=0;i<32;++i){
   await d.keys([8,0,16,18,2,0,1,0][i%8]);await sleep(24+i%3*12);await d.pullTrace();
  }
  await compare('sampled keyboard stream '+phase);
  if(phase===0){const edited=copy(board);edited.objects.unshift({kind:'bumper',group:0,x:64,y:110,u:7,v:280,value:100});
   await d.upload(encode(edited),2);await compare('live geometry insertion');await d.upload(original,3);}
  if(phase===1){await d.restart(987654321);await compare('seeded restart');await d.place(60,160);await compare('ball placement');}
 }
 await d.inspectStorage();await compare('SD read pause and resume');
 await d.endFollow();const before=await state();await sleep(250);const after=await state();
 assert.ok(after[3]>before[3],'console must keep playing when following ends');
 report.independent_console_continues=true;report.result='passed';
}catch(e){report.result='failed';report.error=e.stack;throw e;}
finally{
 try{await d.endFollow();await d.request('X');await d.request('Q 1');if(original)await d.upload(original);await d.restart(12345);await d.request('Q '+(initial?.[13]||0));}catch(e){report.restore_error=e.message;}
 bridge.stdin.end();bridge.kill();fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');
}
console.log(JSON.stringify(report));
