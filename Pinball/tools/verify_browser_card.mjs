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
 // Repeated guarded saves publish PBT files without making revert copies.
 const original=encode(boards[0]),first=encode({...boards[0],title:'Safe edit one'}),second=encode({...boards[0],title:'Safe edit two'});
 card=await BoardCard.open(device);const volume=card.volume;
 await card.saveChecked('SAFE',original,{volume,expected:null});
 await card.saveChecked('SAFE',first,{volume,expected:Array.from(original)});
 await card.saveChecked('SAFE',second,{volume,expected:Array.from(first)});
 card=await BoardCard.open(device);assert.deepEqual(await card.saved('SAFE'),second);
 const item=(await card.inventory()).items.find(i=>i.file==='SAFE');assert.deepEqual(item.data,Array.from(second));assert.equal('checkpoint' in item,false);
 const untouched=fs.readFileSync(process.argv[2]);
 await assert.rejects(()=>card.saveChecked('SAFE',first,{volume:'another-card',expected:Array.from(second)}),/card changed/);
 await assert.rejects(()=>card.saveChecked('SAFE',first,{volume,expected:Array.from(original)}),/changed on SD/);
 await assert.rejects(()=>card.saveChecked('SAFE',encode(boards[8]),{volume,expected:Array.from(second)}),/another board/);
 assert.deepEqual(fs.readFileSync(process.argv[2]),untouched,'conflicts never modify the SD card');
 await card.save('FAILSAFE',original);let free=2;while(await card.get(free)!==0)free++;fail=card.sector(free);
 await assert.rejects(()=>card.saveChecked('FAILSAFE',first,{volume,expected:Array.from(original)}));fail=null;card=await BoardCard.open(device);
 assert.deepEqual(await card.saved('FAILSAFE'),original,'failed data write leaves the original intact');
 const folder=await card.folder(),slot=await card.find(folder,new TextEncoder().encode('SAFE    PBT'));fail=slot[0];
 await assert.rejects(()=>card.saveChecked('SAFE',first,{volume,expected:Array.from(second)}));fail=null;card=await BoardCard.open(device);
 assert.deepEqual(await card.saved('SAFE'),second,'failed publication leaves the previous board intact');
 const backups=[];
 for await(const sector of card.directory(folder)){
  const b=await card.read(sector);
  for(let at=0;at<512;at+=32){if(!b[at])break;if(b[at]!==229&&new TextDecoder().decode(b.subarray(at+8,at+11))==='PBK')backups.push(new TextDecoder().decode(b.subarray(at,at+8)).trim());}
 }
 assert.deepEqual(backups,process.argv.includes('--new-folder')?[]:['SAFE'],'no new backup files are created');
}finally{fs.closeSync(fd);}
