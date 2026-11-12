import {BoardStorage} from './board-storage.mjs';
import {BoardPicker} from './board-picker.mjs';
import {DeviceKeyStream} from './key-stream.mjs';
import {CATALOG,THEMES,copy,createPart,validate,encode,decode,newIdentity,nextBoardFilename,controlsForKey,pick,handles,rampPoint,editableBoard,rubberOutline,boardNumberLimits,elementLimits,validElement} from './model.mjs';
import {BrowserDevice} from './serial.mjs';
import {drawPartPreview} from './part-drag.mjs';
import {WasmEngine} from './wasm-engine.mjs';
import {PlaySession} from './play-session.mjs';
import {fitBoard,followScroll} from './layout.mjs';
const $=s=>document.querySelector(s),NS='http://www.w3.org/2000/svg',HEADER_HEIGHT=24;
const state={boards:[],validBoards:{},id:null,selected:-1,undo:[],redo:[],revision:0,zoom:1.5,fit:true,mask:0,pressed:new Map(),device:false,direct:null,uploading:false,lastState:null,lastFrame:null,drag:null,ready:false};
const board=()=>state.boards.find(b=>b.id===state.id);
let engine,play,deviceTimer,toastTimer,sprites,bases,borders;
let storage=new BoardStorage({onChange:storageChanged});
state.browserSaved=true;
const boardPicker=new BoardPicker($('#boardPicker'),id=>{choose(id);canvas.focus({preventScroll:true});},releaseKeys);
function toast(text){$('#toast').textContent=text;$('#toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('show'),4200);}
function status(text,error=false){$('#syncStatus').textContent=text;$('#syncStatus').classList.toggle('error',error);}
function persist(){try{localStorage.setItem('midnight-studio-v1',JSON.stringify({boards:state.boards,validBoards:state.validBoards,id:state.id,storage:storage.export(),separatePlay:!!state.separatePlay}));state.browserSaved=true;}catch{state.browserSaved=false;}}
function remember(){state.undo.push(copy(board()));if(state.undo.length>80)state.undo.shift();state.redo=[];historyButtons();}
function historyButtons(){$('#undoButton').disabled=!state.undo.length;$('#redoButton').disabled=!state.redo.length;}
function restore(redo=false){const source=redo?state.redo:state.undo,target=redo?state.undo:state.redo;if(!source.length)return;target.push(copy(board()));state.boards[state.boards.findIndex(b=>b.id===state.id)]=source.pop();state.selected=-1;refresh();edited(false);}
function send(data){if(play)Promise.resolve(play.send(data)).catch(e=>toast(e.message));else engine?.send(data);}
function edited(snapshot=true,isEdit=true){
 if(snapshot)remember();state.revision++;refreshLibrary();refreshFieldLimits();$('#boardHeading').textContent=board().title;$('#elementCount').textContent=`${board().objects.length} / 72 elements`;
 const result=validate(board());if(!result.errors.length)state.validBoards[state.id]=copy(board());persist();showValidation(result);selection();
 clearTimeout(deviceTimer);deviceTimer=undefined;
 if(isEdit)storage.changed(board());else storage.select(board());
 if(result.errors.length){status('Fix the highlighted limits · previous valid board is still playing',true);return;}
 status(play?.followsConsole?'Draft preview · waiting for CHGame':'Applying live edit…');
 send({type:'board',board:copy(board()),revision:state.revision});
 if(state.device&&$('#liveDevice').checked)deviceTimer=setTimeout(()=>{deviceTimer=undefined;uploadDevice();},180);
}
function showValidation({errors,warnings}){const box=$('#validation');box.replaceChildren();for(const text of [...errors,...warnings]){const p=document.createElement('p');p.textContent=(errors.includes(text)?'! ':'↳ ')+text;if(errors.includes(text))p.className='error';box.append(p);}}
function refreshLibrary(){boardPicker.update(state.boards,state.id,borders,b=>storage.view(b));$('#boardCount').textContent=state.boards.length;}
function choose(id){releaseKeys();state.id=Number(id);state.selected=-1;state.undo=[];state.redo=[];state.lastFrame=null;refresh();if(validate(board()).errors.length&&state.validBoards[state.id])send({type:'board',board:copy(state.validBoards[state.id]),revision:state.revision});edited(false,false);fit();}
function refresh(){
 refreshLibrary();historyButtons();const b=board();$('#boardHeading').textContent=b.title;
 for(const [selector,key] of [['#titleInput','title'],['#missionInput','mission'],['#heightInput','height'],['#gravityInput','gravity'],['#fileInput','file'],['#themeSelect','theme']])$(selector).value=b[key];
 $('#elementCount').textContent=`${b.objects.length} / 72 elements`;themeStrip();inspector();refreshFieldLimits();showValidation(validate(b));resizeCanvas();selection();paintIcons();renderStorage();
}
function themeStrip(){const strip=$('#themeStrip');strip.replaceChildren();board().palette.slice(0,15).forEach(c=>{const s=document.createElement('span');s.style.background='#'+c;strip.append(s);});}
function resizeCanvas(){const c=$('#boardCanvas'),height=Number.isInteger(board().height)&&board().height>=256&&board().height<=480?board().height:(state.validBoards[state.id]?.height||384);if(c.height!==height){c.height=height;$('#selection').setAttribute('viewBox',`0 0 128 ${height}`);}c.style.width=128*state.zoom+'px';c.style.height=height*state.zoom+'px';$('#headerCanvas').style.width=128*state.zoom+'px';$('#headerCanvas').style.height=HEADER_HEIGHT*state.zoom+'px';$('#fitButton').textContent=state.fit?'Fit':Math.round(state.zoom*100)+'%';}
function fit(){state.fit=true;const box=$('#boardViewport'),padding=getComputedStyle($('#boardSurface'));if(!box.clientWidth||!box.clientHeight)return;state.zoom=fitBoard(box.clientWidth,box.clientHeight,canvas.height,parseFloat(padding.paddingLeft)+parseFloat(padding.paddingRight),parseFloat(padding.paddingTop)+parseFloat(padding.paddingBottom));resizeCanvas();selection();}
function zoom(direction){state.fit=false;state.zoom=Math.max(.2,Math.min(5,state.zoom+direction*.35));resizeCanvas();selection();if(state.lastState)followViewport(state.lastState,true);}
function setNumberLimits(input,[min,max]){
 input.min=String(min);input.max=String(max);input.step='1';
}
function bindNumber(input,read,write){
 let recorded=false;
 input.addEventListener('focus',()=>{recorded=false;});
 const record=()=>{if(!recorded){remember();recorded=true;}};
 function update(commit){
  const current=read();
  if(current===undefined)return;
  const min=Number(input.min),max=Number(input.max);
  let value=input.valueAsNumber;
  if(commit&&Number.isFinite(value)&&min<=max)value=Math.max(min,Math.min(max,Math.round(value)));
  if(Number.isInteger(value)&&value>=min&&value<=max&&value!==current)write(value,record);
  if(commit)input.value=read();
 }
 input.addEventListener('input',()=>update(false));
 input.addEventListener('blur',()=>update(true));
 input.addEventListener('keydown',event=>{if(event.key==='Enter')input.blur();});
}
function field(label,key,o,options){
 const container=document.createElement('div'),l=document.createElement('label');
 const input=document.createElement(options?'select':'input');
 container.className='field';input.id='prop-'+key;l.htmlFor=input.id;l.textContent=label;
 const read=()=>board().objects[state.selected]?.[key];
 const write=(value,record)=>{
  const part=board().objects[state.selected];
  if(!part)return;
  const candidate={...part,[key]:value};
  if(!validElement(candidate,board())&&validElement(part,board()))return;
  record();part[key]=value;edited(false);
 };
 if(options){
  options.forEach((text,i)=>input.add(new Option(text,i)));
  input.addEventListener('change',()=>{if(Number(input.value)!==read())write(Number(input.value),remember);input.value=read();});
 }else{
  input.type='number';
  setNumberLimits(input,elementLimits(o,board().height)[key]);
  bindNumber(input,read,write);
 }
 input.value=o[key];input.dataset.property=key;container.append(l,input);return container;
}
function refreshFieldLimits(){
 const b=board(),part=b.objects[state.selected];
 for(const key of ['height','gravity'])setNumberLimits($('#'+key+'Input'),boardNumberLimits(b,key));
 if(!part)return;
 const limits=elementLimits(part,b.height);
 for(const input of $('#inspector').querySelectorAll('[data-property]')){
  if(input.type==='number')setNumberLimits(input,limits[input.dataset.property]);
  else for(const option of input.options)option.disabled=Number(option.value)!==part.group&&!validElement({...part,group:Number(option.value)},b);
 }
}
function inspector(){
 const box=$('#inspector'),o=board().objects[state.selected];box.replaceChildren();
 if(!o)return;
 const definition=CATALOG.find(c=>c.kind===o.kind),title=document.createElement('div'),p=document.createElement('p');title.className='section-title';title.textContent=definition.name.toUpperCase();p.className='description';p.textContent=definition.description;box.append(title,p);
 if(o.kind==='ramp'){const intent=document.createElement('div');intent.id='selectionIntent';intent.className='selection-intent';intent.setAttribute('role','status');intent.textContent='Whole ramp';box.append(intent);}
 const row=document.createElement('div');row.className='field-row';row.append(field('X','x',o),field('Y','y',o));box.append(row);
 const names={rubber:['Width','Height'],wall:['End X','End Y'],gate:['End X','End Y'],ramp:['Exit X','Exit Y'],flippers:['Right pivot X','Bat length'],target:['Width','Height'],drop_target:['Width','Height'],spinner:['Half-width','Kick'],scoop:['Radius','Kick'],saucer:['Radius','Hold / kick'],kickback:['Radius','Kick'],bumper:['Radius','Kick'],lane:['Radius','Kick']}[o.kind];
 const dimensions=document.createElement('div');dimensions.className='field-row';if(o.kind!=='spinner')dimensions.append(field(names[0],'u',o));if(['wall','gate','ramp','flippers','target','drop_target','bumper','rubber'].includes(o.kind))dimensions.append(field(names[1],'v',o));box.append(dimensions);if(!['wall','flippers','spinner','kickback'].includes(o.kind))box.append(field(o.kind==='ramp'?'Curve':o.kind==='gate'?'Gate rule':o.kind==='rubber'?'Facing':'Color bank','group',o,o.kind==='ramp'?['Left side','Right side','Center']:o.kind==='rubber'?['Left · points right','Right · points left']:o.kind==='gate'?['Pass toward upper side','Pass toward lower side','Unlock with all target banks']:['Cyan','Pink','Gold']));if(!['wall','gate','flippers'].includes(o.kind))box.append(field('Points','value',o));
 const actions=document.createElement('div');actions.className='selection-actions';const duplicate=document.createElement('button'),remove=document.createElement('button');duplicate.textContent='⧉ Duplicate';duplicate.onclick=duplicatePart;remove.textContent='Remove';remove.className='delete';remove.onclick=removePart;actions.append(duplicate,remove);box.append(actions);refreshFieldLimits();
}
function refreshCoordinates(){const o=board().objects[state.selected];if(!o)return;for(const k of ['x','y','u','v']){const input=$('#prop-'+k);if(input&&document.activeElement!==input)input.value=o[k];}}
function selection(){
 const svg=$('#selection');svg.replaceChildren();const o=board().objects[state.selected];if(!o)return;
 const shape=document.createElementNS(NS,'path');shape.setAttribute('class','selection-outline');
 if(o.kind==='ramp'){
  let d=`M ${o.x} ${o.y+8} L ${o.x} ${o.y}`;for(let i=1;i<=16;i++){const p=rampPoint(o,i/16);d+=` L ${p.x} ${p.y}`;}
  shape.setAttribute('d',d);shape.setAttribute('class','ramp-selection');shape.dataset.action=state.drag&&!state.drag.handle?'whole':'';svg.append(shape);
  for(const p of handles(o)){
   const r=6/state.zoom,c=document.createElementNS(NS,p.key==='end'?'path':'circle');
   if(p.key==='end')c.setAttribute('d',`M ${p.x} ${p.y-r} L ${p.x+r} ${p.y} L ${p.x} ${p.y+r} L ${p.x-r} ${p.y} Z`);
   else{c.setAttribute('cx',p.x);c.setAttribute('cy',p.y);c.setAttribute('r',r);}
   c.setAttribute('class','ramp-handle');c.dataset.end=p.key;c.dataset.active=String(state.drag?.handle===p.key);svg.append(c);
   const label=document.createElementNS(NS,'text');label.setAttribute('class','ramp-end-label');label.setAttribute('font-size',10/state.zoom);
   label.setAttribute('x',Math.max(2,Math.min(128-38/state.zoom,p.x+10/state.zoom)));label.setAttribute('y',p.y+(p.key==='start'?14:-10)/state.zoom);
   label.textContent=p.key==='start'?'ENTRY':'EXIT';svg.append(label);
  }
  const intent=$('#selectionIntent');if(intent)intent.textContent=state.drag?(state.drag.handle==='start'?'Moving entry':state.drag.handle==='end'?'Moving exit':'Moving whole ramp'):'Whole ramp · green entry / violet exit';
  return;
 }
 else if(o.kind==='rubber'){shape.setAttribute('d',rubberOutline(o).map((p,i)=>`${i?'L':'M'} ${p.x} ${p.y}`).join(' ')+' Z');shape.setAttribute('fill','none');svg.append(shape);}
 else if(['wall','gate'].includes(o.kind)){shape.setAttribute('d',`M ${o.x} ${o.y} L ${o.u} ${o.v}`);shape.style.strokeWidth=8;svg.append(shape);}
 else{const rect=document.createElementNS(NS,'rect');const fl=o.kind==='flippers',r=fl?6:Math.max(6,o.u)+3;rect.setAttribute('x',o.x-r);rect.setAttribute('y',o.y-r);rect.setAttribute('width',fl?o.u-o.x+r*2:r*2);rect.setAttribute('height',fl?25:r*2);rect.setAttribute('rx','3');rect.setAttribute('class','selection-outline');svg.append(rect);}
 for(const p of handles(o)){const c=document.createElementNS(NS,'circle');c.setAttribute('cx',p.x);c.setAttribute('cy',p.y);c.setAttribute('r','2.4');c.setAttribute('class','selection-handle');svg.append(c);}
}
function point(event){const rect=$('#boardCanvas').getBoundingClientRect();return {x:Math.round((event.clientX-rect.left)*128/rect.width),y:Math.round((event.clientY-rect.top)*board().height/rect.height)};}
function dropPoint(){const viewport=$('#boardViewport'),canvas=$('#boardCanvas').getBoundingClientRect(),area=viewport.getBoundingClientRect();return {x:64,y:Math.max(15,Math.min(board().height-65,Math.round((area.top+area.height*.4-canvas.top)/state.zoom)))};}
function add(kind,p=dropPoint()){
 if(board().objects.length>=72)return toast('This board already has 72 elements.');const o=createPart(kind,p,board().height);
 if(!validElement(o,board()))return toast('This part does not fit at that position.');
 remember();board().objects.push(o);state.selected=board().objects.length-1;inspector();edited(false);$('#boardCanvas').focus({preventScroll:true});
}
function removePart(){if(state.selected<0)return;remember();board().objects.splice(state.selected,1);state.selected=-1;inspector();edited(false);}
function duplicatePart(){
 const b=board(),part=b.objects[state.selected];
 if(!part||b.objects.length>=72)return;
 for(const [dx,dy] of [[6,8],[-6,8],[6,-8],[-6,-8],[0,8],[0,-8]]){
  const o={...part,x:part.x+(part.kind==='flippers'?0:dx),y:part.y+dy};
  if(['wall','gate','ramp'].includes(o.kind)){o.u+=dx;o.v+=dy;}
  if(!validElement(o,b))continue;
  remember();b.objects.push(o);state.selected=b.objects.length-1;inspector();edited(false);return;
 }
 toast('Move this part away from the edge to duplicate it.');
}
function create(blank=false){const b=newIdentity(board(),state.boards,blank?'Untitled board':'');if(blank){b.objects=[];b.mission='BUILD YOUR OWN RUN';}state.boards.push(b);choose(b.id);storage.changed(b);toast(blank?'A blank board, ready to build.':'Cloned with its own board ID and high score.');}
const canvas=$('#boardCanvas');
canvas.addEventListener('pointerdown',e=>{
 if(e.button!==0)return;canvas.focus({preventScroll:true});const p=point(e);if(e.altKey){dropBall(p);return;}
 let handle=handles(board().objects[state.selected]).find(h=>Math.hypot(h.x-p.x,h.y-p.y)*state.zoom<=8);
 if(!handle)state.selected=pick(board(),p.x,p.y);
 inspector();selection();if(state.selected<0)return;
 state.drag={start:p,original:copy(board().objects[state.selected]),handle:handle?.key};selection();canvas.setPointerCapture(e.pointerId);e.preventDefault();
});
canvas.addEventListener('pointermove',e=>{
 const p=point(e);$('#cursorPosition').textContent=`x ${p.x}  ·  y ${p.y}`;
 if(!state.drag){const o=board().objects[state.selected],handle=handles(o).find(h=>Math.hypot(h.x-p.x,h.y-p.y)*state.zoom<=8);canvas.title=o?.kind==='ramp'?(handle?.key==='start'?'Drag entry':handle?.key==='end'?'Drag exit':'Drag ramp to move the whole part'):'';canvas.style.cursor=handle?'crosshair':pick(board(),p.x,p.y)>=0?'grab':'';return;}
 const d=state.drag,o=copy(d.original),dx=p.x-d.start.x,dy=p.y-d.start.y;
 if(d.handle==='end'){o.u+=dx;o.v+=dy;}
 else if(d.handle==='start'){o.x+=dx;o.y+=dy;}
 else{o.x+=dx;o.y+=dy;if(['wall','ramp','gate'].includes(o.kind)){o.u+=dx;o.v+=dy;}else if(o.kind==='flippers')o.u+=dx;}
 const current=board().objects[state.selected];
 if(['x','y','u','v'].every(key=>o[key]===current[key]))return;
 if(!validElement(o,board()))return;
 if(!state.drag.moved)remember();board().objects[state.selected]=o;state.drag.moved=true;refreshCoordinates();edited(false);
});
function endDrag(){
 const drag=state.drag;
 if(!drag)return;
 state.drag=null;
 state.cameraHoldUntil=performance.now()+600;
 selection();
 if(drag.moved&&deviceTimer!==undefined){
  clearTimeout(deviceTimer);
  deviceTimer=undefined;
  uploadDevice();
 }
}
canvas.addEventListener('pointerup',endDrag);canvas.addEventListener('pointercancel',endDrag);canvas.addEventListener('lostpointercapture',endDrag);
canvas.addEventListener('dblclick',e=>{const p=point(e);if(pick(board(),p.x,p.y)<0)dropBall(p);});
function dropBall(p=dropPoint()){const x=Math.round(Math.max(10,Math.min(108,p.x))),y=Math.round(Math.max(12,Math.min(board().height-20,p.y)));send({type:'place',x,y});}
function followViewport(game,force=false){
 if(state.fit||state.drag||document.body.classList.contains('dragging-part')||!Number.isFinite(game.view_y))return;
 if(!force&&(game.paused||performance.now()<(state.cameraHoldUntil||0)||document.activeElement?.closest('#inspector input,#inspector select,#boardSettings input,#boardSettings select,#boardPicker')))return;
 const viewport=$('#boardViewport');if(viewport.scrollHeight<=viewport.clientHeight+1&&viewport.scrollWidth<=viewport.clientWidth+1)return;
 const area=viewport.getBoundingClientRect(),rect=canvas.getBoundingClientRect();
 const origin={x:rect.left-area.left+viewport.scrollLeft-viewport.clientLeft-game.shake_x*state.zoom,y:rect.top-area.top+viewport.scrollTop-viewport.clientTop-game.shake_y*state.zoom};
 const target=followScroll(game,state.zoom,origin,viewport.clientWidth,viewport.clientHeight,viewport.scrollWidth,viewport.scrollHeight);
 viewport.scrollLeft=target.left;viewport.scrollTop=target.top;
}
$('#boardViewport').addEventListener('wheel',()=>{state.cameraHoldUntil=performance.now()+1200;},{passive:true});
function paintIcons(){if(!sprites||!board())return;const inks={'.':-1,'0':2,w:1,m:3,t:4,d:7,i:5,c:4,o:9,g:10,b:12,p:13,s:14,r:6};
 for(const def of CATALOG){const c=document.querySelector(`[data-part="${def.kind}"] canvas`),ctx=c.getContext('2d'),frame=sprites[def.sprite]?.[0];ctx.clearRect(0,0,c.width,c.height);
 if(def.kind==='rubber'){drawPartPreview(c,{...def.defaults,x:12,y:3,u:12,v:21},sprites,board().palette);continue;}
 if(def.kind==='gate'){drawPartPreview(c,{...def.defaults,x:8,y:18,u:33,v:18},sprites,board().palette);continue;}
 if(def.kind==='ramp'){drawPartPreview(c,{...def.defaults,x:20,y:18,u:24,v:-10},sprites,board().palette);continue;}
 if(!frame){ctx.strokeStyle='#baff76';ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(6,22);ctx.quadraticCurveTo(14,5,33,6);ctx.stroke();continue;}
 const scale=Math.max(1,Math.min(2,Math.floor(40/frame[0].length)));const x=(40-frame[0].length*scale)/2,y=(28-frame.length*scale)/2;
 frame.forEach((r,j)=>[...r].forEach((v,i)=>{if(inks[v]<0)return;ctx.fillStyle='#'+board().palette[inks[v]];ctx.fillRect(x+i*scale,y+j*scale,scale,scale);}));
 }
}
function paletteButtons(){const box=$('#catalog');for(const d of CATALOG){const b=document.createElement('button');b.className='part';b.dataset.part=d.kind;b.title=d.description;const c=document.createElement('canvas');c.width=40;c.height=28;const label=document.createElement('span');label.textContent=d.name;b.append(c,label);b.onclick=()=>add(d.kind);bindPartDrag(b,d.kind);box.append(b);}}
function bindPartDrag(button,kind){
 let drag,dragClick=false;
 const ghost=document.createElement('canvas'),marker=document.createElement('div');ghost.className='part-drag-sprite';marker.className='part-drop-anchor';ghost.hidden=marker.hidden=true;ghost.setAttribute('aria-hidden','true');marker.setAttribute('aria-hidden','true');document.body.append(ghost,marker);
 function show(e){
  const rect=canvas.getBoundingClientRect(),inside=e.clientX>=rect.left&&e.clientX<=rect.right&&e.clientY>=rect.top&&e.clientY<=rect.bottom;
  const p=inside?point(e):{x:64,y:140},part=createPart(kind,p,board().height);
  ghost.width=128;ghost.height=board().height;drawPartPreview(ghost,part,sprites,board().palette);
  ghost.style.width=128*state.zoom+'px';ghost.style.height=board().height*state.zoom+'px';
  const x=inside?rect.left+part.x*state.zoom:e.clientX,y=inside?rect.top+part.y*state.zoom:e.clientY;
  ghost.style.left=(x-part.x*state.zoom)+'px';ghost.style.top=(y-part.y*state.zoom)+'px';ghost.hidden=false;
  marker.style.left=x+'px';marker.style.top=y+'px';marker.hidden=!inside;
  if(inside)$('#cursorPosition').textContent=`Drop at x ${part.x}  ·  y ${part.y}`;
  drag.inside=inside;drag.point=p;
 }
 function end(e,cancel=false){
  if(!drag)return;if(drag.moved&&!cancel)show(e);const active=drag;dragClick=active.moved;drag=null;ghost.hidden=marker.hidden=true;document.body.classList.remove('dragging-part');
  if(button.hasPointerCapture(active.id))button.releasePointerCapture(active.id);
  if(active.moved){e.preventDefault();e.stopPropagation();if(!cancel&&active.inside){add(kind,active.point);const p=createPart(kind,active.point,board().height);$('#cursorPosition').textContent=`x ${p.x}  ·  y ${p.y}`;}else $('#cursorPosition').textContent='Double-click to drop a ball';}
 }
 button.addEventListener('pointerdown',e=>{if(e.button!==0)return;dragClick=false;drag={id:e.pointerId,x:e.clientX,y:e.clientY,moved:false};button.setPointerCapture(e.pointerId);});
 button.addEventListener('pointermove',e=>{if(!drag)return;if(!drag.moved&&Math.hypot(e.clientX-drag.x,e.clientY-drag.y)<5)return;drag.moved=true;document.body.classList.add('dragging-part');show(e);e.preventDefault();});
 button.addEventListener('pointerup',e=>end(e));button.addEventListener('pointercancel',e=>end(e,true));button.addEventListener('lostpointercapture',e=>end(e,true));
 // A pointer drag must not also invoke the button's click-to-add action.
 button.addEventListener('click',e=>{if(e.detail&&dragClick){e.preventDefault();e.stopImmediatePropagation();dragClick=false;}},true);
 window.addEventListener('blur',e=>end(e,true));window.addEventListener('keydown',e=>{if(e.key==='Escape')end(e,true);});
}
function image(bytes,width,height,draftPalette){
 const pixels=bytes.subarray(0,width*height/2),palette=new DataView(bytes.buffer,bytes.byteOffset+width*height/2,32),colors=[];
 for(let i=0;i<16;i++){
  let rgb;
  if(draftPalette)rgb=i===2?(parseInt(draftPalette[0],16)>>1)&0x777:parseInt(draftPalette[i],16);
  else{
   const v=palette.getUint16(i*2,true);
   rgb=((v>>12)<<8)|(((v>>7)&15)<<4)|((v>>1)&15);
  }
  colors.push([((rgb>>8)&15)*17,((rgb>>4)&15)*17,(rgb&15)*17,255]);
 }
 const result=new ImageData(width,height);for(let i=0;i<width*height;i++){const col=colors[(pixels[i>>1]>>((i&1)*4))&15];result.data.set(col,i*4);}return result;
}
function showShake(s){
 const active=s.shake_ticks>0||s.tilt>=3,stage=$('.stage'),wrap=$('.canvas-wrap'),badge=$('#shakeFeedback');
 stage.classList.toggle('shaking',active);badge.hidden=!active;
 wrap.dataset.shake=active?(s.tilt>=3?'tilt':s.shake_level>=3?'danger':'shove'):'';
 wrap.dataset.impact=String(s.shake_ticks>24&&(41-s.shake_ticks)%12<6);
 if(active){const direction=s.shake_direction<0?'←':'→',label=s.tilt>=3?'TILT · WAIT FOR DRAIN':`${direction} ${s.shake_level>=3?'DANGER':'SHAKE'} · ${s.shake_level}/3`;
  if(badge.textContent!==label)badge.textContent=label;badge.dataset.danger=String(s.shake_level>=3||s.tilt>=3);}
}
function engineFrame(game,bytes,draft){
 const visible=draft||game;
 if(visible.id!==board().id||visible.height!==canvas.height)return;
 const full=image(bytes,128,visible.height+HEADER_HEIGHT,draft?.palette);$('#headerCanvas').getContext('2d').putImageData(full,0,0);canvas.getContext('2d').putImageData(full,0,-HEADER_HEIGHT);
 if(game.id!==visible.id||game.height!==visible.height)return;
 state.lastState=game;const pause=$('#pauseButton'),pauseLabel=game.paused?'▶ Resume':'Ⅱ Pause';if(pause.textContent!==pauseLabel)pause.textContent=pauseLabel;pause.setAttribute('aria-label',game.paused?'Resume':'Pause');pause.dataset.paused=String(Boolean(game.paused));
 $('#playScore').textContent=game.score.toLocaleString();$('#playBall').textContent=game.over?'GAME OVER':`${game.lives} BALL${game.lives===1?'':'S'} · ×${game.effective_mult}`;
 const mission=$('#laneMission');mission.hidden=game.lane_groups!==7;
 if(!mission.hidden){
  const missing=[];
  for(let g=0;g<3;g++){
   const lamp=mission.querySelector(`[data-lane="${g}"]`),letter=String.fromCharCode(65+g),done=Boolean(game.lanes&(1<<g));
   lamp.classList.toggle('done',done);lamp.style.setProperty('--lane-ink','#'+board().palette[[4,8,10][g]]);
   lamp.setAttribute('aria-label',`Lane ${letter}: ${done?'collected':'still needed'}`);if(!done)missing.push(letter);
  }
  $('#laneReward').textContent=game.mult>=5?'Ball save':`Next ×${game.lane_goal}`;
  $('#laneMissionHint').textContent=`${missing.length} left · hit ${missing.join(' + ')} in one ball`;
 }
 $('.canvas-wrap').style.transform=`translate(${game.shake_x*state.zoom}px,${game.shake_y*state.zoom}px)`;showShake(game);
 for(const [key,value] of Object.entries({shakeLevel:game.shake_level,tilt:game.tilt,ticks:game.ticks,score:game.score,ballX:game.x,ballY:game.y,left:game.left,right:game.right,shooter:game.shooter,shooterFlap:game.shooter_flap,seed:game.seed}))canvas.dataset[key]=value;
 state.lastFrame=performance.now();$('#engineLoading').hidden=true;
 followViewport(game);
 renderPlayMode();
}
function renderPlayMode(){
 const mode=play?.mode||'web',panel=$('#playStatus');panel.dataset.mode=mode;
 $('#playModeTitle').textContent=mode==='console'?'CONSOLE PLAY':mode==='starting'?'STARTING CONSOLE PLAY':mode==='error'?'CONSOLE PLAY INTERRUPTED':state.device?'WEB PLAY · SEPARATE GAMES':'WEB PLAY';
 const lag=Math.max(0,(engine?.receivedFrame||0)-(engine?.appliedFrame||0));
 $('#playModeDescription').textContent=mode==='console'?'Keyboard → CHGame · browser follows'+(lag>12?' · catching up':''):mode==='starting'?'Release console buttons':mode==='error'?(play.error+' Choose separate web play or Resync.'):state.device?'Independent browser and console games':'Keyboard → browser';
 $('#separatePlay').checked=!state.device||mode==='web';$('#separatePlay').disabled=!state.device||mode==='starting';
 $('#resyncPlay').hidden=!state.device||mode==='web';$('#resyncPlay').disabled=mode==='starting';
 $('#liveDevice').disabled=mode==='console'||mode==='starting';if($('#liveDevice').disabled)$('#liveDevice').checked=true;
 if(play?.notice)$('#playModeDescription').textContent+=' '+play.notice;
}
async function connectSimulator(){
 engine=await WasmEngine.create(engineFrame,revision=>{
  if(revision===state.revision)status(validate(board()).errors.length?'Draft saved · previous valid board is playing':'Live · saved in this browser');
 },e=>{if(play?.followsConsole)play.failed(e);status(e.message,true);});
 play=new PlaySession({engine,onChange:renderPlayMode,onError:e=>toast(e.message)});renderPlayMode();
 state.ready=true;const valid=state.validBoards[state.id]||board();if(!validate(valid).errors.length)send({type:'board',board:copy(valid),revision:state.revision});publishKeys();
}
const deviceKeys=new DeviceKeyStream(mask=>state.device&&play?.controlsConsole?deviceAction('keys',{mask}):Promise.resolve(),e=>deviceLost(e));
function publishKeys(){state.mask=[...state.pressed.values()].reduce((a,b)=>a|b,0);send({type:'keys',mask:state.mask});if(state.device&&play?.controlsConsole)deviceKeys.push(state.mask);else deviceKeys.clear();}
function releaseKeys(){state.pressed.clear();engine?.release();publishKeys();}
const isForm=e=>e.target.closest?.('input,textarea,select,[contenteditable=true],#boardPicker');
window.addEventListener('keydown',e=>{
 if(isForm(e))return;
 if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='z'){e.preventDefault();restore(e.shiftKey);return;}
 if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='d'){e.preventDefault();duplicatePart();return;}
 if(e.key==='Delete'||e.key==='Backspace'){e.preventDefault();removePart();return;}
 if(e.key==='Escape'){state.selected=-1;inspector();selection();return;}
 const mask=controlsForKey(e);if(mask){e.preventDefault();state.pressed.set(e.code,mask);publishKeys();}
});
window.addEventListener('keyup',e=>{if(state.pressed.has(e.code)){state.pressed.delete(e.code);publishKeys();}});window.addEventListener('blur',releaseKeys);document.addEventListener('visibilitychange',()=>{if(document.hidden)releaseKeys();});
setInterval(()=>{if(state.mask)publishKeys();},150);
async function deviceAction(op,args={}){
 if(state.direct){if(op==='keys')return state.direct.keys(args.mask);if(op==='upload')return state.direct.upload(encode(args.board),args.revision);if(op==='boards'){const entries=await state.direct.boards();return entries.map(e=>({...e,board:decode(e.data,e.file)}));}}
 throw new Error('Connect CHGame using browser USB first.');
}
function deviceUi(connected){state.device=connected;if(!connected){deviceKeys.clear();state.lastRam=null;storage.disconnect();}$('#deviceBadge').textContent=connected?'CONNECTED':'OFFLINE';$('#deviceBadge').style.color=connected?'var(--accent)':'';$('#connectButton').firstChild.textContent=connected?'Disconnect CHGame ':'Connect CHGame ';$('#readBoards').disabled=!connected;$('#deviceStatus').textContent=connected?'Live edits change console RAM. SD auto-save and recovery are shown above the board.':'Connect CHGame to check SD versions and save your browser drafts.';renderStorage();}
function deviceLost(e){deviceUi(false);play?.disconnect(board(),state.revision).catch(()=>{});const direct=state.direct;state.direct=null;direct?.close().catch(()=>{});renderPlayMode();toast(e.message||'CHGame disconnected.');}
async function connectDevice(){try{
 if(!('serial' in navigator))throw new Error('Direct CHGame USB needs Chrome or Edge on a computer. Browser play and editing work here.');
 if(state.device){if(storage.pending().length&&!confirm('Some board edits are not verified on SD. Browser drafts will be kept. Disconnect CHGame?'))return;releaseKeys();storage.disconnect();await storage.idle();await play.disconnect(board(),state.revision);if(state.direct){await state.direct.close();state.direct=null;}deviceUi(false);renderPlayMode();return;}
 releaseKeys();state.direct=await new BrowserDevice().connect();deviceUi(true);await storage.connect(state.direct);
 const valid=state.validBoards[state.id]||board();await play.connect(state.direct,copy(valid),state.revision,!!state.separatePlay);
 if(play.controlsConsole)state.lastRam=copy(valid);else if($('#liveDevice').checked)await uploadDevice();renderStorage();renderPlayMode();
 }catch(e){toast(e.message);}}
async function uploadDevice(){
 if(!state.device||validate(board()).errors.length)return;
 if(state.uploading){state.uploadAgain=true;return;}state.uploading=true;const revision=state.revision,snapshot=copy(board());renderStorage();
 try{await deviceAction('upload',{board:snapshot,revision});state.lastRam=snapshot;}
 catch(e){deviceLost(e);}finally{state.uploading=false;renderStorage();if(state.uploadAgain||revision!==state.revision){state.uploadAgain=false;if(state.device)uploadDevice();}}
}
function storageChanged(){if(!board())return;persist();refreshLibrary();renderStorage();}
function renderStorage(){
 if(!board())return;const current=storage.view(board()),pending=storage.pending();
 const status=$('#sdStatus');if(status.textContent!==current.label)status.textContent=current.label;status.dataset.state=current.kind;status.title=current.savedAt?'Last verified on SD: '+new Date(current.savedAt).toLocaleString():'';
 $('#sdFilename').textContent=board().file+'.PBT';$('#autoSaveSd').checked=storage.auto;
 $('#browserSaveStatus').textContent=state.browserSaved?'Browser draft saved':'Browser storage failed · export your draft';
 const ramMatches=state.lastRam&&JSON.stringify(state.lastRam)===JSON.stringify(board());
 $('#ramStatus').textContent=!state.device?'Console offline':state.uploading?'Sending to RAM…':ramMatches?'Console RAM up to date':$('#liveDevice').checked?'RAM update pending':'RAM updates off';
 $('#saveSd').disabled=!(current.canSave||state.device&&current.kind==='error'&&!storage.checking);$('#saveSd').textContent=current.kind==='saving'?'Saving…':current.kind==='error'?'Retry SD save':'Save to SD now';
 $('#revertSd').disabled=!state.device||!current.revert||current.kind==='saving'||current.kind==='conflict'||storage.checking;
 $('#checkSd').disabled=!state.device||storage.checking;$('#setCheckpoint').disabled=!state.device||current.kind!=='saved';$('#resetLayout').hidden=!bases?.some(b=>b.id===board().id);
 $('#saveSummary').textContent=pending.length?pending.length+' board'+(pending.length===1?'':'s')+' not saved to SD':'All boards';
 $('#saveAllSd').disabled=!state.device||!pending.length||storage.checking;
 const failures=pending.filter(r=>r.error||r.conflict);$('#saveSummary').dataset.state=failures.length?'error':'';
 const list=$('#boardSaveList');list.replaceChildren();for(const b of state.boards){const view=storage.view(b),row=document.createElement('button'),name=document.createElement('strong'),label=document.createElement('span');row.type='button';row.setAttribute('aria-label',b.title+': '+view.label);name.textContent=b.title;label.textContent=view.label;label.dataset.state=view.kind;row.append(name,label);row.onclick=()=>{$('#saveOverview').open=false;choose(b.id);};list.append(row);}
 let warning=current.detail;if(!warning&&failures.length)warning='SD save needs attention for '+failures.map(r=>r.board.title).join(', ')+'. Open All boards to review.';
 if(current.kind==='invalid')warning='This draft is kept in the browser. Fix the board limits before RAM or SD can use it.';
 if(!state.device&&pending.length)warning='Edits are in this browser only. Connect CHGame to save them to SD.';
 if(!state.browserSaved)warning='Browser storage is unavailable. Export your draft before closing this tab.';
 $('#storageWarning').hidden=!warning;$('#storageWarningText').textContent=warning||'';
 $('#useSdVersion').hidden=current.kind!=='conflict'||!storage.sdBoard(board());$('#saveCopySd').hidden=!['conflict','error'].includes(current.kind);
}
async function saveSd(){try{if(storage.error)await storage.check();await storage.save(board());toast('Saved to SD and read back. Revert point is protected.');}catch(e){toast(e.message);}renderStorage();}
async function revertSd(){
 const original=copy(board());if(!confirm('Revert '+original.file+'.PBT to its protected SD version? Your current draft stays available in Undo.'))return;
 try{const restored=await storage.recover(original);if(state.id===original.id){remember();state.boards[state.boards.findIndex(b=>b.id===original.id)]=restored;state.selected=-1;refresh();edited(false);}toast('Reverted on SD. Undo can bring back your previous draft.');}catch(e){toast(e.message);}
}
async function useSdVersion(){
 await storage.check();const current=board(),saved=storage.sdBoard(current);if(!saved)return;
 if(!confirm('Load '+current.file+'.PBT from SD? Your browser version will be kept as a separate draft.'))return;
 const local=newIdentity(current,[...state.boards,...(storage.inventory||[]).map(e=>({file:e.file}))],(current.title+' draft').slice(0,19));
 state.boards[state.boards.findIndex(b=>b.id===current.id)]=local;
 const existing=state.boards.find(b=>b.id===saved.id);if(existing)state.boards[state.boards.indexOf(existing)]=saved;else state.boards.push(saved);
 storage.acceptSd(current);storage.acceptSd(saved);choose(saved.id);toast('Loaded SD version. Your previous draft is kept separately.');
}
async function retrieve(){const b=$('#readBoards');b.disabled=true;b.textContent='Reading…';try{
 const entries=await deviceAction('boards');let added=0;
 for(const entry of entries){let incoming=editableBoard(entry.board);const existing=state.boards.find(v=>v.id===incoming.id);
  if(existing){const before=validate(existing).errors.length?state.validBoards[existing.id]:existing,after=validate(incoming).errors.length?entry.board:incoming;if(before&&JSON.stringify(encode(before))===JSON.stringify(encode(after)))continue;incoming=newIdentity(incoming,state.boards,(incoming.title+' SD').slice(0,19));}
  else if(state.boards.some(v=>v.file===incoming.file))incoming.file=nextBoardFilename(incoming.file,state.boards);
  keepImported(entry.board,incoming);added++;
 }
 persist();refreshLibrary();toast(`Read ${entries.length} boards from CHGame. ${added} added to your library.`);
 }catch(e){toast(e.message);}finally{b.disabled=!state.device;b.textContent='↑ Get boards from console';}}
function keepImported(raw,editable){
 state.boards.push(editable);
 // A full legacy board can temporarily exceed 72 after exposing its pair.
 // Keep playing its valid source until the player removes two other parts.
 state.validBoards[editable.id]=validate(editable).errors.length?{...copy(raw),id:editable.id,file:editable.file,title:editable.title}:copy(editable);
}
async function importFile(file){
 try{let imported;if(file.name.toLowerCase().endsWith('.json')){const j=JSON.parse(await file.text());imported=Array.isArray(j)?j:[j];}else imported=[decode(new Uint8Array(await file.arrayBuffer()),file.name)];
 let added=0;
 for(const raw of imported){
  const errors=validate(raw).errors;if(errors.length)throw new Error(errors[0]);
  state.id=raw.id;
  if(state.boards.some(v=>v.id===raw.id))continue;
  const b=editableBoard(raw);
  if(state.boards.some(v=>v.file===b.file))b.file=nextBoardFilename(b.file,state.boards);
  keepImported(raw,b);added++;
 }
 choose(state.id);
 toast(added?`Imported ${added} board${added===1?'':'s'}.`:'Already in your board library.');
 }catch(e){toast(e.message);}}
$('#cloneButton').onclick=()=>create();$('#newButton').onclick=()=>create(true);$('#undoButton').onclick=()=>restore();$('#redoButton').onclick=()=>restore(true);$('#fitButton').onclick=fit;$('#zoomIn').onclick=()=>zoom(1);$('#zoomOut').onclick=()=>zoom(-1);
$('#restartButton').onclick=e=>{const seed=e.shiftKey?state.lastState?.seed:0;send({type:'restart',seed});};$('#pauseButton').onclick=()=>{const paused=!state.lastState?.paused;send({type:'pause',paused});};$('#dropButton').onclick=()=>dropBall();
$('#separatePlay').onchange=async e=>{releaseKeys();state.separatePlay=e.target.checked;persist();try{if(state.separatePlay)await play.separate(copy(state.validBoards[state.id]||board()),state.revision);else await play.start(copy(state.validBoards[state.id]||board()),state.revision);}catch(error){toast(error.message);}renderPlayMode();};
$('#resyncPlay').onclick=async()=>{releaseKeys();await play.start(copy(state.validBoards[state.id]||board()),state.revision);};
$('#connectButton').onclick=connectDevice;$('#readBoards').onclick=retrieve;$('#saveSd').onclick=saveSd;
const autoSaveDialog=$('#autoSaveDialog');
$('#autoSaveSd').onchange=e=>{
 if(!e.target.checked){storage.setAuto(false);return;}
 e.target.checked=false;
 autoSaveDialog.returnValue='';
 autoSaveDialog.showModal();
};
autoSaveDialog.addEventListener('close',()=>{
 if(autoSaveDialog.returnValue==='enable')storage.setAuto(true);
});
$('#resetLayout').onclick=()=>{const base=bases.find(b=>b.id===board().id);if(!base||!confirm('Use the current shipped layout? Your draft stays in Undo. If auto-save is on and CHGame is connected, the new layout will also be saved to SD.'))return;remember();state.boards[state.boards.findIndex(b=>b.id===state.id)]=editableBoard(copy(base));state.selected=-1;refresh();edited(false);};
$('#revertSd').onclick=revertSd;$('#checkSd').onclick=()=>storage.check();
$('#saveAllSd').onclick=()=>storage.saveAll();
$('#useSdVersion').onclick=useSdVersion;
$('#saveCopySd').onclick=()=>{const b=newIdentity(board(),[...state.boards,...(storage.inventory||[]).map(e=>({file:e.file}))]);state.boards.push(b);choose(b.id);storage.changed(b);};
$('#setCheckpoint').onclick=async()=>{if(!confirm('Use the current SD version as the new revert point? This replaces the previous revert point.'))return;try{await storage.recover(board(),true);toast('New SD revert point set.');}catch(e){toast(e.message);}};
window.addEventListener('beforeunload',e=>{if(storage.pending().length||[...storage.records.values()].some(r=>r.saving)||!state.browserSaved){e.preventDefault();e.returnValue='';}});

$('#browserUsb').hidden=true;$('#browserUsb').onclick=connectDevice;
$('#importButton').onclick=()=>$('#importFile').click();$('#importFile').onchange=e=>{if(e.target.files[0])importFile(e.target.files[0]);e.target.value='';};
$('#exportButton').onclick=e=>{try{const bytes=e.shiftKey?JSON.stringify(board(),null,2):encode(board());const url=URL.createObjectURL(new Blob([bytes],{type:e.shiftKey?'application/json':'application/octet-stream'}));const a=document.createElement('a');a.href=url;a.download=board().file+(e.shiftKey?'.json':'.PBT');a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Board exported. Shift-click Export for editable JSON.');}catch(e){toast(e.message);}};
for(const key of ['height','gravity']){
 const input=$('#'+key+'Input');
 bindNumber(input,()=>board()?.[key],(value,record)=>{
  record();board()[key]=value;
  if(key==='height'){resizeCanvas();if(state.fit)fit();}
  edited(false);
 });
}
for(const [id,key,pattern] of [['titleInput','title',/^[\x20-\x7e]{1,19}$/],['missionInput','mission',/^[\x20-\x7e]{1,23}$/],['fileInput','file',/^[A-Z0-9_]{1,8}$/]]){
 const input=$('#'+id);
 input.onfocus=()=>input._before=false;
 input.oninput=()=>{
  const value=key==='file'?input.value.toUpperCase():input.value;
  if(key==='file')input.value=value;
  if(!pattern.test(value)||value===board()[key])return;
  if(!input._before){remember();input._before=true;}
  board()[key]=value;edited(false);
 };
 input.onblur=()=>{if(board())input.value=board()[key];};
}
$('#themeSelect').onchange=e=>{remember();board().theme=Number(e.target.value);board().palette=copy(bases.find(b=>b.theme===board().theme).palette);themeStrip();paintIcons();edited(false);canvas.focus({preventScroll:true});};
$('#liveDevice').onchange=()=>{if(state.device&&$('#liveDevice').checked)uploadDevice();renderStorage();};
new ResizeObserver(()=>{if(state.fit&&board())fit();}).observe($('#boardViewport'));
try{
 const asset=async name=>{const r=await fetch(new URL('./assets/'+name,import.meta.url));if(!r.ok)throw new Error('Missing Studio asset: '+name);return r.json();};
 const [templates,art,skins]=await Promise.all([asset('boards.json'),asset('elements.json'),asset('borders.json')]);bases=copy(templates);sprites=art;borders=Object.values(skins);
 let saved;try{saved=JSON.parse(localStorage.getItem('midnight-studio-v1'));}catch{}
 state.separatePlay=!!saved?.separatePlay;
 state.boards=saved?.boards?.length&&saved.boards.every(b=>b&&Number.isInteger(b.id)&&Array.isArray(b.objects))?saved.boards:templates;state.validBoards=saved?.validBoards||{};for(const b of state.boards)if(!validate(b).errors.length)state.validBoards[b.id]=copy(b);state.boards=state.boards.map(editableBoard);for(const b of state.boards)if(!validate(b).errors.length)state.validBoards[b.id]=copy(b);state.id=state.boards.some(b=>b.id===saved?.id)?saved.id:state.boards.at(-1).id;storage=new BoardStorage({saved:saved?.storage,onChange:storageChanged});for(const b of state.boards)storage.record(b);persist();
 THEMES.forEach((name,i)=>$('#themeSelect').add(new Option(name,i)));paletteButtons();refresh();fit();await connectSimulator();
}catch(e){$('#engineLoading').textContent=e.message;status(e.message,true);}
// Read-only test/accessibility handle. All changes still use the public UI.
window.pinballStudio={get board(){return copy(board());},get status(){return {ready:state.ready,revision:state.revision,selected:state.selected,keys:state.mask,game:copy(state.lastState),device:state.device};}};
