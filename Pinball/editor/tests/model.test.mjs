import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {encode,decode,validate,controlsForKey,newIdentity,pick,editableBoard,createPart,rubberPoint} from '../model.mjs';
const boards=JSON.parse(fs.readFileSync(new URL('../../boards/tables.json',import.meta.url)));
for(const board of boards)test(`${board.title}: byte-identical PBT codec`,()=>{
 const bytes=encode(board),reference=fs.readFileSync(new URL('../../sd/PINBALL/'+board.file+'.PBT',import.meta.url));assert.deepEqual(Buffer.from(bytes),reference);assert.deepEqual(encode(decode(bytes,board.file)),bytes);
 const bad=bytes.slice();bad[97]^=1;assert.throws(()=>decode(bad,board.file),/checksum/);
});
test('Keyboard controls separate flippers, contextual launch and directional shake',()=>{
 for(const [code,key,expected] of [['ShiftLeft','Shift',16],['KeyA','a',1],['ArrowLeft','ArrowLeft',16],['ShiftRight','Shift',2],['KeyD','d',2],['ArrowRight','ArrowRight',32],['Space',' ',8],['Enter','Enter',8],['NumpadEnter','Enter',8],['Tab','Tab',0],['KeyB','b',2],['ArrowDown','ArrowDown',8]])assert.equal(controlsForKey({code,key}),expected);
 assert.equal(controlsForKey({code:'KeyA',key:'a',metaKey:true}),0);
});
test('Clones keep their art and geometry, but have unique IDs/files/scores',()=>{const original=boards[8],clone=newIdentity(original,boards);assert.notEqual(clone.id,original.id);assert.notEqual(clone.file,original.file);assert.deepEqual(clone.objects,original.objects);clone.objects[0].x++;assert.notDeepEqual(clone.objects,original.objects);});
test('Blank and incomplete boards remain playable, with mission warnings',()=>{const b=structuredClone(boards[0]);b.objects=[];assert.deepEqual(validate(b).errors,[]);assert.equal(validate(b).warnings.length,3);assert.equal(encode(b).length,96);});
test('Picking follows long rails and curved ramps, not only their anchor',()=>{const b=structuredClone(boards[0]);b.objects=[{kind:'wall',x:20,y:70,u:90,v:170}];assert.equal(pick(b,55,120),0);assert.equal(pick(b,100,80),-1);});
test('Unsafe board sizes, geometry and non-ASCII labels are refused',()=>{for(const patch of [{height:900},{gravity:0},{file:'../X'},{title:'⚓'}])assert.ok(validate({...boards[0],...patch}).errors.length);});

test('Legacy slings become two independent, movable parts exactly once',()=>{
 const original=copyBoard(),b=editableBoard(original),rubbers=b.objects.filter(o=>o.kind==='rubber');
 assert.equal(original.flags,undefined);assert.equal(b.flags,1);assert.equal(rubbers.length,2);
 assert.deepEqual(rubbers.map(o=>[o.x,o.y,o.u,o.v,o.group]),[[30,b.height-75,15,27,0],[88,b.height-75,15,27,1]]);
 assert.deepEqual(editableBoard(b),b);
 for(const o of rubbers){assert.equal(pick(b,o.x,o.y+12),b.objects.indexOf(o));assert.equal(pick(b,(o.x+rubberPoint(o,256).x)/2,o.y+17),b.objects.indexOf(o));}
 assert.deepEqual(encode(decode(encode(b),b.file)),encode(b));
 b.objects=b.objects.filter(o=>o.kind!=='rubber');assert.equal(editableBoard(decode(encode(b),b.file)).objects.filter(o=>o.kind==='rubber').length,0,'removing both does not resurrect the cabinet pair');
});
const copyBoard=()=>structuredClone(boards[0]);
test('Rubber placement, size, mirroring and pick footprint follow actual hardware',()=>{
 const b=editableBoard(copyBoard());b.objects=[createPart('rubber',{x:40,y:180},b.height)];const o=b.objects[0];
 assert.deepEqual(validate(b).errors,[]);assert.equal(pick(b,48,197),0);assert.equal(pick(b,80,197),-1);
 for(let t=0;t<=256;t++){
  const left=rubberPoint(o,t),right=rubberPoint({...o,group:1,x:88},t);assert.equal(left.x+right.x,128);assert.equal(left.y,right.y);
 }
 for(const patch of [{u:7},{v:41},{group:2},{x:100},{y:b.height-30}])assert.ok(validate({...b,objects:[{...o,...patch}]}).errors.length);
 assert.ok(validate({...b,flags:0}).errors.length,'new elements require explicit-rubbers flag');
 assert.deepEqual(validate({...b,objects:[{...o,u:24,v:40}]}).errors,[]);
});

test('Full legacy drafts keep every part while exposing the 72-element save limit',()=>{
 const b=copyBoard();while(b.objects.length<72)b.objects.push(createPart('bumper',{x:64,y:100},b.height));
 const converted=editableBoard(b);assert.equal(converted.objects.length,74);assert.ok(validate(converted).errors.length);assert.equal(b.objects.length,72);
 converted.objects.splice(0,2);assert.equal(converted.objects.filter(o=>o.kind==='rubber').length,2);assert.deepEqual(validate(converted).errors,[]);
});

test('Legacy conversion never clears unknown format flags',()=>{const b={...copyBoard(),flags:2};assert.equal(editableBoard(b).flags,2);assert.ok(validate(editableBoard(b)).errors.length);});
