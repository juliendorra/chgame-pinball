import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {emblemPixels,paintEmblem} from '../board-picker.mjs';
const art=Object.values(JSON.parse(fs.readFileSync(new URL('../../sprites/board_borders.json',import.meta.url))));
const boards=JSON.parse(fs.readFileSync(new URL('../../boards/tables.json',import.meta.url)));
const inks={'0':2,w:1,m:3,t:4,d:7,i:5,c:8,o:9,g:10,b:12,p:13,s:14,r:6},accent=[4,4,14,10,10,13,8,11,10];
test('All nine board choices use their own canonical crest and accent',()=>{
 const signatures=new Set();
 for(const b of boards){
  const pixels=emblemPixels(b,art);assert.equal(pixels.length,8);assert.equal(pixels[0].length,12);
  art[b.theme].emblem.forEach((row,y)=>[...row].forEach((ink,x)=>assert.equal(pixels[y][x],ink==='.'?0:ink==='c'?accent[b.theme]:inks[ink])));
  signatures.add(JSON.stringify(pixels));
 }
 assert.equal(signatures.size,9);
 const clone={...boards[8],title:'Another pirate board',id:123};assert.deepEqual(emblemPixels(clone,art),emblemPixels(boards[8],art));
});
test('Menu crest uses the board felt, derived shadow and exact integer pixels',()=>{
 const board={...boards[0],palette:[...boards[0].palette]};board.palette[0]='ACE';board.palette[2]='F00';
 const calls=[],ctx={set fillStyle(value){this.ink=value;},fillRect(...rect){calls.push([this.ink,...rect]);}};
 const canvas={getContext:()=>ctx};paintEmblem(canvas,board,art);
 assert.equal(canvas.width,48);assert.equal(canvas.height,32);assert.equal(calls.length,96);
 for(const call of calls){assert.equal(call[3],4);assert.equal(call[4],4);assert.equal(call[1]%4,0);assert.equal(call[2]%4,0);}
 assert.ok(calls.some(c=>c[0]==='#ACE'));assert.ok(calls.some(c=>c[0]==='#567'));assert.ok(!calls.some(c=>c[0]==='#F00'));
 assert.equal(board.palette[2],'F00');
});
