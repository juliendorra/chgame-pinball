// Async counterpart of fat.py, restricted to PINBALL/*.PBT. No mass-storage
// emulation: sectors are exchanged with the running game's bounded protocol.
import {decode} from './model.mjs';
const u16=(b,o)=>new DataView(b.buffer,b.byteOffset,b.byteLength).getUint16(o,true);
const u32=(b,o)=>new DataView(b.buffer,b.byteOffset,b.byteLength).getUint32(o,true);
const put16=(b,o,n)=>new DataView(b.buffer,b.byteOffset,b.byteLength).setUint16(o,n,true);
const put32=(b,o,n)=>new DataView(b.buffer,b.byteOffset,b.byteLength).setUint32(o,n,true);
const ascii=s=>new TextEncoder().encode(s),equal=(a,b)=>a.length===b.length&&a.every((v,i)=>v===b[i]);
export class BoardCard {
 static async open(device){const card=new BoardCard(device);await card.init();return card;}
 constructor(device){this.device=device;this.cache=new Map();}
 async read(lba){if(!this.cache.has(lba)){const b=await this.device.read(lba);if(b.length!==512)throw new Error('Short SD sector');this.cache.set(lba,b.slice());}return this.cache.get(lba);}
 async write(lba,data){if(!Number.isInteger(lba)||lba<this.base||lba>=this.base+this.total||data.length!==512)throw new Error('Write outside FAT volume');await this.device.write(lba,data);this.cache.set(lba,data.slice());}
 async init(){
  let b=await this.read(0);this.base=0;
  if(u16(b,11)!==512||!b[13]||(b[13]&(b[13]-1))){
   const part=[0,1,2,3].find(i=>[4,6,11,12,14].includes(b[450+i*16]));if(part===undefined)throw new Error('A FAT16 or FAT32 SD card is required');
   this.base=u32(b,446+part*16+8);b=await this.read(this.base);
  }
  if(b[510]!==85||b[511]!==170||u16(b,11)!==512)throw new Error('Invalid FAT boot sector');
  this.spc=b[13];this.reserved=u16(b,14);this.copies=b[16];this.rootCount=u16(b,17);this.total=u16(b,19)||u32(b,32);this.fatSize=u16(b,22)||u32(b,36);
  if(!this.spc||(this.spc&(this.spc-1))||this.spc>128||this.copies<1||this.copies>2||!this.fatSize||!this.reserved)throw new Error('Unsupported FAT geometry');
  this.fatBase=this.base+this.reserved;this.rootBase=this.fatBase+this.copies*this.fatSize;this.rootSectors=Math.ceil(this.rootCount*32/512);this.dataBase=this.rootBase+this.rootSectors;
  this.clusterCount=Math.floor((this.total-(this.dataBase-this.base))/this.spc);this.bits=this.clusterCount>=4085&&this.clusterCount<65525?16:this.clusterCount>=65525?32:0;
  if(!this.bits||(this.clusterCount+2)*this.bits/8>this.fatSize*512)throw new Error('Unsupported FAT type or size');
  if(this.bits===32&&(u16(b,40)&128))throw new Error('FAT32 without FAT mirroring is unsupported');
  this.root=this.bits===16?0:u32(b,44);
  if(this.bits===16&&!this.rootCount||this.bits===32&&(this.rootCount||this.root<2||this.root>=this.clusterCount+2))throw new Error('Invalid FAT root directory');
  this.fsinfo=this.bits===32&&u16(b,48)<this.reserved?this.base+u16(b,48):null;
  this.backup=this.bits===32&&u16(b,50)+u16(b,48)<this.reserved?this.base+u16(b,50)+u16(b,48):null;
  this.end=this.bits===16?0xffff:0x0fffffff;this.nextFree=2;
 }
 checkCluster(n){if(!Number.isInteger(n)||n<2||n>=this.clusterCount+2)throw new Error('Invalid FAT cluster');}
 async get(n){this.checkCluster(n);const offset=n*(this.bits/8),b=await this.read(this.fatBase+Math.floor(offset/512));return this.bits===16?u16(b,offset%512):u32(b,offset%512)&0x0fffffff;}
 async set(n,value){this.checkCluster(n);const offset=n*(this.bits/8);for(let copy=0;copy<this.copies;copy++){const lba=this.fatBase+copy*this.fatSize+Math.floor(offset/512),b=(await this.read(lba)).slice();if(this.bits===16)put16(b,offset%512,value);else put32(b,offset%512,(u32(b,offset%512)&0xf0000000)|value);await this.write(lba,b);}}
 async chain(start){const result=[],seen=new Set();let n=start;while(n){this.checkCluster(n);if(seen.has(n))throw new Error('Broken FAT chain');seen.add(n);result.push(n);n=await this.get(n);if(n>=this.end-7)return result;}throw new Error('Truncated FAT chain');}
 sector(n){this.checkCluster(n);return this.dataBase+(n-2)*this.spc;}
 async allocate(count){
  const chosen=[];for(let n=this.nextFree;n<this.clusterCount+2;n++){if(await this.get(n)===0)chosen.push(n);if(chosen.length===count)break;}
  if(chosen.length!==count)throw new Error('The SD card is full');this.nextFree=chosen.at(-1)+1;
  for(const [i,n] of chosen.entries())await this.set(n,chosen[i+1]??this.end);return chosen;
 }
 async *directory(cluster){if(cluster===0){for(let n=0;n<this.rootSectors;n++)yield this.rootBase+n;}else for(const c of await this.chain(cluster))for(let n=0;n<this.spc;n++)yield this.sector(c)+n;}
 async find(cluster,name){for await(const sector of this.directory(cluster)){const b=await this.read(sector);for(let at=0;at<512;at+=32){if(b[at]===0)return null;if(b[at]!==229&&b[at+11]!==15&&equal(b.subarray(at,at+11),name))return [sector,at,b.slice(at,at+32)];}}return null;}
 async slot(cluster){
  for await(const sector of this.directory(cluster)){const b=await this.read(sector);for(let at=0;at<512;at+=32)if(b[at]===0||b[at]===229)return [sector,at];}
  if(cluster===0)throw new Error('The FAT16 root directory is full');const extra=(await this.allocate(1))[0];
  for(let n=0;n<this.spc;n++)await this.write(this.sector(extra)+n,new Uint8Array(512));await this.set((await this.chain(cluster)).at(-1),extra);return [this.sector(extra),0];
 }
 entry(name,cluster,size,folder=false){const e=new Uint8Array(32);e.set(name);e[11]=folder?16:32;put16(e,26,cluster&65535);if(this.bits===32)put16(e,20,cluster>>>16);put32(e,28,size);return e;}
 async publish([sector,at],entry){const b=(await this.read(sector)).slice();b.set(entry,at);await this.write(sector,b);}
 cluster(e){return u16(e,26)|(this.bits===32?u16(e,20)<<16:0);}
 async folder(){
  const found=await this.find(this.root,ascii('PINBALL    '));if(found){if(!(found[2][11]&16))throw new Error('PINBALL exists but is not a folder');return this.cluster(found[2]);}
  const slot=await this.slot(this.root),cluster=(await this.allocate(1))[0],first=this.sector(cluster);
  for(let n=0;n<this.spc;n++)await this.write(first+n,new Uint8Array(512));const b=new Uint8Array(512);b.set(this.entry(ascii('.          '),cluster,0,true));b.set(this.entry(ascii('..         '),this.root,0,true),32);await this.write(first,b);
  await this.publish(slot,this.entry(ascii('PINBALL    '),cluster,0,true));return cluster;
 }
 async file(e){const size=u32(e,28);if(size>960||!size)throw new Error('Existing PBT file has an invalid size');const out=new Uint8Array(size);let at=0;
  for(const c of await this.chain(this.cluster(e)))for(let n=0;n<this.spc;n++){const b=await this.read(this.sector(c)+n),count=Math.min(512,size-at);out.set(b.subarray(0,count),at);at+=count;if(at>=size)return out;}throw new Error('Incomplete file');
 }
 async save(stem,data){
  if(!/^[A-Z0-9_]{1,8}$/.test(stem))throw new Error('Use a 1–8 character uppercase SD filename');decode(data,stem);
  const folder=await this.folder(),name=ascii(stem.padEnd(8)+'PBT'),old=await this.find(folder,name);
  if(old){if(old[2][11]&16)throw new Error('Destination is a folder');decode(await this.file(old[2]),stem);}
  const slot=old?old.slice(0,2):await this.slot(folder),clusters=await this.allocate(Math.ceil(data.length/(512*this.spc)));let attempted=false;
  try{
   for(let i=0;i<Math.ceil(data.length/512);i++){const sector=this.sector(clusters[Math.floor(i/this.spc)])+i%this.spc,b=new Uint8Array(512);b.set(data.subarray(i*512,(i+1)*512));await this.write(sector,b);}
   const entry=this.entry(name,clusters[0],data.length);
   for(const c of clusters)for(let n=0;n<this.spc;n++)this.cache.delete(this.sector(c)+n);
   if(!equal(await this.file(entry),data))throw new Error('SD board readback differs');attempted=true;await this.publish(slot,entry);
  }catch(e){if(!attempted)for(const n of clusters)await this.set(n,0);throw e;}
  if(old)for(const n of await this.chain(this.cluster(old[2])))await this.set(n,0);
  for(const sector of new Set([this.fsinfo,this.backup].filter(n=>n!==null))){const b=(await this.read(sector)).slice();if(equal(b.subarray(0,4),ascii('RRaA'))&&equal(b.subarray(484,488),ascii('rrAa'))){b.fill(255,488,496);await this.write(sector,b);}}
  this.cache.clear();return {path:`PINBALL/${stem}.PBT`,bytes:data.length,verified:true};
 }
}
