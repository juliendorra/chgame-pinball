// Production BrowserDevice + BoardStorage + FAT writer, real console sectors.
// Owns only the absent PBAUTOT.PBT/PBK test files and removes them afterwards.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {BrowserDevice,unhex} from '../editor/serial.mjs';
import {BoardStorage} from '../editor/board-storage.mjs';
import {copy,decode,editableBoard,encode} from '../editor/model.mjs';

const game=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const [python,port,out]=process.argv.slice(2);
if(!python||!port||!out)throw new Error('Usage: node verify_device_storage.mjs PYTHON PORT OUTPUT.json');
const child=spawn(python,[path.join(game,'tools/live_request_bridge.py'),'--port',port],{stdio:['pipe','pipe','inherit']});
const requests=new Map();let sequence=0,writes=0;
createInterface({input:child.stdout}).on('line',line=>{const response=JSON.parse(line),r=requests.get(response.id);if(!r)return;requests.delete(response.id);response.error?r.reject(new Error(response.error)):r.resolve(response.lines);});
child.on('exit',code=>{for(const r of requests.values())r.reject(new Error('USB bridge stopped: '+code));requests.clear();});
const device=new BrowserDevice();device.tail=Promise.resolve();
device.request=command=>new Promise((resolve,reject)=>{if(command.startsWith('W '))writes++;const id=++sequence;requests.set(id,{resolve,reject});child.stdin.write(JSON.stringify({id,command})+'\n');});
const report={result:'failed',checks:[]},owned=new Set();let storage,original,inventory,paused;
const check=label=>{report.checks.push(label);console.log('PASS: '+label);};
const ram=async()=>unhex((await device.request('T')).at(-1).slice(10));
const inventoryKey=items=>JSON.stringify([...items].sort((a,b)=>a.file.localeCompare(b.file)));
const wait=async predicate=>{const deadline=Date.now()+90000;while(!predicate()){if(Date.now()>deadline)throw new Error('Auto-save timed out');await new Promise(resolve=>setTimeout(resolve,50));}};
try{
 const hello=(await device.request('?')).at(-1);device.capabilities=new Set(hello.split(' '));report.hello=hello;
 original=await ram();paused=(await device.request('V')).at(-1).split(' ').map(Number).at(-2);
 inventory=await device.inspectStorage();assert.equal(writes,0);
 await device.withCard(async card=>{assert.equal(await card.saved('PBAUTOT'),null);assert.equal(await card.saved('PBAUTOT','PBK'),null);});
 const board=editableBoard(copy(JSON.parse(fs.readFileSync(path.join(game,'boards/tables.json')))[0]));
 Object.assign(board,{file:'PBAUTOT',id:0x4155544f,title:'AUTOSAVE TEST'});
 storage=new BoardStorage({delay:100});storage.select(board);await storage.connect(device);assert.equal(writes,0);check('Connecting/selecting reads the SD without writing');
 // Ownership is claimed only after verifying that both filenames are absent.
 owned.add('PBAUTOT');storage.changed(board);
 await wait(()=>storage.view(board).kind==='saved');await storage.idle();
 const first=encode(board);assert.deepEqual(await ram(),original);check('Default auto-save verifies SD without switching the active RAM board');
 board.title='AUTOSAVE SECOND';storage.changed(board);await wait(()=>storage.view(board).kind==='saved');await storage.idle();
 await device.withCard(async card=>{assert.deepEqual(await card.saved(board.file),encode(board));assert.deepEqual(await card.saved(board.file,'PBK'),first);});
 check('Second auto-save preserves the original SD revert point');
 const restored=await storage.recover(board);storage.changed(restored);assert.deepEqual(encode(restored),first);check('Revert restores the protected PBT and cancels pending re-save');
 const beforeInvalid=writes;const invalid={...restored,height:1};storage.changed(invalid);await new Promise(resolve=>setTimeout(resolve,180));assert.equal(storage.view(invalid).kind,'invalid');assert.equal(writes,beforeInvalid);storage.changed(restored);check('Invalid drafts remain in the editor without SD writes');
 assert.deepEqual(await ram(),original);report.result='passed';
}finally{
 storage?.disconnect();await storage?.idle();
 try{
  if(owned.size)await device.withCard(async card=>{
   const folder=await card.folder(false);if(folder===null)return;
   for(const stem of owned)for(const ext of ['PBT','PBK']){
    const entry=await card.find(folder,new TextEncoder().encode(stem.padEnd(8)+ext));if(!entry)continue;
    assert.equal(decode(await card.file(entry[2]),stem).id,0x4155544f,'Cleanup only owns its temporary board ID');
    const chain=await card.chain(card.cluster(entry[2])),deleted=entry[2].slice();deleted[0]=229;
    await card.publish(entry.slice(0,2),deleted);for(const cluster of chain)await card.set(cluster,0);
   }
  });
  if(owned.size)await device.request('L');
  if(inventory){const after=await device.inspectStorage();assert.equal(inventoryKey(after.items),inventoryKey(inventory.items));check('Temporary test files removed; every existing board/checkpoint is unchanged');}
  if(original){assert.deepEqual(await ram(),original);const values=(await device.request('V')).at(-1).split(' ').map(Number);assert.equal(values.at(-2),paused);check('Console RAM board and pause state preserved');}
 }catch(error){report.result='failed';report.cleanup_error=error.message;throw error;}
 finally{report.sector_writes=writes;fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');child.stdin.end();}
}
