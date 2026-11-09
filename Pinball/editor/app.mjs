import {BoardPicker} from './board-picker.mjs';
import {DeviceKeyStream} from './key-stream.mjs';
import {CATALOG,THEMES,copy,createPart,validate,encode,decode,newIdentity,controlsForKey,pick,handles,rampPoint} from './model.mjs';
import {BrowserDevice} from './serial.mjs';
import {drawPartPreview} from './part-drag.mjs';
import {WasmEngine} from './wasm-engine.mjs';
const $=s=>document.querySelector(s),NS='http://www.w3.org/2000/svg',HEADER_HEIGHT=24;
const state={boards:[],validBoards:{},id:null,selected:-1,undo:[],redo:[],revision:0,zoom:1.5,fit:true,mask:0,pressed:new Map(),device:false,direct:null,uploading:false,lastState:null,lastFrame:null,drag:null,ready:false};
const board=()=>state.boards.find(b=>b.id===state.id);
let engine,deviceTimer,toastTimer,sprites,bases,borders;
const boardPicker=new BoardPicker($('#boardPicker'),id=>{choose(id);canvas.focus({preventScroll:true});},releaseKeys);
function toast(text){$('#toast').textContent=text;$('#toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('show'),4200);}
function status(text,error=false){$('#syncStatus').textContent=text;$('#syncStatus').classList.toggle('error',error);}
function persist(){try{localStorage.setItem('midnight-studio-v1',JSON.stringify({boards:state.boards,validBoards:state.validBoards,id:state.id}));}catch{toast('Browser storage is full. Export your board to keep it.');}}
function remember(){state.undo.push(copy(board()));if(state.undo.length>80)state.undo.shift();state.redo=[];historyButtons();}
function historyButtons(){$('#undoButton').disabled=!state.undo.length;$('#redoButton').disabled=!state.redo.length;}
function restore(redo=false){const source=redo?state.redo:state.undo,target=redo?state.undo:state.redo;if(!source.length)return;target.push(copy(board()));state.boards[state.boards.findIndex(b=>b.id===state.id)]=source.pop();state.selected=-1;refresh();edited(false);}
function send(data){engine?.send(data);}
function edited(snapshot=true){
 if(snapshot)remember();state.revision++;refreshLibrary();$('#boardHeading').textContent=board().title;$('#elementCount').textContent=`${board().objects.length} / 72 elements`;
 const result=validate(board());if(!result.errors.length)state.validBoards[state.id]=copy(board());persist();showValidation(result);selection();
 clearTimeout(deviceTimer);
 if(result.errors.length){status('Fix the highlighted limits · previous valid board is still playing',true);return;}
 status('Applying live edit…');send({type:'board',board:copy(board()),revision:state.revision});
 if(state.device&&$('#liveDevice').checked)deviceTimer=setTimeout(()=>uploadDevice(),180);
}
function showValidation({errors,warnings}){const box=$('#validation');box.replaceChildren();for(const text of [...errors,...warnings]){const p=document.createElement('p');p.textContent=(errors.includes(text)?'! ':'↳ ')+text;if(errors.includes(text))p.className='error';box.append(p);}}
function refreshLibrary(){boardPicker.update(state.boards,state.id,borders);$('#boardCount').textContent=state.boards.length;}
function choose(id){releaseKeys();state.id=Number(id);state.selected=-1;state.undo=[];state.redo=[];state.lastFrame=null;refresh();edited(false);fit();}
function refresh(){
 refreshLibrary();historyButtons();const b=board();$('#boardHeading').textContent=b.title;
 for(const [selector,key] of [['#titleInput','title'],['#missionInput','mission'],['#heightInput','height'],['#gravityInput','gravity'],['#fileInput','file'],['#themeSelect','theme']])$(selector).value=b[key];
 $('#elementCount').textContent=`${b.objects.length} / 72 elements`;themeStrip();inspector();showValidation(validate(b));resizeCanvas();selection();paintIcons();
}
function themeStrip(){const strip=$('#themeStrip');strip.replaceChildren();board().palette.slice(0,15).forEach(c=>{const s=document.createElement('span');s.style.background='#'+c;strip.append(s);});}
function resizeCanvas(){const c=$('#boardCanvas'),height=Number.isInteger(board().height)&&board().height>=256&&board().height<=480?board().height:(state.validBoards[state.id]?.height||384);if(c.height!==height){c.height=height;$('#selection').setAttribute('viewBox',`0 0 128 ${height}`);}c.style.width=128*state.zoom+'px';c.style.height=height*state.zoom+'px';$('#headerCanvas').style.width=128*state.zoom+'px';$('#headerCanvas').style.height=HEADER_HEIGHT*state.zoom+'px';$('#fitButton').textContent=state.fit?'Fit':Math.round(state.zoom*100)+'%';}
function fit(){state.fit=true;const box=$('#boardViewport').getBoundingClientRect();state.zoom=Math.min(3.5,Math.max(.65,Math.min((box.height-65)/(canvas.height+HEADER_HEIGHT),(box.width-100)/128)));resizeCanvas();}
function zoom(direction){state.fit=false;state.zoom=Math.max(.65,Math.min(5,state.zoom+direction*.35));resizeCanvas();}
function field(label,key,o,options){const container=document.createElement('div');container.className='field';const l=document.createElement('label'),input=document.createElement(options?'select':'input');input.id='prop-'+key;l.htmlFor=input.id;l.textContent=label;if(options)options.forEach((text,i)=>input.add(new Option(text,i)));else{input.type='number';input.step=1;}input.value=o[key];input.dataset.property=key;input.addEventListener('focus',()=>{input._before=false;});input.addEventListener('input',()=>{if(!input._before){remember();input._before=true;}board().objects[state.selected][key]=Number(input.value);edited(false);});container.append(l,input);return container;}
function inspector(){
 const box=$('#inspector'),o=board().objects[state.selected];box.replaceChildren();
 if(!o){const title=document.createElement('div');title.className='section-title';title.textContent='MAKE IT YOURS';const p=document.createElement('p');p.className='description';p.textContent='Click any part to tune it. Drag to move. The ball keeps going.';box.append(title,p);return;}
 const definition=CATALOG.find(c=>c.kind===o.kind),title=document.createElement('div'),p=document.createElement('p');title.className='section-title';title.textContent=definition.name.toUpperCase();p.className='description';p.textContent=definition.description;box.append(title,p);
 const row=document.createElement('div');row.className='field-row';row.append(field('X','x',o),field('Y','y',o));box.append(row);
 const names={wall:['End X','End Y'],gate:['End X','End Y'],ramp:['Exit X','Exit Y'],flippers:['Right pivot X','Bat length'],target:['Width','Height'],drop_target:['Width','Height'],spinner:['Half-width','Kick'],scoop:['Radius','Kick'],saucer:['Radius','Hold / kick'],kickback:['Radius','Kick'],bumper:['Radius','Kick'],lane:['Radius','Kick']}[o.kind];
 const dimensions=document.createElement('div');dimensions.className='field-row';if(o.kind!=='spinner')dimensions.append(field(names[0],'u',o));if(['wall','gate','ramp','flippers','target','drop_target','bumper'].includes(o.kind))dimensions.append(field(names[1],'v',o));box.append(dimensions);if(!['wall','flippers','spinner','kickback'].includes(o.kind))box.append(field(o.kind==='ramp'?'Curve':o.kind==='gate'?'Gate rule':'Color bank','group',o,o.kind==='ramp'?['Left side','Right side','Center']:o.kind==='gate'?['Pass toward upper side','Pass toward lower side','Unlock with all target banks']:['Cyan','Pink','Gold']));if(!['wall','gate','flippers'].includes(o.kind))box.append(field('Points','value',o));
 const actions=document.createElement('div');actions.className='selection-actions';const duplicate=document.createElement('button'),remove=document.createElement('button');duplicate.textContent='⧉ Duplicate';duplicate.onclick=duplicatePart;remove.textContent='Remove';remove.className='delete';remove.onclick=removePart;actions.append(duplicate,remove);box.append(actions);
}
function refreshCoordinates(){const o=board().objects[state.selected];if(!o)return;for(const k of ['x','y','u','v']){const input=$('#prop-'+k);if(input&&document.activeElement!==input)input.value=o[k];}}
function selection(){
 const svg=$('#selection');svg.replaceChildren();const o=board().objects[state.selected];if(!o)return;
 const shape=document.createElementNS(NS,'path');shape.setAttribute('class','selection-outline');
 if(o.kind==='ramp'){let d='M '+o.x+' '+o.y;for(let i=1;i<=16;i++){const p=rampPoint(o,i/16);d+=` L ${p.x} ${p.y}`;}shape.setAttribute('d',d);shape.setAttribute('fill','none');shape.style.strokeWidth=1;svg.append(shape);}
 else if(['wall','gate'].includes(o.kind)){shape.setAttribute('d',`M ${o.x} ${o.y} L ${o.u} ${o.v}`);shape.style.strokeWidth=8;svg.append(shape);}
 else{const rect=document.createElementNS(NS,'rect');const fl=o.kind==='flippers',r=fl?6:Math.max(6,o.u)+3;rect.setAttribute('x',o.x-r);rect.setAttribute('y',o.y-r);rect.setAttribute('width',fl?o.u-o.x+r*2:r*2);rect.setAttribute('height',fl?25:r*2);rect.setAttribute('rx','3');rect.setAttribute('class','selection-outline');svg.append(rect);}
 for(const p of handles(o)){const c=document.createElementNS(NS,'circle');c.setAttribute('cx',p.x);c.setAttribute('cy',p.y);c.setAttribute('r','2.4');c.setAttribute('class','selection-handle');svg.append(c);}
}
function point(event){const rect=$('#boardCanvas').getBoundingClientRect();return {x:Math.round((event.clientX-rect.left)*128/rect.width),y:Math.round((event.clientY-rect.top)*board().height/rect.height)};}
function dropPoint(){const viewport=$('#boardViewport'),canvas=$('#boardCanvas').getBoundingClientRect(),area=viewport.getBoundingClientRect();return {x:64,y:Math.max(15,Math.min(board().height-65,Math.round((area.top+area.height*.4-canvas.top)/state.zoom)))};}
function add(kind,p=dropPoint()){
 if(board().objects.length>=72)return toast('This board already has 72 elements.');const o=createPart(kind,p,board().height);
 remember();board().objects.push(o);state.selected=board().objects.length-1;inspector();edited(false);$('#boardCanvas').focus({preventScroll:true});
}
function removePart(){if(state.selected<0)return;remember();board().objects.splice(state.selected,1);state.selected=-1;inspector();edited(false);}
function duplicatePart(){if(state.selected<0||board().objects.length>=72)return;remember();const o=copy(board().objects[state.selected]);o.x+=6;o.y+=8;if(['wall','gate','ramp'].includes(o.kind)){o.u+=6;o.v+=8;}if(o.kind==='flippers'){o.x-=6;}board().objects.push(o);state.selected=board().objects.length-1;inspector();edited(false);}
function create(blank=false){const b=newIdentity(board(),state.boards,blank?'Untitled board':'');if(blank){b.objects=[];b.mission='BUILD YOUR OWN RUN';}state.boards.push(b);choose(b.id);toast(blank?'A blank board, ready to build.':'Cloned with its own board ID and high score.');}
const canvas=$('#boardCanvas');
canvas.addEventListener('pointerdown',e=>{
 if(e.button!==0)return;canvas.focus({preventScroll:true});const p=point(e);if(e.altKey){dropBall(p);return;}
 let handle=handles(board().objects[state.selected]).find(h=>Math.hypot(h.x-p.x,h.y-p.y)<=4);
 if(!handle)state.selected=pick(board(),p.x,p.y);
 inspector();selection();if(state.selected<0)return;
 state.drag={start:p,original:copy(board().objects[state.selected]),handle:handle?.key};canvas.setPointerCapture(e.pointerId);e.preventDefault();
});
canvas.addEventListener('pointermove',e=>{
 const p=point(e);$('#cursorPosition').textContent=`x ${p.x}  ·  y ${p.y}`;
 if(!state.drag)return;
 const d=state.drag,o=copy(d.original),dx=p.x-d.start.x,dy=p.y-d.start.y;
 if(d.handle==='end'){o.u+=dx;o.v+=dy;}
 else if(d.handle==='start'){o.x+=dx;o.y+=dy;}
 else{o.x+=dx;o.y+=dy;if(['wall','ramp','gate'].includes(o.kind)){o.u+=dx;o.v+=dy;}else if(o.kind==='flippers')o.u+=dx;}
 const candidate=copy(board());candidate.objects[state.selected]=o;if(validate(candidate).errors.length)return;
 if(!state.drag.moved)remember();board().objects[state.selected]=o;state.drag.moved=true;refreshCoordinates();edited(false);
});
function endDrag(){state.drag=null;}
canvas.addEventListener('pointerup',endDrag);canvas.addEventListener('pointercancel',endDrag);canvas.addEventListener('lostpointercapture',endDrag);
canvas.addEventListener('dblclick',e=>{const p=point(e);if(pick(board(),p.x,p.y)<0)dropBall(p);});
function dropBall(p=dropPoint()){const x=Math.max(10,Math.min(108,p.x)),y=Math.max(12,Math.min(board().height-20,p.y));send({type:'place',x,y});if(state.device)deviceAction('place',{x,y}).catch(e=>toast(e.message));}
function paintIcons(){if(!sprites||!board())return;const inks={'.':-1,'0':2,w:1,m:3,t:4,d:7,i:5,c:4,o:9,g:10,b:12,p:13,s:14,r:6};
 for(const def of CATALOG){const c=document.querySelector(`[data-part="${def.kind}"] canvas`),ctx=c.getContext('2d'),frame=sprites[def.sprite]?.[0];ctx.clearRect(0,0,c.width,c.height);
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
function image(bytes,width,height){
 const pixels=bytes.subarray(0,width*height/2),palette=new DataView(bytes.buffer,bytes.byteOffset+width*height/2,32),colors=[];
 for(let i=0;i<16;i++){let v=palette.getUint16(i*2,true);colors.push([((v>>12)&15)*17,((v>>7)&15)*17,((v>>1)&15)*17,255]);}
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
function engineFrame(game,bytes){
 if((game.id>>>0)!==(board().id>>>0)||game.height!==canvas.height)return;
 const full=image(bytes,128,game.height+HEADER_HEIGHT);$('#headerCanvas').getContext('2d').putImageData(full,0,0);canvas.getContext('2d').putImageData(full,0,-HEADER_HEIGHT);
 state.lastState=game;const pauseLabel=game.paused?'▶ Resume':'Ⅱ Pause';if($('#pauseButton').textContent!==pauseLabel)$('#pauseButton').textContent=pauseLabel;
 $('#playScore').textContent=game.score.toLocaleString();$('#playBall').textContent=game.over?'GAME OVER':`${game.lives} BALL${game.lives===1?'':'S'} · ×${game.effective_mult}`;
 const mission=$('#laneMission');mission.hidden=game.lane_groups!==7;
 if(!mission.hidden){
  const missing=[];mission.dataset.pulse=String(Boolean(game.ticks&16));
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
}
async function connectSimulator(){
 engine=await WasmEngine.create(engineFrame,revision=>{
  if(revision===state.revision)status(validate(board()).errors.length?'Draft saved · previous valid board is playing':'Live · saved in this browser');
 },e=>status(e.message,true));
 state.ready=true;const valid=state.validBoards[state.id]||board();if(!validate(valid).errors.length)send({type:'board',board:copy(valid),revision:state.revision});publishKeys();
}
const deviceKeys=new DeviceKeyStream(mask=>state.device?deviceAction('keys',{mask}):Promise.resolve(),e=>deviceLost(e));
function publishKeys(){state.mask=[...state.pressed.values()].reduce((a,b)=>a|b,0);send({type:'keys',mask:state.mask});if(state.device)deviceKeys.push(state.mask);else deviceKeys.clear();}
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
 if(state.direct){if(op==='keys')return state.direct.keys(args.mask);if(op==='restart')return state.direct.restart(args.seed||0);if(op==='pause')return state.direct.pause(args.paused);if(op==='place')return state.direct.place(args.x,args.y);if(op==='upload')return state.direct.upload(encode(args.board));if(op==='boards'){const entries=await state.direct.boards();return entries.map(e=>({...e,board:decode(e.data,e.file)}));}}
 throw new Error('Connect CHGame using browser USB first.');
}
function deviceUi(connected){state.device=connected;if(!connected)deviceKeys.clear();$('#deviceBadge').textContent=connected?'CONNECTED':'OFFLINE';$('#deviceBadge').style.color=connected?'var(--accent)':'';$('#connectButton').firstChild.textContent=connected?'Disconnect CHGame ':'Connect CHGame ';$('#readBoards').disabled=$('#saveSd').disabled=!connected;$('#deviceStatus').textContent=connected?'Edits go straight to RAM. Save to SD to keep them after power-off.':'Connect over USB to try edits on the handheld.';}
function deviceLost(e){deviceUi(false);const direct=state.direct;state.direct=null;direct?.close().catch(()=>{});toast(e.message||'CHGame disconnected.');}
async function connectDevice(){try{
 if(!('serial' in navigator))throw new Error('Direct CHGame USB needs Chrome or Edge on a computer. Browser play and editing work here.');
 if(state.device){if(state.direct){await state.direct.close();state.direct=null;}deviceUi(false);return;}
 state.direct=await new BrowserDevice().connect();deviceUi(true);await uploadDevice();toast('CHGame connected. This board is playing on both screens.');
 }catch(e){toast(e.message);}}
async function uploadDevice(){
 if(!state.device||validate(board()).errors.length)return;
 if(state.uploading){state.uploadAgain=true;return;}state.uploading=true;const revision=state.revision;
 try{const result=await deviceAction('upload',{board:copy(board())});$('#deviceStatus').textContent=`Live on CHGame · ${result.bytes} bytes verified in RAM`;}
 catch(e){deviceLost(e);}finally{state.uploading=false;if(state.uploadAgain||revision!==state.revision){state.uploadAgain=false;if(state.device)uploadDevice();}}
}
async function saveSd(){
 if(validate(board()).errors.length)return toast('Fix the board limits before saving.');const button=$('#saveSd');button.disabled=true;button.textContent='Saving…';
 try{const result=await state.direct.save(board().file,encode(board()));$('#deviceStatus').textContent=`${result.path} · saved and read back`;toast('Saved to SD and verified. Ready for the next power-on.');}
 catch(e){toast(e.message);}finally{button.disabled=!state.device;button.textContent='Save to SD';}}
async function retrieve(){const b=$('#readBoards');b.disabled=true;b.textContent='Reading…';try{
 const entries=await deviceAction('boards');let added=0;
 for(const entry of entries){const incoming=entry.board,existing=state.boards.find(v=>v.id===incoming.id);if(existing){if(JSON.stringify(encode(existing))===JSON.stringify(encode(incoming)))continue;const duplicate=newIdentity(incoming,state.boards,(incoming.title+' SD').slice(0,19));state.boards.push(duplicate);}else{if(state.boards.some(v=>v.file===incoming.file))incoming.file=newIdentity(incoming,state.boards).file;state.boards.push(incoming);}added++;}
 persist();refreshLibrary();toast(`Read ${entries.length} boards from CHGame. ${added} added to your library.`);
 }catch(e){toast(e.message);}finally{b.disabled=!state.device;b.textContent='↓ Get boards';}}
async function importFile(file){
 try{let imported;if(file.name.toLowerCase().endsWith('.json')){const j=JSON.parse(await file.text());imported=Array.isArray(j)?j:[j];}else imported=[decode(new Uint8Array(await file.arrayBuffer()),file.name)];
 for(let b of imported){const errors=validate(b).errors;if(errors.length)throw new Error(errors[0]);if(state.boards.some(v=>v.id===b.id||v.file===b.file))b=newIdentity(b,state.boards,b.title);state.boards.push(b);state.id=b.id;}
 choose(state.id);toast(`Imported ${imported.length} board${imported.length===1?'':'s'}.`);
 }catch(e){toast(e.message);}}
$('#cloneButton').onclick=()=>create();$('#newButton').onclick=()=>create(true);$('#undoButton').onclick=()=>restore();$('#redoButton').onclick=()=>restore(true);$('#fitButton').onclick=fit;$('#zoomIn').onclick=()=>zoom(1);$('#zoomOut').onclick=()=>zoom(-1);
$('#restartButton').onclick=e=>{const seed=e.shiftKey?state.lastState?.seed:0;send({type:'restart',seed});if(state.device)deviceAction('restart',{seed}).catch(e=>toast(e.message));};$('#pauseButton').onclick=()=>{const paused=!state.lastState?.paused;send({type:'pause'});$('#pauseButton').textContent=paused?'▶ Resume':'Ⅱ Pause';if(state.device)deviceAction('pause',{paused}).catch(e=>toast(e.message));};$('#dropButton').onclick=()=>dropBall();
$('#connectButton').onclick=connectDevice;$('#readBoards').onclick=retrieve;$('#saveSd').onclick=saveSd;
$('#browserUsb').hidden=true;$('#browserUsb').onclick=async()=>{try{if(state.device)await connectDevice();state.direct=await new BrowserDevice().connect();deviceUi(true);await uploadDevice();toast('Connected directly through Web Serial.');}catch(e){state.direct=null;deviceLost(e);}};
$('#importButton').onclick=()=>$('#importFile').click();$('#importFile').onchange=e=>{if(e.target.files[0])importFile(e.target.files[0]);e.target.value='';};
$('#exportButton').onclick=e=>{try{const bytes=e.shiftKey?JSON.stringify(board(),null,2):encode(board());const url=URL.createObjectURL(new Blob([bytes],{type:e.shiftKey?'application/json':'application/octet-stream'}));const a=document.createElement('a');a.href=url;a.download=board().file+(e.shiftKey?'.json':'.PBT');a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Board exported. Shift-click Export for editable JSON.');}catch(e){toast(e.message);}};
for(const [id,key]of [['titleInput','title'],['missionInput','mission'],['heightInput','height'],['gravityInput','gravity'],['fileInput','file']]){const input=$('#'+id);input.onfocus=()=>input._before=false;input.oninput=()=>{if(!input._before){remember();input._before=true;}board()[key]=['height','gravity'].includes(key)?Number(input.value):key==='file'?input.value.toUpperCase():input.value;if(key==='file')input.value=board().file;if(key==='height'){resizeCanvas();if(state.fit)fit();}edited(false);};}
$('#themeSelect').onchange=e=>{remember();board().theme=Number(e.target.value);board().palette=copy(bases.find(b=>b.theme===board().theme).palette);themeStrip();paintIcons();edited(false);canvas.focus({preventScroll:true});};
$('#liveDevice').onchange=()=>{if(state.device&&$('#liveDevice').checked)uploadDevice();};
window.addEventListener('resize',()=>{if(state.fit&&board())fit();});
try{
 const asset=async name=>{const r=await fetch(new URL('./assets/'+name,import.meta.url));if(!r.ok)throw new Error('Missing Studio asset: '+name);return r.json();};
 const [templates,art,skins]=await Promise.all([asset('boards.json'),asset('elements.json'),asset('borders.json')]);bases=copy(templates);sprites=art;borders=Object.values(skins);
 let saved;try{saved=JSON.parse(localStorage.getItem('midnight-studio-v1'));}catch{}
 state.boards=saved?.boards?.length&&saved.boards.every(b=>b&&Number.isInteger(b.id)&&Array.isArray(b.objects))?saved.boards:templates;state.validBoards=saved?.validBoards||{};for(const b of state.boards)if(!validate(b).errors.length)state.validBoards[b.id]=copy(b);state.id=state.boards.some(b=>b.id===saved?.id)?saved.id:state.boards.at(-1).id;
 THEMES.forEach((name,i)=>$('#themeSelect').add(new Option(name,i)));paletteButtons();refresh();fit();await connectSimulator();
}catch(e){$('#engineLoading').textContent=e.message;status(e.message,true);}
// Read-only test/accessibility handle. All changes still use the public UI.
window.pinballStudio={get board(){return copy(board());},get status(){return {ready:state.ready,revision:state.revision,selected:state.selected,keys:state.mask,game:copy(state.lastState),device:state.device};}};
