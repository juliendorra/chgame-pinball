import {Link,SerialCard,installHelper,flashApplication,crc32,equal,string,view} from './vendor/organizer/serial.mjs';
import {scanMenu,cartHeader,encodeIndex,uniqueShortName} from './vendor/organizer/menu.mjs';
import {prepareLinkedPackage} from './vendor/organizer/import.mjs';

const REPOSITORY='juliendorra/chgame-pinball';
const RELEASE_RELAY='https://chgame-release-relay.juliendorra.workers.dev/api/github-release';
const HELPER_SOURCE='https://raw.githubusercontent.com/juliendorra/chgame-menu-organizer/43bf9d2848c3981495f17b61d4eda86021f50f5e/firmware/helper.bin';
const HELPER_SHA256='85b88d8ddefe2049df9a6e2edc9827a509c16eb708525e6f7466b1fb099e0966';
const cancelled=()=>new DOMException('Pinball setup cancelled','AbortError');
const parent=name=>name.slice(0,Math.max(0,name.lastIndexOf('/')));
const leaf=name=>name.slice(name.lastIndexOf('/')+1);

export async function latestPinballRelease(fetcher=fetch){
 const response=await fetcher('https://api.github.com/repos/'+REPOSITORY+'/releases/latest',{
  credentials:'omit',referrerPolicy:'no-referrer',signal:AbortSignal.timeout(10000),
 });
 if(!response.ok)throw new Error('Could not check the latest Pinball release (HTTP '+response.status+').');
 const release=await response.json();
 const assets=release.assets?.filter(a=>a.state==='uploaded'&&/\.chgame$/i.test(a.name))||[];
 if(assets.length!==1)throw new Error('The latest Pinball release must contain one .chgame package.');
 const url=new URL(assets[0].browser_download_url);
 if(url.origin!=='https://github.com'||url.username||url.password||
    !url.pathname.startsWith('/'+REPOSITORY+'/releases/download/')||!url.pathname.endsWith('.chgame')){
  throw new Error('GitHub returned an unexpected Pinball download URL.');
 }
 return {version:release.tag_name.replace(/^v/,''),url};
}

export function pinballCart(bytes){
 const header=cartHeader(bytes.subarray(0,512),bytes.length);
 const fields=view(bytes);
 if(!header.compatible)throw new Error('The SD Pinball cart is invalid or incompatible.');
 const size=fields.getUint32(16,true),image=bytes.subarray(512,512+size);
 if(crc32(image)!==fields.getUint32(20,true)||string(image.subarray(8,12))==='CHBL'){
  throw new Error('The SD Pinball executable failed verification.');
 }
 const offset=fields.getUint32(108,true),length=fields.getUint32(112,true);
 let metadata;
 if(length){
  if(length>1048576||offset<512+size||offset+length>bytes.length||
     crc32(bytes.subarray(offset,offset+length))!==fields.getUint32(116,true)){
   throw new Error('The SD cart metadata failed verification.');
  }
  metadata=JSON.parse(new TextDecoder().decode(bytes.subarray(offset,offset+length)));
 }
 const id=metadata?.game?.id;
 if(id?id!=='midnight-pinball':header.title!=='MIDNIGHT PINBALL'){
  throw new Error('This cart does not identify itself as Midnight Pinball.');
 }
 return {header,image,metadata};
}

export async function releasePackage(release,fetcher=fetch){
 const local=typeof location!=='undefined'&&['localhost','127.0.0.1','[::1]'].includes(location.hostname);
 const relay=local?new URL('/api/pinball-release',location.origin).href:RELEASE_RELAY;
 const pkg=await prepareLinkedPackage(release.url,fetcher,relay);
 const carts=pkg.files.filter(file=>file.path.startsWith('GAMES/')&&file.path.endsWith('.CHG'));
 if(carts.length!==1)throw new Error('The Pinball release must contain one game.');
 const cart=pinballCart(carts[0].data);
 if(cart.header.version!==release.version)throw new Error('The release tag and packaged game versions differ.');
 return {...pkg,cart:cart,cartBytes:carts[0].data};
}

export async function prepareInstall(card,menu,pkg,existing,destination=menu.root.path){
 const folders=new Map(),directories=[],files=[],preserved=[];
 async function listing(folder){
  if(folders.has(folder))return folders.get(folder);
  const upper=parent(folder);
  if(folder){
   const found=(await listing(upper)).find(entry=>entry.name===leaf(folder));
   if(found&&!found.directory)throw new Error('A file blocks the SD folder '+folder+'.');
   if(!found){directories.push(folder);folders.set(folder,[]);return [];}
  }
  const items=await card.list(folder);folders.set(folder,items);return items;
 }
 for(const file of pkg.files.filter(file=>!file.path.startsWith('GAMES/'))){
  if(!file.path.startsWith('PINBALL/'))throw new Error('Unexpected Pinball asset path '+file.path);
  const found=(await listing(parent(file.path))).find(entry=>entry.name===leaf(file.path));
  if(found?.directory)throw new Error('A folder blocks the SD asset '+file.path+'.');
  // Keep every authored board and its recovery copy. New defaults fill gaps.
  if(found&&/\.(PBT|PBK)$/.test(file.path)){preserved.push(file.path);continue;}
  if(found&&found.size===file.data.length&&await card.check(file.path,found.size)===crc32(file.data))continue;
  files.push({path:file.path,data:file.data});
 }
 let index=null,path=existing?.path;
 if(!path){
  const folder=menu.folders.find(item=>item.path===destination);
  if(!folder||folder.editBlocked||folder.overLimit)throw new Error('Choose an editable SD category.');
  if(folder.entries.length>=240)throw new Error('This SD category is full. Choose another category.');
  const items=await listing(destination);
  const name=uniqueShortName('PINBALL.CHG',new Map(items.map(item=>[item.name,item])));
  path=destination+'/'+name;
  const before=folder.index;
  const bytes=encodeIndex([...folder.entries,{name}]);
  index={path:destination+'/MENU.IDX',before,data:bytes};
 }
 const old=existing&&await card.read(path,0,existing.size);
 if(old)pinballCart(old);
 files.push({path,data:pkg.cartBytes});
 return {directories,files,index,preserved,path,old};
}

export async function writeInstall(card,plan,progress=()=>{}){
 // Detect a cart changed since the offer, before touching any package files.
 if(plan.old&&!equal(await card.read(plan.path,0,plan.old.length),plan.old)){
  throw new Error('The installed Pinball cart changed. Check the SD card again.');
 }
 if(plan.index){
  const folder=parent(plan.index.path),items=await card.list(folder);
  const found=items.find(item=>item.name==='MENU.IDX');
  const actual=found?await card.read(plan.index.path,0,found.size):null;
  if(Boolean(actual)!==Boolean(plan.index.before)||actual&&!equal(actual,plan.index.before)){
   throw new Error('The SD menu changed. Check the SD card again.');
  }
 }
 for(const dir of plan.directories)await card.mkdir(dir);
 for(const file of plan.files){
  progress('Saving '+file.path+'…');
  await card.replace(file.path,file.data);
 }
 if(plan.index)await card.replace(plan.index.path,plan.index.data);
 await card.sync();
}

async function helperImage(fetcher){
 const response=await fetcher(HELPER_SOURCE,{credentials:'omit',referrerPolicy:'no-referrer',signal:AbortSignal.timeout(15000)});
 if(!response.ok)throw new Error('Could not download the SD helper.');
 const bytes=new Uint8Array(await response.arrayBuffer());
 const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
 if(hash!==HELPER_SHA256)throw new Error('The SD helper failed its checksum.');
 return bytes;
}

export async function prepareConsole(serial,port,{
 progress=()=>{},choose,fetcher=fetch,open=Link.open,
 startHelper=installHelper,flash=flashApplication,
 latest=latestPinballRelease,download=releasePackage,helper=helperImage,
}){
 let link,card;
 try{
  progress('Checking the latest Pinball release…');
  const release=await latest(fetcher);
  // Fetch and validate before replacing the current application with the helper.
  progress('Downloading Pinball '+release.version+'…');
  const pkg=await download(release,fetcher);
  link=await open(port);
  card=await SerialCard.identify(link);
  if(card)await card.start();
  else{
   progress('Opening the SD card…');
   card=await startHelper(serial,link,await helper(fetcher),(done,total)=>
    progress('Opening SD card… '+Math.round(done*100/total)+'%'));
   link=card.link;
  }
  progress('Finding Pinball on the SD card…');
  const root=await card.list('');
  const menu=root.some(entry=>entry.name==='GAMES'&&entry.directory)?
   await scanMenu(card,folder=>progress('Checking '+folder.path+'…')):
   {root:{path:'GAMES',entries:[],index:null},folders:[]};
  if(!menu.folders.length)menu.folders=[menu.root];
  const candidates=menu.folders.flatMap(folder=>folder.entries)
   .filter(entry=>!entry.directory&&entry.compatible&&entry.title==='MIDNIGHT PINBALL');
  let existing,image;
  for(const entry of candidates){
   const bytes=await card.read(entry.path,0,entry.size),cart=pinballCart(bytes);
   if(!existing){existing=entry;image=cart.image;}
   if(entry.version===release.version&&equal(cart.image,pkg.cart.image)){existing=entry;image=cart.image;break;}
  }
  const destination=menu.folders[0].path;
  let plan=await prepareInstall(card,menu,pkg,existing,destination);
  const assetsChanged=plan.files.some(file=>file.path!==plan.path&&!/\.(PBT|PBK)$/.test(file.path));
  if(!image||existing.version!==release.version||!equal(image,pkg.cart.image)||assetsChanged){
   const answer=await choose({
    title:existing?'Update Pinball on SD?':'Install Pinball on SD?',
    description:existing?'SD version '+existing.version+' at '+existing.path+'. Latest release '+release.version+'.':
     'Pinball is missing from this SD card. Latest release '+release.version+'.',
    detail:'Keeps existing boards and high scores. '+plan.files.length+' files will be saved and verified.',
    folders:existing?[]:menu.folders.filter(folder=>!folder.editBlocked&&!folder.overLimit),
    choices:existing?[
     {value:'install',label:'Update SD & launch'},
     {value:'launch',label:'Launch SD version '+existing.version},
     {value:'cancel',label:'Cancel'},
    ]:[{value:'install',label:'Install to SD & launch'},{value:'cancel',label:'Cancel'}],
   });
   if(answer.action==='cancel')throw cancelled();
   if(answer.action==='install'){
    if(!existing&&answer.destination&&answer.destination!==destination){
     plan=await prepareInstall(card,menu,pkg,null,answer.destination);
    }
    await writeInstall(card,plan,progress);
    image=pkg.cart.image;
   }
  }
  progress('Launching Pinball from the SD cart…');
  await card.sync();
  // RUN starts internal flash. Use the verified SD payload through the
  // existing bootloader uploader, then RUN and reconnect to Pinball.
  const next=await flash(serial,link,image,(done,total)=>
   progress('Starting Pinball… '+Math.round(done*100/total)+'%'));
  link=null;
  return next;
 }catch(error){
  // Leave the SD helper through its synchronized menu exit on cancellation.
  if(card&&!card.link.disconnected)await card.menu().catch(()=>{});
  throw error;
 }finally{await link?.close();}
}
