import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {PlaySession} from '../play-session.mjs';
import {parseTrace} from '../serial.mjs';
const board=JSON.parse(fs.readFileSync(new URL('../../boards/tables.json',import.meta.url)))[0];
const packet=(frame,runs=[],flags=0,build=123)=>{
 const b=Buffer.alloc(9+runs.length);b.writeUInt32LE(frame>>>0);b.writeUInt32LE(build>>>0,4);b[8]=flags;b.set(runs,9);return 'LIVE DATA '+b.toString('hex');
};
test('console input runs require matching build, complete sequence and intact history',()=>{
 assert.deepEqual(parseTrace(packet(5,[16,2,0,3]),123),{type:'steps',frame:5,runs:[{mask:16,count:2},{mask:0,count:3}]});
 assert.equal(parseTrace(packet(5),123,5).frame,5);
 assert.throws(()=>parseTrace(packet(6,[0,2]),123,5),/lost/);
 assert.throws(()=>parseTrace(packet(0,[],0,999),123),/builds differ/);
 assert.throws(()=>parseTrace(packet(0,[],1),123),/overflowed/);
 assert.throws(()=>parseTrace(packet(0,[],2),123),/left the table/);
 assert.throws(()=>parseTrace(packet(0,[0,0]),123),/Invalid/);
 assert.throws(()=>parseTrace(packet(0)+'f',123),/Invalid/);
 assert.throws(()=>parseTrace('LIVE DATA 0011',123),/Truncated/);
 assert.equal(parseTrace(packet(1,[0,3]),123,0xfffffffe).frame,1,'32-bit frame rollover is checked');
});
function fixture(){
 const calls=[],events=[],timers=[];
 const engine={build:123,send:e=>events.push(['web',e]),setFollowing:on=>events.push(['follow',on]),consoleEvent:e=>events.push(['console',e])};
 const device={capabilities:new Set(['TRACE']),beginFollow:async(bytes,seed,build,revision)=>{calls.push(['begin',seed,build]);device.onReplay({type:'reset',board,seed,revision,session:seed});},endFollow:async()=>calls.push(['end']),pullTrace:async()=>calls.push(['poll']),restart:async seed=>calls.push(['restart',seed]),pause:async paused=>calls.push(['pause',paused]),place:async(x,y)=>calls.push(['place',x,y])};
 const p=new PlaySession({engine,seed:()=>12345,schedule:fn=>{timers.push(fn);return timers.length;},cancel:()=>{},onError:()=>{}});
 return {p,device,calls,events,timers};
}
test('web-only mode keeps both play sessions separate while connected',async()=>{
 const {p,device,calls,events}=fixture();await p.connect(device,board,1,true);
 for(const event of [{type:'keys',mask:16},{type:'pause',paused:true},{type:'restart',seed:9},{type:'place',x:44,y:120},{type:'board',board,revision:2}])await p.send(event);
 assert.deepEqual(calls,[['end']]);assert.equal(events.filter(e=>e[0]==='web').length,5);assert.equal(p.controlsConsole,false);
});
test('console mode replays acknowledged events and does not predict local input',async()=>{
 const {p,device,calls,events,timers}=fixture();await p.connect(device,board,1);
 assert.equal(p.mode,'console');assert.equal(p.controlsConsole,true);
 await p.send({type:'keys',mask:16});await p.send({type:'board',board,revision:2});
 assert.deepEqual(events.filter(e=>e[0]==='web'),[['web',{type:'board',board,revision:2}]],'only layout previews are sent locally');
 await p.send({type:'restart',seed:7});await p.send({type:'pause',paused:true});await p.send({type:'place',x:40,y:100});
 assert.deepEqual(calls.slice(1),[['restart',7],['pause',true],['place',40,100]]);
 device.onReplay({type:'steps',session:12345,frame:2,runs:[{mask:16,count:2}]});
 assert.equal(events.at(-1)[1].frame,2);await timers[0]();assert.equal(calls.at(-1)[0],'poll');
 await p.separate(board,3);await p.send({type:'keys',mask:2});assert.equal(events.at(-1)[0],'web');assert.equal(p.mode,'web');
 const count=events.length;device.onReplay({type:'steps',session:12345,frame:9,runs:[]});assert.equal(events.length,count,'late packets cannot operate independent web play');
});
test('overflow or mismatched firmware freezes following and releases console injection',async()=>{
 const {p,device,calls,events}=fixture();await p.connect(device,board,1);p.failed(new Error('history lost'));
 assert.equal(p.mode,'error');assert.equal(p.controlsConsole,false);assert.deepEqual(events.at(-1),['follow',true]);
 await p.send({type:'restart'});assert.equal(calls.at(-1)[0],'end');
 await p.disconnect(board,2);assert.equal(p.mode,'web');assert.equal(p.device,null);
});
test('older firmware offers independent play without starting an unsupported trace',async()=>{
 const {p,device,calls}=fixture();device.capabilities.clear();await p.connect(device,board,1);
 assert.equal(p.mode,'web');assert.match(p.notice,/Update/);assert.equal(calls.length,0);
});
