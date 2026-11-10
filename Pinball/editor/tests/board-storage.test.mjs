import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {BoardStorage,matchesSd} from '../board-storage.mjs';
import {copy,encode,editableBoard} from '../model.mjs';
const templates=JSON.parse(fs.readFileSync(new URL('../../boards/tables.json',import.meta.url)));
const board=i=>editableBoard(copy(templates[i]));
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const tick=()=>new Promise(resolve=>setTimeout(resolve,35));
class Device{
 constructor(boards=[]){this.volume='card-A';this.items=boards.map(b=>({file:b.file,data:Array.from(encode(b)),checkpoint:null}));this.writes=[];}
 async inspectStorage(){return copy({volume:this.volume,items:this.items});}
 async save(file,bytes,options){
  if(options.automatic&&this.playing)throw Object.assign(new Error('Console playing'),{code:'play_active'});
  if(this.gate)await this.gate;
  const current=this.items.find(b=>b.file===file);
  if(options.volume!==this.volume||current&&!equal(current.data,options.expected))throw Object.assign(new Error('External SD change'),{code:'conflict'});
  const result={file,volume:this.volume,data:Array.from(bytes),checkpoint:current?.checkpoint||current?.data||Array.from(bytes)};
  this.items=this.items.filter(b=>b.file!==file).concat(result);this.writes.push(copy(result));return result;
 }
 async revertSd(file,options){const item=this.items.find(b=>b.file===file);return this.save(file,new Uint8Array(item.checkpoint),options);}
 async checkpointSd(file,options){const item=this.items.find(b=>b.file===file);assert.deepEqual(item.data,options.expected);item.checkpoint=copy(item.data);return copy({...item,volume:this.volume});}
}
function setup(boards,options={}){const device=new Device(boards),storage=new BoardStorage({delay:15,...options});for(const b of boards)storage.record(b);return {device,storage};}
test('Connecting and selecting never auto-overwrite a board; legacy conversion is already saved',async()=>{
 const raw=copy(templates[0]),b=editableBoard(raw),{storage,device}=setup([raw]);
 storage.select(b);await storage.connect(device);await tick();assert.equal(device.writes.length,0);assert.equal(storage.view(b).kind,'saved');assert.ok(matchesSd(b,encode(raw)));storage.disconnect();
});
test('Auto-save requires opt-in and preserves the checkpoint and preference on reconnect',async()=>{
 const b=board(8),original=Array.from(encode(b)),{storage,device}=setup([b]);await storage.connect(device);
 assert.equal(storage.auto,false);assert.equal(new BoardStorage({saved:{auto:true}}).auto,false);
 for(let n=0;n<12;n++){b.objects[0].x=26+n;storage.changed(b);}
 await tick();assert.equal(device.writes.length,0);
 storage.setAuto(true);
 await tick();await storage.idle();assert.equal(device.writes.length,1);assert.deepEqual(device.writes[0].data,Array.from(encode(b)));assert.deepEqual(device.writes[0].checkpoint,original);assert.equal(storage.view(b).kind,'saved');
 b.objects[0].x++;storage.changed(b);await storage.save(b);assert.deepEqual(device.writes[1].checkpoint,original);
 const persisted=storage.export();storage.disconnect();const again=new BoardStorage({saved:persisted,delay:15});again.record(b);await again.connect(device);assert.ok(again.auto);assert.ok(again.view(b).revert);assert.equal(again.view(b).kind,'saved');again.disconnect();
});
test('An edit arriving during a write stays pending and is saved next',async()=>{
 const b=board(8),{storage,device}=setup([b]);await storage.connect(device);storage.setAuto(false);
 let release;device.gate=new Promise(resolve=>release=resolve);b.objects[0].x++;storage.changed(b);const first=storage.save(b);await Promise.resolve();await Promise.resolve();
 b.objects[0].x++;storage.changed(b);release();await first;assert.equal(storage.view(b).kind,'pending');
 device.gate=null;await storage.save(b);assert.equal(device.writes.length,2);assert.deepEqual(device.writes.at(-1).data,Array.from(encode(b)));storage.disconnect();
});
test('Switching boards keeps each pending save attached to its own filename',async()=>{
 const a=board(0),b=board(8),{storage,device}=setup([a,b]);await storage.connect(device);
 storage.setAuto(true);
 a.objects[0].x++;storage.changed(a);storage.select(b);b.objects[0].x++;storage.changed(b);await tick();await storage.idle();
 assert.deepEqual(new Set(device.writes.map(w=>w.file)),new Set([a.file,b.file]));assert.equal(storage.pending().length,0);storage.disconnect();
});
test('Manual mode and invalid drafts never write automatically',async()=>{
 const b=board(8),{storage,device}=setup([b]);await storage.connect(device);storage.setAuto(false);b.title='New pirate board';storage.changed(b);await tick();assert.equal(device.writes.length,0);await storage.save(b);assert.equal(device.writes.length,1);
 storage.setAuto(true);b.height=800;storage.changed(b);await tick();assert.equal(storage.view(b).kind,'invalid');assert.equal(device.writes.length,1);assert.ok(storage.pending().length);storage.disconnect();
});
test('External changes, filename collisions and a different card block unattended writes',async()=>{
 const b=board(8),{storage,device}=setup([b]);await storage.connect(device);storage.setAuto(false);b.title='My browser draft';storage.changed(b);
 device.items[0].data=Array.from(encode({...board(8),title:'Someone else edited'}));await assert.rejects(()=>storage.save(b),/External/);assert.equal(storage.view(b).kind,'conflict');assert.equal(device.writes.length,0);
 await storage.check();assert.equal(storage.view(b).kind,'conflict');storage.disconnect();device.volume='card-B';await storage.connect(device);assert.equal(storage.view(b).kind,'conflict');assert.equal(device.writes.length,0);storage.disconnect();
});
test('Revert restores the stable checkpoint, and a new checkpoint is explicit',async()=>{
 const b=board(8),old=copy(b),{storage,device}=setup([b]);await storage.connect(device);storage.setAuto(false);b.title='Edited pirate';storage.changed(b);await storage.save(b);
 const restored=await storage.recover(b);assert.deepEqual(restored,old);storage.changed(restored);assert.equal(storage.view(restored).kind,'saved');
 b.title='Keep this version';storage.changed(b);await storage.save(b);await storage.recover(b,true);b.title='Later changes';storage.changed(b);await storage.save(b);assert.equal((await storage.recover(b)).title,'Keep this version');storage.disconnect();
});
test('Offline drafts persist as pending without claiming SD success',async()=>{
 const b=board(8),storage=new BoardStorage({delay:15});storage.record(b);b.objects[0].x++;storage.changed(b);assert.equal(storage.view(b).kind,'pending');assert.equal(storage.pending().length,1);
 const restored=new BoardStorage({saved:storage.export()});restored.record(b);assert.equal(restored.pending().length,1);assert.match(restored.view(b).label,/not saved to SD/);storage.disconnect();restored.disconnect();
});

test('Undo or an explicit default restore matching SD clears the conflict without a write',async()=>{
 const original=board(8),draft={...copy(original),title:'Another local draft'},{storage,device}=setup([original]);storage.record(draft);await storage.connect(device);assert.equal(storage.view(draft).kind,'conflict');
 storage.changed(original);assert.equal(storage.view(original).kind,'saved');await tick();assert.equal(device.writes.length,0);storage.disconnect();
});

test('Auto-save stays queued during console play and writes the latest draft after pause',async()=>{
 const b=board(8),{storage,device}=setup([b]);device.playing=true;await storage.connect(device);
 storage.setAuto(true);
 b.objects[0].x++;storage.changed(b);await tick();await storage.idle();
 assert.equal(device.writes.length,0);assert.equal(storage.pending().length,1);
 assert.equal(storage.view(b).kind,'pending');assert.match(storage.view(b).label,/pause console/);assert.equal(storage.record(b).error,null);
 b.objects[0].x++;storage.changed(b);await tick();assert.equal(device.writes.length,0);
 device.playing=false;await tick();await storage.idle();
 assert.equal(device.writes.length,1);assert.deepEqual(device.writes[0].data,Array.from(encode(b)));assert.equal(storage.view(b).kind,'saved');storage.disconnect();
});

test('Manual save remains available during play, and deferred drafts survive disconnect',async()=>{
 const b=board(8),{storage,device}=setup([b]);device.playing=true;await storage.connect(device);
 storage.setAuto(true);
 b.objects[0].x++;storage.changed(b);await tick();await storage.save(b);assert.equal(device.writes.length,1);
 b.objects[0].x++;storage.changed(b);await tick();const persisted=storage.export();storage.disconnect();
 const restored=new BoardStorage({saved:persisted});restored.record(b);assert.equal(restored.pending().length,1);assert.match(restored.view(b).label,/not saved to SD/);restored.disconnect();
});
