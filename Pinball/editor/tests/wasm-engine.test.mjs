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
