import {test} from 'node:test';
import assert from 'node:assert/strict';
import {BrowserDevice,hex} from '../serial.mjs';
import {fnv} from '../model.mjs';
test('sector transfers use the bounded raw-sector protocol and exact checksum',async()=>{
 const d=new BrowserDevice(),calls=[];d.request=async command=>{calls.push(command);return ['LIVE OK'];};
 const bytes=Uint8Array.from({length:512},(_,i)=>i&255);await d.transfer(bytes,123);
 assert.equal(calls[0],'W 123');assert.equal(calls.length,18);
 for(let i=0;i<16;i++)assert.equal(calls[i+1],`D ${i*32} ${hex(bytes.slice(i*32,(i+1)*32))}`);
 assert.equal(calls.at(-1),'F '+fnv(bytes));
});
test('failed direct SD initialization restores the previous pause state on the same connection',async()=>{
 for(const paused of [0,1]){
  const d=new BrowserDevice(),calls=[];d.tail=Promise.resolve();
  d.request=async command=>{calls.push(command);if(command==='V')return ['LIVE STATE '+[1,0,3,22,100,200,0,0,0,0,0,0,256,paused,22].join(' ')];if(command==='I')throw new Error('Card unavailable');return ['LIVE OK'];};
  await assert.rejects(()=>d.save('TEST',new Uint8Array()),/Card unavailable/);
  assert.deepEqual(calls,['V','X','Q 1','I','Q '+paused]);
 }
});
test('seeded restart verifies all 32 seed bits via little-endian readback',async()=>{
 const d=new BrowserDevice(),calls=[];d.tail=Promise.resolve();d.request=async c=>{calls.push(c);return [c==='Z'?'LIVE DATA 2143658721436587':'LIVE OK'];};
 await d.restart(0x87654321);assert.deepEqual(calls,['R 2271560481','Z']);
 d.request=async c=>[c==='Z'?'LIVE DATA 01000000':'LIVE OK'];await assert.rejects(()=>d.restart(123),/seed readback differs/);
});

test('Editable-rubber boards reject an older console before RAM or SD writes',async()=>{
 const d=new BrowserDevice();d.tail=Promise.resolve();let requests=0;d.request=async()=>{requests++;return ['LIVE OK'];};
 const bytes=new Uint8Array(96);bytes[7]=1;
 await assert.rejects(()=>d.upload(bytes),/Update Pinball/);await assert.rejects(()=>d.save('TEST',bytes),/Update Pinball/);assert.equal(requests,0);
 d.capabilities=new Set(['RUBBER']);assert.doesNotThrow(()=>d.requireBoardSupport(bytes));
 assert.doesNotThrow(()=>new BrowserDevice().requireBoardSupport(new Uint8Array(96)),'old files still work on old firmware');
});
