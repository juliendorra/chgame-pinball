import {test} from 'node:test';
import assert from 'node:assert/strict';
import {KeyQueue,WasmEngine} from '../wasm-engine.mjs';
import {encode} from '../model.mjs';
import fs from 'node:fs';
const board=JSON.parse(fs.readFileSync(new URL('../../boards/tables.json',import.meta.url)))[0];
test('short key edges and simultaneous flips survive render coalescing',()=>{
 const q=new KeyQueue();for(const mask of [16,18,2,0,1,0])q.push(mask);
 assert.deepEqual(Array.from({length:6},()=>q.sample()),[16,18,2,0,1,0]);assert.equal(q.sample(),0);
 for(let i=0;i<50;i++)q.push(i%2);q.clear();assert.equal(q.sample(),0);
});
test('latest live edit commits between ticks, with gameplay continuing through edits',()=>{
 const events=[],oldRAF=globalThis.requestAnimationFrame;globalThis.requestAnimationFrame=()=>1;
 try{
  const heap=new Int32Array(2048),bytes=new Uint8Array(heap.buffer);let loaded;
  const module={HEAP32:heap,HEAPU8:bytes,_pb_input:()=>1024,_pb_state:()=>0,_pb_apply:n=>{loaded=n;events.push('apply');heap[0]=board.id;heap[1]=board.height;return 1;},_pb_step:mask=>{events.push(['step',mask]);heap[5]++;},_pb_render:()=>0,_pb_render_size:()=>0};
  const engine=new WasmEngine(module,()=>events.push('render'),revision=>events.push(['applied',revision]),e=>{throw e;});
  engine.send({type:'board',board,revision:1});engine.send({type:'board',board,revision:2});engine.send({type:'keys',mask:18});engine.frame(0);
  assert.equal(loaded,encode(board).length);assert.deepEqual(events.slice(0,4),['apply',['applied',2],['step',18],'render']);
  events.length=0;engine.send({type:'board',board,revision:3});engine.frame(17);
  assert.ok(events.some(e=>Array.isArray(e)&&e[0]==='step'&&e[1]===18),'dragging must not release or pause flips');
  engine.release();engine.frame(34);assert.ok(events.some(e=>Array.isArray(e)&&e[0]==='step'&&e[1]===0));
 }finally{globalThis.requestAnimationFrame=oldRAF;}
});
test('console replay waits for sampled ticks and preserves edits, pauses and restarts in order',()=>{
 const oldRAF=globalThis.requestAnimationFrame;globalThis.requestAnimationFrame=()=>1;
 try{
  const events=[],heap=new Int32Array(4096);
  const module={HEAP32:heap,HEAPU8:new Uint8Array(heap.buffer),_pb_input:()=>2048,_pb_state:()=>0,
   _pb_apply:()=>{events.push('board');return 1;},_pb_step:mask=>events.push(['step',mask]),
   _pb_restart:seed=>events.push(['restart',seed]),_pb_pause:on=>events.push(['pause',on]),
   _pb_place:(x,y)=>events.push(['place',x,y]),_pb_render:()=>0,_pb_render_size:()=>0};
  const engine=new WasmEngine(module,()=>{},()=>{},e=>{throw e;});engine.setFollowing(true);
  engine.frame(0);engine.frame(10000);assert.deepEqual(events,[],'elapsed browser time cannot invent console ticks');
  engine.consoleEvent({type:'reset',board,seed:123,revision:1});
  engine.consoleEvent({type:'steps',frame:3,runs:[{mask:16,count:2},{mask:0,count:1}]});
  engine.consoleEvent({type:'board',board,revision:2});
  engine.consoleEvent({type:'pause',paused:1});engine.consoleEvent({type:'place',x:40,y:100});
  engine.consoleEvent({type:'restart',seed:456});
  engine.consoleEvent({type:'steps',frame:4,runs:[{mask:2,count:1}]});engine.frame(10017);
  assert.deepEqual(events,['board',['pause',1],['step',0],['restart',123],
   ['step',16],['step',16],['step',0],'board',['pause',1],['place',40,100],['restart',456],['step',2]]);
  assert.equal(engine.appliedFrame,4);assert.equal(engine.receivedFrame,4);
  const done=events.length;engine.frame(20000);assert.equal(events.length,done);
  engine.consoleEvent({type:'steps',frame:34,runs:[{mask:18,count:30}]});engine.frame(20017);
  assert.equal(engine.appliedFrame,16,'one RAF catches up at most twelve input frames');
  engine.frame(20034);engine.frame(20051);assert.equal(engine.appliedFrame,34);
  engine.consoleEvent({type:'steps',frame:40,runs:[{mask:2,count:6}]});
  engine.setFollowing(false);engine.send({type:'keys',mask:16});engine.frame(20068);
  assert.deepEqual(events.at(-1),['step',16],'separate play discards stale console samples');
 }finally{globalThis.requestAnimationFrame=oldRAF;}
});
