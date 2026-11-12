import {test} from 'node:test';
import assert from 'node:assert/strict';
import {BrowserDevice,hex} from '../serial.mjs';
import {BoardCard} from '../card.mjs';
import {fnv,encode} from '../model.mjs';
import fs from 'node:fs';
test('Automatic SD saves never pause active console play, including the launch lane',async()=>{
 for(const shooter of [0,1]){
  const d=new BrowserDevice(),calls=[];d.tail=Promise.resolve();d.capabilities=new Set(['PBT2']);
  d.request=async command=>{calls.push(command);return ['LIVE STATE '+[1,0,3,22,100,200,0,0,0,0,shooter,0,256,0,22].join(' ')];};
  await assert.rejects(()=>d.save('TEST',new Uint8Array(96),{automatic:true}),e=>e.code==='play_active');
  assert.deepEqual(calls,['V'],'no release, pause, card initialization or write');
 }
});
test('Automatic SD saves proceed when paused or out of balls and retain the previous pause state',async()=>{
 const open=BoardCard.open;
 try{for(const [lives,paused] of [[3,1],[0,0]]){
  const d=new BrowserDevice(),calls=[];d.tail=Promise.resolve();d.capabilities=new Set(['PBT2']);
  d.request=async command=>{calls.push(command);return [command==='V'?'LIVE STATE '+[1,0,lives,22,100,200,0,0,0,0,0,0,256,paused,22].join(' '):'LIVE OK'];};
  BoardCard.open=async()=>({saveProtected:async(file,bytes,options)=>{assert.equal(options.automatic,undefined);return {verified:true};}});
  assert.equal((await d.save('TEST',new Uint8Array(96),{automatic:true})).verified,true);
  assert.deepEqual(calls,['V','X','Q 1','I','L','Q '+paused]);
 }}finally{BoardCard.open=open;}
});
test('sector transfers use the bounded raw-sector protocol and exact checksum',async()=>{
 const d=new BrowserDevice(),calls=[];d.request=async command=>{calls.push(command);return ['LIVE OK'];};
 const bytes=Uint8Array.from({length:512},(_,i)=>i&255);await d.transfer(bytes,123);
 assert.equal(calls[0],'W 123');assert.equal(calls.length,18);
 for(let i=0;i<16;i++)assert.equal(calls[i+1],`D ${i*32} ${hex(bytes.slice(i*32,(i+1)*32))}`);
 assert.equal(calls.at(-1),'F '+fnv(bytes));
});
test('failed direct SD initialization restores the previous pause state on the same connection',async()=>{
 for(const paused of [0,1]){
  const d=new BrowserDevice(),calls=[];d.tail=Promise.resolve();d.capabilities=new Set(['PBT2']);
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

test('PBT2 boards reject an older console before RAM or SD writes',async()=>{
 const d=new BrowserDevice();d.tail=Promise.resolve();let requests=0;d.request=async()=>{requests++;return ['LIVE OK'];};
 const bytes=new Uint8Array(100);bytes[4]=2;
 await assert.rejects(()=>d.upload(bytes),/Update Pinball/);await assert.rejects(()=>d.save('TEST',bytes),/Update Pinball/);assert.equal(requests,0);
 d.capabilities=new Set(['PBT2']);assert.doesNotThrow(()=>d.requireBoardSupport());
});

test('SD saving restores pause and never switches the console RAM board',async()=>{
 const d=new BrowserDevice(),calls=[];d.tail=Promise.resolve();d.capabilities=new Set(['PBT2']);
 d.request=async command=>{calls.push(command);return [command==='V'?'LIVE STATE '+[1,0,3,22,100,200,0,0,0,0,0,0,256,0,22].join(' '):'LIVE OK'];};
 const open=BoardCard.open;BoardCard.open=async()=>({saveProtected:async()=>({verified:true})});
 try{const result=await d.save('TEST',new Uint8Array(96),{volume:'test',expected:null});assert.equal(result.verified,true);assert.deepEqual(calls,['V','X','Q 1','I','L','Q 0']);}finally{BoardCard.open=open;}
});
test('console mutation replies flush input history before the matching browser operation',async()=>{
 const d=new BrowserDevice(),events=[],commands=[];
 const board=JSON.parse(fs.readFileSync(new URL('../../boards/tables.json',import.meta.url)))[0],bytes=encode(board);
 Object.assign(d,{tail:Promise.resolve(),following:true,replayBuild:123,replaySession:456,replayFrame:0,
  capabilities:new Set(['TRACE','PBT2']),onReplay:e=>events.push(e)});
 let reply,frame=0;
 d.writer={write:async data=>{
  const c=new TextDecoder().decode(data).trim().slice(1);commands.push(c);
  if(['C','Q 1','Q 0','P 40,100','R 999'].includes(c)){
   const b=Buffer.alloc(11);b.writeUInt32LE(++frame);b.writeUInt32LE(123,4);b[9]=16;b[10]=1;reply='LIVE DATA '+b.toString('hex');
  }else if(c==='T')reply='LIVE DATA '+hex(bytes);
  else if(c==='Z')reply='LIVE DATA e7030000e7030000';
  else if(c==='V')reply='LIVE STATE '+[1,0,3,22,100,200,0,0,0,0,0,0,256,0,22].join(' ');
  else reply='LIVE OK';
 }};d.line=async()=>reply;
 await d.upload(bytes,7);await d.pause(true);await d.place(40,100);await d.restart(999);
 assert.deepEqual(events.map(e=>e.type),['steps','board','steps','pause','steps','place','steps','restart']);
 assert.equal(events[1].revision,7);assert.equal(events[2].frame,2);assert.ok(events.every(e=>e.session===456));
 const open=BoardCard.open;BoardCard.open=async()=>({saveProtected:async()=>({verified:true})});
 try{await d.save('TEST',bytes,{});}finally{BoardCard.open=open;}
 assert.deepEqual(events.slice(-4).map(e=>e.type),['steps','pause','steps','pause']);
 assert.equal(events.at(-3).paused,1);assert.equal(events.at(-1).paused,0);
 assert.deepEqual(commands.slice(-6),['V','X','Q 1','I','L','Q 0']);
});
