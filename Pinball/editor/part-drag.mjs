// Palette drag artwork only. Play continues to use the native C++ renderer.
import {CATALOG,rampPoint} from './model.mjs';
const INKS={'.':-1,'0':2,w:1,m:3,t:4,d:7,i:5,c:4,o:9,g:10,b:12,p:13,s:14,r:6};

export function drawPartPreview(canvas,part,sprites,palette){
 const ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);
 const color=index=>'#'+(index===2?palette[0].split('').map(n=>(parseInt(n,16)>>1).toString(16)).join(''):palette[index]);
 const bank=part.group===0?4:part.group===1?8:10;
 function sprite(name,x,y,scale=1,ink=bank,frame=0){
  const rows=sprites[name]?.[frame];if(!rows)return;
  const left=-Math.floor(rows[0].length*scale/2),top=-Math.floor(rows.length*scale/2);
  ctx.save();ctx.translate(x,y);
  for(const [j,row] of rows.entries())for(const [i,pixel] of [...row].entries()){
   let index=INKS[pixel];if(index<0)continue;if(pixel==='c')index=ink;
   ctx.fillStyle=color(index);ctx.fillRect(left+i*scale,top+j*scale,scale,scale);
  }
  ctx.restore();
 }
 function rail(points,ink){
  ctx.lineCap='round';ctx.lineJoin='round';
  for(const [width,index,dx,dy] of [[6,2,2,3],[5,3,0,0],[3,ink,0,0],[1,14,-1,-1]]){
   ctx.beginPath();points.forEach((p,i)=>ctx[i?'lineTo':'moveTo'](p.x+dx,p.y+dy));ctx.strokeStyle=color(index);ctx.lineWidth=width;ctx.stroke();
  }
 }
 if(part.kind==='wall'||part.kind==='gate'){
  rail([part,{x:part.u,y:part.v}],part.kind==='wall'?14:10);
  if(part.kind==='gate'){
   sprite('gate',part.x,part.y,1,10);ctx.fillStyle=color(14);ctx.fillRect(part.u-1,part.v-1,3,3);
   const dx=part.u-part.x,dy=part.v-part.y,len=Math.hypot(dx,dy),side=(part.group===1?-1:1)*(dx<0||(dx===0&&dy<0)?-1:1),nx=dy*side/len,ny=-dx*side/len,x=(part.x+part.u)/2+nx*8,y=(part.y+part.v)/2+ny*8;
   ctx.strokeStyle=color(10);ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x-nx*2-dx*2/len,y-ny*2-dy*2/len);ctx.lineTo(x+nx*2,y+ny*2);ctx.lineTo(x-nx*2+dx*2/len,y-ny*2+dy*2/len);ctx.stroke();
  }
 }else if(part.kind==='ramp'){
  const path=[{x:part.x,y:part.y+8,w:6},{x:part.x,y:part.y+4,w:6},...Array.from({length:17},(_,i)=>({...rampPoint(part,i/16),w:i<2?5-i:3}))];
  ctx.beginPath();[...path.map(p=>({x:p.x-p.w,y:p.y})),...path.toReversed().map(p=>({x:p.x+p.w,y:p.y}))].forEach((p,i)=>ctx[i?'lineTo':'moveTo'](p.x,p.y));ctx.closePath();ctx.fillStyle=color(5);ctx.fill();
  sprite('ramp',part.x,part.y);
  for(const side of [-1,1])rail(path.map(p=>({x:p.x+side*p.w,y:p.y})),side<0?5:14);
  sprite('ramp',part.x-1,part.y+4,1,4,1);
 }else if(part.kind==='flippers'){
  const rows=sprites.flipper[0],scale=part.v/23;
  for(const [pivot,side] of [[part.x,1],[part.u,-1]]){
   ctx.save();ctx.translate(pivot,part.y);ctx.scale(side*scale,scale);ctx.rotate(18*Math.PI*2/256);
   rows.forEach((row,y)=>[...row].forEach((pixel,x)=>{if(INKS[pixel]<0)return;ctx.fillStyle=color(INKS[pixel]);ctx.fillRect(x-6,y-6,1,1);}));ctx.restore();
  }
 }else{
  const def=CATALOG.find(d=>d.kind===part.kind);
  sprite(def.sprite,part.x,part.y,part.kind==='bumper'?(2*part.u+3)/19:1,part.kind==='kickback'?11:bank);
 }
}
