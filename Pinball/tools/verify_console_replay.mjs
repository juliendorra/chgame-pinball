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
import {PlaySession} from '../editor/play-session.mjs';
import {decode,encode,copy} from '../editor/model.mjs';
const [python,port,distArg,outArg,boardPath]=process.argv.slice(2);
if(!outArg)throw new Error('Use: node verify_console_replay.mjs PYTHON PORT DIST REPORT [BOARD.PBT]');
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
let frames=[],measuring=false,failure;
const engine=new WasmEngine(m,()=>{
 if(measuring)frames.push({time:performance.now(),applied:engine.appliedFrame,received:engine.receivedFrame});
},()=>{},error=>{failure??=error;});
const play=new PlaySession({engine,seed:()=>12345,onError:error=>{failure??=error;}});
const renderTimer=setInterval(()=>engine.frame(performance.now()),1000/60);
const report={schema:1,checks:[]};let original,initial;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function state(){return (await d.run(()=>d.request('V'))).at(-1).split(' ').slice(2).map(Number);}
async function compare(label){
 await d.pause(true);
 const pauseFrame=d.replayFrame,deadline=performance.now()+4000;
 while(engine.appliedFrame<pauseFrame||!readState(m).paused){
  if(failure)throw failure;
  assert.ok(performance.now()<deadline,`${label}: replay did not reach the pause`);
  await sleep(5);
 }
 const actual=await state(),web=readState(m);
 const names=['id','score','lives','ticks','xq','yq','vx','vy','left','right','shooter','camera','zoom','paused'];
 for(let i=0;i<names.length;++i)assert.equal(web[names[i]]>>>0,actual[i]>>>0,`${label}: ${names[i]}`);
 const rng=unhex((await d.run(()=>d.request('Z'))).at(-1).slice(10)),view=new DataView(rng.buffer,rng.byteOffset);
 assert.equal(web.seed,view.getUint32(0,true),label+': seed');assert.equal(web.rng,view.getUint32(4,true),label+': rng');
 report.checks.push({label,frame:engine.appliedFrame,ticks:web.ticks,score:web.score,fields:names.length+2});
 await d.pause(false);
}
try{
 report.hello=(await d.request('?')).at(-1);
 initial=await state();original=unhex((await d.request('T')).at(-1).slice(10));
 const testBytes=boardPath?fs.readFileSync(boardPath):original;
 const board=decode(testBytes);report.board=board.title;report.build=m._pb_build()>>>0;
 await play.connect(d,board,1);
 if(failure)throw failure;
 await compare('shared reset');
 await d.keys(8);await sleep(85);await d.keys(0);await sleep(250);
 frames=[];measuring=true;
 const start=performance.now();
 for(let i=0;i<30;++i){
  await d.keys([16,0,2,0][i%4]);
  await sleep(160);
  if(failure)throw failure;
 }
 const duration=(performance.now()-start)/1000;
 measuring=false;
 const drawn=frames.filter((frame,i)=>!i||frame.applied!==frames[i-1].applied);
 const gaps=drawn.slice(1).map((frame,i)=>frame.time-drawn[i].time).sort((a,b)=>a-b);
 const backlog=drawn.map(frame=>frame.received-frame.applied).sort((a,b)=>a-b);
 const p95=values=>values[Math.floor(0.95*(values.length-1))];
 report.pacing={seconds:duration,drawHz:drawn.length/duration,p95GapMs:p95(gaps),p95QueuedTicks:p95(backlog)};
 await compare('paced USB replay');
 assert.ok(report.pacing.drawHz>=52,'expected at least 52 replay draws per second');
 assert.ok(report.pacing.p95GapMs<=38,'expected at least 95% of gaps within two display frames');
 for(let phase=0;phase<3;++phase){
  for(let i=0;i<32;++i){
   await d.keys([8,0,16,18,2,0,1,0][i%8]);await sleep(24+i%3*12);
  }
  await compare('sampled keyboard stream '+phase);
  if(phase===0){const edited=copy(board);edited.objects.unshift({kind:'bumper',group:0,x:64,y:110,u:7,v:280,value:100});
   await d.upload(encode(edited),2);await compare('live geometry insertion');await d.upload(testBytes,3);}
  if(phase===1){await d.restart(987654321);await compare('seeded restart');await d.place(60,160);await compare('ball placement');}
 }
 await d.inspectStorage();await compare('SD read pause and resume');
 await play.disconnect(board,4);const before=await state();await sleep(250);const after=await state();
 assert.ok(after[3]>before[3],'console must keep playing when following ends');
 report.independent_console_continues=true;report.result='passed';
}catch(e){report.result='failed';report.error=e.stack;throw e;}
finally{
 clearInterval(renderTimer);
 try{await play.disconnect();await d.request('X');await d.request('Q 1');if(original)await d.upload(original);await d.restart(12345);await d.request('Q '+(initial?.[13]||0));
  if(original)assert.deepEqual(unhex((await d.request('T')).at(-1).slice(10)),original,'RAM board was restored');
 }catch(e){report.restore_error=e.message;report.result='failed';process.exitCode=1;}
 bridge.stdin.end();bridge.kill();fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');
}
console.log(JSON.stringify(report));
