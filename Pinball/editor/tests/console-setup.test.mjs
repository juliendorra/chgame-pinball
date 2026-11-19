import test from 'node:test';
import assert from 'node:assert/strict';
import {latestPinballRelease,checkConsoleUpdate,pinballCart,prepareConsole,prepareInstall,writeInstall} from '../console-setup.mjs';
import {SerialCard,ascii,crc32,view,flashApplication} from '../vendor/organizer/serial.mjs';
import {encodeIndex,scanMenu} from '../vendor/organizer/menu.mjs';

function cart(version='1.4.20',fill=42){
 const image=new Uint8Array(32).fill(fill),record=ascii(JSON.stringify({chgRecord:1,game:{id:'midnight-pinball'}}));
 const bytes=new Uint8Array(544+record.length),fields=view(bytes);
 bytes.set(ascii('CHG1'));fields.setUint16(4,1,true);fields.setUint16(6,512,true);
 fields.setUint32(8,0x35335843,true);fields.setUint32(12,0x003000f7,true);
 fields.setUint32(16,32,true);fields.setUint32(20,crc32(image),true);
 bytes.set(ascii('MIDNIGHT PINBALL'),32);bytes.set(ascii(version),80);
 fields.setUint32(108,544,true);fields.setUint32(112,record.length,true);fields.setUint32(116,crc32(record),true);
 bytes.set(image,512);bytes.set(record,544);fields.setUint32(508,crc32(bytes.subarray(0,508)),true);
 return bytes;
}
class Card{
 constructor(files={}){
  this.files=new Map(Object.entries(files));this.dirs=new Set(['','GAMES','GAMES/ARCADE','PINBALL']);
  this.writes=[];this.link={close:async()=>{this.closed=true;},disconnected:false};
 }
 async list(folder){
  const prefix=folder?folder+'/':'';
  const dirs=[...this.dirs].filter(name=>name!==folder&&name.startsWith(prefix)&&!name.slice(prefix.length).includes('/'))
   .map(name=>({name:name.slice(prefix.length),directory:true,size:0}));
  return dirs.concat([...this.files].filter(([name])=>name.startsWith(prefix)&&!name.slice(prefix.length).includes('/'))
   .map(([name,data])=>({name:name.slice(prefix.length),directory:false,size:data.length})));
 }
 async read(path,offset,length){const data=this.files.get(path);if(!data||offset+length>data.length)throw new Error('Missing SD data');return data.slice(offset,offset+length);}
 async check(path){return crc32(this.files.get(path));}
 async replace(path,bytes){this.writes.push(path);this.files.set(path,bytes.slice());}
 async mkdir(path){this.dirs.add(path);}
 async start(){}
 async sync(){this.synced=true;}
 async menu(){this.menuExited=true;}
}
const latestCart=cart();
const pkg={cart:pinballCart(latestCart),cartBytes:latestCart,files:[
 {path:'GAMES/PINBALL.CHG',data:latestCart},
 {path:'PINBALL/STORM.PBT',data:ascii('shipped default')},
 {path:'PINBALL/THEMES.PBA',data:ascii('new theme')},
]};
const release={version:'1.4.20',url:new URL('https://github.com/juliendorra/chgame-pinball/releases/download/v1.4.20/Pinball.chgame')};

test('release lookup only accepts this repository and one uploaded cart',async()=>{
 const fetcher=async()=>({ok:true,json:async()=>({tag_name:'v1.4.20',assets:[{state:'uploaded',name:'Pinball.chgame',browser_download_url:release.url.href}]})});
 assert.equal((await latestPinballRelease(fetcher)).version,'1.4.20');
 await assert.rejects(()=>latestPinballRelease(async()=>({ok:true,json:async()=>({tag_name:'v1',assets:[]})})),/one .chgame/);
 await assert.rejects(()=>latestPinballRelease(async()=>({ok:true,json:async()=>({tag_name:'v1',assets:[
  {state:'uploaded',name:'Pinball.chgame',browser_download_url:'https://github.com/other/game/releases/download/v1/game.chgame'},
 ]})})),/unexpected/);
});
test('running-game update preflight distinguishes a matching release from a newer editor',async()=>{
 const calls=[],fetcher=async(url,options)=>{
  calls.push(url);assert.equal(options.credentials,'omit');
  return {ok:true,text:async()=> '#pragma once\n#define PINBALL_GAME_HASH 123u\n'};
 };
 const latest=async()=>release;
 assert.equal((await checkConsoleUpdate(123,{fetcher,latest})).compatible,true);
 assert.equal((await checkConsoleUpdate(124,{fetcher,latest})).compatible,false);
 assert.equal(calls[0],'https://raw.githubusercontent.com/juliendorra/chgame-pinball/v1.4.20/Pinball/SyncBuild.h');
 await assert.rejects(()=>checkConsoleUpdate(123,{latest,fetcher:async()=>({ok:false})}),/has not been interrupted/);
 for(const text of ['', '#define PINBALL_GAME_HASH 4294967296u']){
  await assert.rejects(()=>checkConsoleUpdate(123,{latest,fetcher:async()=>({ok:true,text:async()=>text})}),/no valid replay/);
 }
});
test('launch verifies the actual executable and metadata checksums',()=>{
 assert.equal(pinballCart(latestCart).image.length,32);
 const corrupt=latestCart.slice();corrupt[520]^=1;
 assert.throws(()=>pinballCart(corrupt),/executable failed/);
 const bad=latestCart.slice();bad[545]^=1;
 assert.throws(()=>pinballCart(bad),/metadata failed/);
});
test('SD update preserves edited boards, recovery copies, scores, categories and menu bytes',async()=>{
 const index=encodeIndex([{name:'OTHER.CHG'},{name:'MIDNIGHT.CHG'}]);
 const files={
  'GAMES/ARCADE/MENU.IDX':index,'GAMES/ARCADE/MIDNIGHT.CHG':cart('1.4.19',17),
  'PINBALL/STORM.PBT':ascii('user edits'),'PINBALL/STORM.PBK':ascii('revert copy'),
  'SAVES/SCORE.SAV':ascii('scores'),'PINBALL/THEMES.PBA':ascii('old theme'),
 };
 const card=new Card(files),menu=await scanMenu(card);
 const existing=menu.folders.flatMap(folder=>folder.entries).find(entry=>entry.name==='MIDNIGHT.CHG');
 const plan=await prepareInstall(card,menu,pkg,existing);
 assert.deepEqual(plan.preserved,['PINBALL/STORM.PBT']);
 await writeInstall(card,plan);
 assert.deepEqual(card.writes,['PINBALL/THEMES.PBA','GAMES/ARCADE/MIDNIGHT.CHG']);
 for(const path of ['PINBALL/STORM.PBT','PINBALL/STORM.PBK','SAVES/SCORE.SAV','GAMES/ARCADE/MENU.IDX']){
  assert.deepEqual(card.files.get(path),files[path],path);
 }
});
test('new installs append to the chosen category and publish its menu last',async()=>{
 const card=new Card({'GAMES/ARCADE/MENU.IDX':encodeIndex([]),'GAMES/ARCADE/PINBALL.CHG':cart('1.4.19')});
 const menu=await scanMenu(card),plan=await prepareInstall(card,menu,pkg,null,'GAMES/ARCADE');
 assert.equal(plan.path,'GAMES/ARCADE/PINBALL2.CHG');
 await writeInstall(card,plan);
 assert.equal(card.writes.at(-1),'GAMES/ARCADE/MENU.IDX');
 assert.deepEqual(card.files.get(plan.path),latestCart);
});
test('changed SD cart or menu aborts before any replacement',async()=>{
 const card=new Card({'GAMES/ARCADE/MIDNIGHT.CHG':cart('1.4.19')});
 const menu=await scanMenu(card),entry=menu.folders.flatMap(folder=>folder.entries).find(entry=>entry.name==='MIDNIGHT.CHG');
 const update=await prepareInstall(card,menu,pkg,entry);
 card.files.set(entry.path,cart('1.4.18'));
 await assert.rejects(()=>writeInstall(card,update),/cart changed/);
 const install=await prepareInstall(card,menu,pkg,null,'GAMES/ARCADE');
 card.files.set('GAMES/ARCADE/MENU.IDX',encodeIndex([{name:'OTHER.CHG'}]));
 await assert.rejects(()=>writeInstall(card,install),/menu changed/);
 assert.deepEqual(card.writes,[]);
});
async function setup(card,choice){
 const identify=SerialCard.identify;
 SerialCard.identify=async()=>card;
 let flashed,offers=0;
 try{
  await prepareConsole({},'port',{
   open:async()=>card.link,latest:async()=>release,download:async()=>pkg,
   choose:async offer=>{offers++;return {action:choice,destination:'GAMES/ARCADE'};},
   flash:async(_serial,_link,image)=>{flashed=image.slice();return 'next port';},
  });
  return {flashed,offers};
 }finally{SerialCard.identify=identify;}
}
test('latest SD cart launches automatically with no SD writes or update offer',async()=>{
 const card=new Card({'GAMES/ARCADE/PINBALL.CHG':latestCart,'PINBALL/THEMES.PBA':ascii('new theme')});
 const result=await setup(card);
 assert.equal(result.offers,0);assert.deepEqual(result.flashed,pkg.cart.image);
 assert.deepEqual(card.writes,[]);
});
test('outdated SD cart offers update then launches the verified release',async()=>{
 const card=new Card({'GAMES/ARCADE/PINBALL.CHG':cart('1.4.19')});
 const result=await setup(card,'install');
 assert.equal(result.offers,1);assert.deepEqual(result.flashed,pkg.cart.image);
 assert.ok(card.writes.includes('GAMES/ARCADE/PINBALL.CHG'));
});
test('updating a running game opens the helper then installs and launches from SD',async()=>{
 const card=new Card({'GAMES/ARCADE/PINBALL.CHG':cart('1.4.19')}),identify=SerialCard.identify;
 const running={port:'running port',close:async()=>{}},calls=[];
 SerialCard.identify=async link=>{assert.equal(link,running);return null;};
 try{
  const next=await prepareConsole({},running.port,{
   latest:async()=>release,download:async()=>pkg,open:async port=>{assert.equal(port,running.port);return running;},
   helper:async()=>Uint8Array.of(42),
   startHelper:async(_serial,link,image)=>{assert.equal(link,running);assert.equal(image[0],42);calls.push('helper');return card;},
   choose:async()=>({action:'install'}),
   flash:async(_serial,link,image)=>{assert.equal(link,card.link);assert.deepEqual(image,pkg.cart.image);calls.push('launch');return 'updated port';},
  });
  assert.equal(next,'updated port');assert.deepEqual(calls,['helper','launch']);
  assert.deepEqual(card.files.get('GAMES/ARCADE/PINBALL.CHG'),latestCart);
 }finally{SerialCard.identify=identify;}
});
test('declining an update can launch the old SD version without writing it',async()=>{
 const old=cart('1.4.19',17),card=new Card({'GAMES/ARCADE/PINBALL.CHG':old});
 const result=await setup(card,'launch');
 assert.deepEqual(result.flashed,pinballCart(old).image);assert.deepEqual(card.writes,[]);
});
test('missing game offers installation and cancellation exits the helper without SD changes',async()=>{
 const card=new Card();
 await assert.rejects(()=>setup(card,'cancel'),{name:'AbortError'});
 assert.equal(card.menuExited,true);assert.deepEqual(card.writes,[]);
 const fresh=new Card();const result=await setup(fresh,'install');
 assert.equal(result.offers,1);assert.deepEqual(result.flashed,pkg.cart.image);
 assert.ok(fresh.writes.includes('GAMES/ARCADE/PINBALL.CHG'));
});
test('the shared uploader supports a full-size game through END and RUN',async()=>{
 const port={getInfo:()=>({usbVendorId:0x16c0,usbProductId:0x27dd})};
 const serial={getPorts:async()=>[port]},commands=[];
 const hello=new Uint8Array(34),fields=view(hello);
 hello[1]=hello[2]=1;fields.setUint16(4,3,true);
 fields.setUint32(6,0x3000,true);fields.setUint32(10,50944,true);
 fields.setUint16(14,256,true);fields.setUint16(16,512,true);hello.set(ascii('CX35'),30);
 const link={port,close:async()=>{},request:async(protocol,command,payload)=>{
  assert.equal(protocol,'CG');commands.push({command,payload});
  return command===1?hello:Uint8Array.of(0);
 }};
 const image=new Uint8Array(50944).fill(42);
 assert.equal(await flashApplication(serial,link,image,()=>{}),port);
 assert.equal(commands[1].command,2);assert.equal(view(commands[1].payload).getUint32(0,true),50944);
 assert.equal(view(commands[1].payload).getUint32(4,true),crc32(image));
 const pages=commands.filter(item=>item.command===3);
 assert.equal(pages.length,199);
 pages.forEach(({payload},index)=>assert.equal(view(payload).getUint32(0,true),index*256));
 assert.deepEqual(commands.slice(-2).map(item=>item.command),[4,5]);
 await assert.rejects(()=>flashApplication(serial,link,new Uint8Array(50948),()=>{}),/Invalid Rev0/);
});
