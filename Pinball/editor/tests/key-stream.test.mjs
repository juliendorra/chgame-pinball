import test from 'node:test';
import assert from 'node:assert/strict';
import {DeviceKeyStream} from '../key-stream.mjs';
test('USB holds every rapid press/release for a hardware frame and keeps heartbeats',async()=>{
 const sent=[],delays=[];let release;
 const stream=new DeviceKeyStream(async mask=>{sent.push(mask);if(sent.length===1)await new Promise(r=>release=r);},assert.fail,async ms=>delays.push(ms));
 for(const mask of [1,0,32,0,1,0])stream.push(mask);
 release();await new Promise(r=>setImmediate(r));
 assert.deepEqual(sent,[1,0,32,0,1,0]);assert.deepEqual(delays,[18,18,18,18,18,18]);
 stream.push(0);await new Promise(r=>setImmediate(r));assert.equal(sent.at(-1),0);assert.equal(sent.length,7);
});
test('USB disconnect discards queued states and reports error once',async()=>{
 let reject;const sent=[],errors=[];
 const stream=new DeviceKeyStream(mask=>{sent.push(mask);return new Promise((_,r)=>reject=r);},e=>errors.push(e));
 stream.push(1);stream.push(0);reject(new Error('Disconnected'));await new Promise(r=>setImmediate(r));
 assert.equal(errors.length,1);assert.deepEqual(sent,[1]);assert.equal(stream.pending.length,0);assert.equal(stream.running,false);
});
