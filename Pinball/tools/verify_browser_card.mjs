import fs from 'node:fs';
import assert from 'node:assert/strict';
import {BoardCard} from '../editor/card.mjs';
import {encode,copy} from '../editor/model.mjs';
const boards=JSON.parse(fs.readFileSync(new URL('../boards/tables.json',import.meta.url)));
const fd=fs.openSync(process.argv[2],'r+');let fail=null;
const device={read:async lba=>{const b=new Uint8Array(512);assert.equal(fs.readSync(fd,b,0,512,lba*512),512);return b;},write:async(lba,data)=>{if(lba===fail)throw new Error('Injected write failure');assert.equal(fs.writeSync(fd,data,0,512,lba*512),512);}};
try{
 let card=await BoardCard.open(device);
 const before=fs.readFileSync(process.argv[2]);await assert.rejects(()=>card.save('../FAIL',encode(boards[0])));
 const bad=encode(boards[0]);bad[100]^=1;await assert.rejects(()=>card.save('BAD',bad));assert.deepEqual(fs.readFileSync(process.argv[2]),before,'validation precedes any SD mutation');
 if(process.argv.includes('--new-folder')){await card.save('NEWBOARD',encode(boards[2]));}
 else{
  // Copy-on-write data or directory failure must keep the previous board readable.
  const folder=await card.folder(),old=await card.find(folder,new TextEncoder().encode('ORIGINALPBT'));
  let free=2;while(await card.get(free)!==0)free++;fail=card.sector(free);
  await assert.rejects(()=>card.save('ORIGINAL',encode(boards[8])));fail=null;card=await BoardCard.open(device);
  assert.deepEqual(await card.file((await card.find(folder,new TextEncoder().encode('ORIGINALPBT')))[2]),encode(boards[0]));
  fail=old[0];await assert.rejects(()=>card.save('ORIGINAL',encode(boards[8])));fail=null;card=await BoardCard.open(device);
  assert.deepEqual(await card.file((await card.find(folder,new TextEncoder().encode('ORIGINALPBT')))[2]),encode(boards[0]));
  const big=copy(boards[0]);big.objects=Array.from({length:72},(_,i)=>copy(big.objects[i%big.objects.length]));
  await card.save('ORIGINAL',encode(big));await card.save('ORIGINAL',encode(boards[8]));
  for(let i=0;i<20;i++)await card.save('CLONE'+String(i).padStart(2,'0'),encode(boards[i%9]));
 }
}finally{fs.closeSync(fd);}
