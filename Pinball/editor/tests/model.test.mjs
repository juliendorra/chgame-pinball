import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {encode,decode,validate,controlsForKey,newIdentity,pick} from '../model.mjs';
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
