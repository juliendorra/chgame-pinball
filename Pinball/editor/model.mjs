export const KINDS=['wall','bumper','target','lane','scoop','flippers','ramp','spinner','drop_target','kickback','gate','saucer'];
export const CATALOG=[
 ['wall','Rail','Solid, rounded rubber rail','rail',40,145,74,112,0],
 ['bumper','Pop bumper','Powered rebound · scores on impact','bumper',64,110,8,280,180],
 ['target','Stand-up target','Lights one of three target banks','target',64,95,6,4,250],
 ['lane','Rollover','Complete three colors for a multiplier','lane',64,38,6,0,500],
 ['scoop','Lock scoop','Capture · power run · multiball','scoop',64,150,7,0,1000],
 ['flippers','Flipper pair','Art-matched collision · both keyboard sides','flipper',30,230,90,20,0],
 ['ramp','Side ramp','Elevated curve · follow camera · return feed','ramp',30,230,85,145,1800],
 ['spinner','Spinner','Pass through to spin and score','spinner',64,120,10,0,150],
 ['drop_target','Drop target','Collapses on impact, then resets','drop_target',64,110,6,4,300],
 ['kickback','Kickback','One-shot outlane rescue','kickback',14,270,5,1200,500],
 ['gate','One-way gate','Hinged arm · direction arrow · target-bank lock','gate',64,90,84,90,0],
 ['saucer','Saucer','Timed hold · award · controlled eject','saucer',64,160,7,90,750],
].map(([kind,name,description,sprite,x,y,u,v,value])=>({kind,name,description,sprite,defaults:{kind,x,y,u,v,value,group:0}}));
export const THEMES=['Neon Pursuit','Orbital Robot','Shuttle Run','Storm Riders','Solar Temple','Midnight Manor','Cosmic Carnival','Dragon Keep','Buccaneer Bay'];
export const copy=value=>structuredClone(value);
export function createPart(kind,p,height){
 const def=CATALOG.find(c=>c.kind===kind),o=copy(def.defaults);
 o.x=Math.max(5,Math.min(108,p.x));o.y=Math.max(12,Math.min(height-55,p.y));
 if(kind==='flippers'){o.x=30;o.u=90;o.y=Math.max(80,o.y);}
 else if(kind==='ramp'){o.y=Math.max(90,o.y);o.u=o.x<60?90:20;o.v=Math.max(12,o.y-80);}
 else if(['wall','gate'].includes(kind)){o.u=Math.min(110,o.x+24);o.v=Math.max(8,o.y-(kind==='wall'?22:0));}
 return o;
}
export function fnv(bytes,table=false){let hash=2166136261;for(let i=0;i<bytes.length;i++)hash=Math.imul(hash^(table&&i>=16&&i<20?0:bytes[i]),16777619)>>>0;return hash;}
const ascii=(s,max)=>typeof s==='string'&&s.length>0&&s.length<=max&&/^[\x20-\x7e]+$/.test(s);
export function validate(b){
 const errors=[],warnings=[];const bad=(ok,msg)=>{if(!ok)errors.push(msg);};const range=(v,l,h)=>Number.isInteger(v)&&v>=l&&v<=h;
 bad(/^[A-Z0-9_]{1,8}$/.test(b.file),'SD filename needs 1–8 uppercase letters, numbers or underscores.');
 bad(ascii(b.title,19),'Title needs 1–19 printable ASCII characters.');bad(ascii(b.mission,23),'Mission needs 1–23 printable ASCII characters.');
 bad(range(b.id,1,0xffffffff),'Board ID must be a nonzero unsigned integer.');bad(range(b.height,256,480),'Height must be 256–480.');bad(range(b.gravity,8,44),'Gravity must be 8–44.');bad(range(b.theme,0,8),'Choose one of nine themes.');
 bad(Array.isArray(b.palette)&&b.palette.length===16&&b.palette.every(c=>/^[0-9a-f]{3}$/i.test(c)),'Palette needs sixteen RGB444 colors.');
 bad(Array.isArray(b.objects)&&b.objects.length<=72,'A board holds up to 72 elements.');
 for(const [i,o] of (b.objects||[]).entries()){
  let ok=KINDS.includes(o.kind)&&range(o.x,5,108)&&range(o.y,8,b.height-50)&&range(o.group,0,2)&&range(o.value,0,10000)&&range(o.u,-32768,32767)&&range(o.v,-32768,32767);
  if(['wall','gate'].includes(o.kind))ok&&=range(o.u,5,110)&&range(o.v,8,b.height-40)&&(o.x!==o.u||o.y!==o.v);
  else if(o.kind==='flippers')ok&&=range(o.x,20,38)&&range(o.u,82,100)&&range(o.v,16,26)&&o.y>=80&&o.x+2*o.v+16<=o.u;
  else if(o.kind==='ramp')ok&&=range(o.u,8,105)&&range(o.v,12,b.height-50)&&Math.abs(o.y-o.v)>=32;
  else if(['target','drop_target'].includes(o.kind))ok&&=range(o.u,3,12)&&range(o.v,3,12);
  else if(o.kind==='spinner')ok&&=range(o.u,6,16);
  else ok&&=range(o.u,3,12)&&range(o.v,0,1600);
  bad(ok,`Element ${i+1} (${o.kind}) is outside its position or size limits.`);
 }
 for(const [kind,label] of [['target','target bank'],['lane','rollover']]){
  const groups=new Set(b.objects?.filter(o=>o.kind===kind||(kind==='target'&&o.kind==='drop_target')).map(o=>o.group));
  if(groups.size<3)warnings.push(`Add all three ${label} colors to enable its completion award.`);
 }
 if(!b.objects?.some(o=>o.kind==='scoop'))warnings.push('Add a lock scoop to enable multiball and jackpots.');
 return {errors,warnings};
}
export function encode(board){
 const {errors}=validate(board);if(errors.length)throw new Error(errors[0]);
 const bytes=new Uint8Array(96+board.objects.length*12),v=new DataView(bytes.buffer),text=new TextEncoder();
 bytes.set(text.encode('PBT1'));bytes[4]=1;bytes[5]=board.theme;bytes[6]=board.objects.length;
 v.setUint16(8,board.height,true);v.setUint16(10,board.gravity,true);v.setUint32(12,board.id,true);
 bytes.set(text.encode(board.title),20);bytes.set(text.encode(board.mission),40);
 board.palette.forEach((c,i)=>v.setUint16(64+i*2,parseInt(c,16),true));
 board.objects.forEach((o,i)=>{let a=96+i*12;bytes[a]=KINDS.indexOf(o.kind);bytes[a+1]=o.group;for(const [j,k]of ['x','y','u','v'].entries())v.setInt16(a+2+j*2,o[k],true);v.setUint16(a+10,o.value,true);});
 v.setUint32(16,fnv(bytes,true),true);return bytes;
}
export function decode(bytes,file='IMPORT'){
 if(!(bytes instanceof Uint8Array))bytes=new Uint8Array(bytes);if(bytes.length<96)throw new Error('Board file is truncated.');
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),text=new TextDecoder(),read=(at,n)=>text.decode(bytes.slice(at,at+n)).split('\0')[0];
 if(read(0,4)!=='PBT1'||bytes[4]!==1||bytes[7]||bytes.length!==96+bytes[6]*12||v.getUint32(16,true)!==fnv(bytes,true))throw new Error('Board file has an invalid header, size or checksum.');
 const b={file:file.replace(/\.pbt$/i,'').toUpperCase(),id:v.getUint32(12,true),theme:bytes[5],height:v.getUint16(8,true),gravity:v.getUint16(10,true),title:read(20,20),mission:read(40,24),palette:[],objects:[]};
 for(let i=0;i<16;i++)b.palette.push(v.getUint16(64+i*2,true).toString(16).padStart(3,'0').toUpperCase());
 for(let at=96;at<bytes.length;at+=12){const o={kind:KINDS[bytes[at]],group:bytes[at+1],value:v.getUint16(at+10,true)};['x','y','u','v'].forEach((k,i)=>o[k]=v.getInt16(at+2+i*2,true));b.objects.push(o);}
 const {errors}=validate(b);if(errors.length)throw new Error(errors[0]);return b;
}
export function newIdentity(board,boards,title=''){
 const result=copy(board);let id;do{id=crypto.getRandomValues(new Uint32Array(1))[0];}while(!id||boards.some(b=>b.id===id));result.id=id;
 const root=board.file.slice(0,5);let n=1;do{result.file=root+String(n++).padStart(3,'0');}while(boards.some(b=>b.file===result.file));
 result.title=(title||board.title+' II').slice(0,19);return result;
}
export function controlsForKey(event){
 if(event.metaKey||event.ctrlKey||event.altKey)return 0;
 const k=(event.key||'').toLowerCase(),c=event.code;
 if(c==='ShiftLeft'||k==='arrowleft')return 16;
 if(c==='ShiftRight'||k==='d'||k==='b')return 2;
 if(c==='Space'||c==='Enter'||c==='NumpadEnter'||k==='arrowdown')return 8;
 if(k==='a')return 1;
 if(k==='arrowright')return 32;
 return 0;
}
export function rampPoint(o,t){const a=1-t,cx=o.group===0?12:o.group===1?101:(o.x+o.u)/2,cy=(o.y+o.v)/2-20;return {x:a*a*o.x+2*a*t*cx+t*t*o.u,y:a*a*o.y+2*a*t*cy+t*t*o.v};}
function segmentDistance(x,y,a,b){let dx=b.x-a.x,dy=b.y-a.y,t=Math.max(0,Math.min(1,((x-a.x)*dx+(y-a.y)*dy)/(dx*dx+dy*dy||1)));return Math.hypot(x-a.x-t*dx,y-a.y-t*dy);}
export function pick(board,x,y){
 let chosen=-1,nearest=Infinity;
 board.objects.forEach((o,i)=>{
  let d;
  if(['wall','gate'].includes(o.kind))d=segmentDistance(x,y,o,{x:o.u,y:o.v})-3;
  else if(o.kind==='ramp'){d=Infinity;let a=o;for(let j=1;j<=16;j++){let b=rampPoint(o,j/16);d=Math.min(d,segmentDistance(x,y,a,b)-5);a=b;}}
  else if(o.kind==='flippers')d=Math.min(segmentDistance(x,y,o,{x:o.x+o.v,y:o.y+9}),segmentDistance(x,y,{x:o.u,y:o.y},{x:o.u-o.v,y:o.y+9}))-5;
  else d=Math.hypot(x-o.x,y-o.y)-(o.kind==='target'||o.kind==='drop_target'?6:o.u);
  if(d<=5&&d<nearest){chosen=i;nearest=d;}
 });return chosen;
}
export function handles(o){return o&&['wall','ramp','gate'].includes(o.kind)?[{x:o.x,y:o.y,key:'start'},{x:o.u,y:o.v,key:'end'}]:[];}
