// The picker uses the same editable 12x8 crest and palette indices as CHGame.
const INK={'0':2,w:1,m:3,t:4,d:7,i:5,c:8,o:9,g:10,b:12,p:13,s:14,r:6};
const ACCENTS=[4,4,14,10,10,13,8,11,10];
export function emblemPixels(board,art){
 const skin=art[board.theme]||art[0];
 return skin.emblem.map(row=>[...row].map(ink=>ink==='.'?0:ink==='c'?ACCENTS[board.theme]??4:INK[ink]));
}
export function paintEmblem(canvas,board,art){
 canvas.width=48;canvas.height=32;
 const ctx=canvas.getContext('2d'),palette=board.palette.slice();
 palette[2]=((parseInt(palette[0],16)>>1)&0x777).toString(16).padStart(3,'0');
 emblemPixels(board,art).forEach((row,y)=>row.forEach((ink,x)=>{ctx.fillStyle='#'+palette[ink];ctx.fillRect(x*4,y*4,4,4);}));
}
export class BoardPicker{
 constructor(root,onChoose,onOpen){
  this.root=root;this.trigger=root.querySelector('summary');this.menu=root.querySelector('[role=listbox]');
  this.onChoose=onChoose;this.onOpen=onOpen;
  root.addEventListener('toggle',()=>{this.trigger.setAttribute('aria-expanded',String(root.open));if(root.open){this.position();onOpen();}});
  root.addEventListener('keydown',event=>{
   const rows=[...this.menu.querySelectorAll('[role=option]')],index=rows.indexOf(document.activeElement);
   if(event.key==='Escape'&&root.open){event.preventDefault();root.open=false;this.trigger.focus();}
   else if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){
    event.preventDefault();root.open=true;this.position();
    const current=index<0?rows.findIndex(row=>row.getAttribute('aria-selected')==='true'):index;
    const next=event.key==='Home'?0:event.key==='End'?rows.length-1:index<0?Math.max(0,current):(current+(event.key==='ArrowDown'?1:-1)+rows.length)%rows.length;
    rows[next]?.focus();rows[next]?.scrollIntoView({block:'nearest'});
   }
   // Menu navigation never operates the game's flippers or shake controls.
   event.stopPropagation();
  });
  document.addEventListener('pointerdown',event=>{if(!root.contains(event.target))root.open=false;});
  // Safari does not focus buttons on pointer clicks; a null relatedTarget
  // must not close the popup before the option's click arrives.
  root.addEventListener('focusout',event=>{if(event.relatedTarget&&!root.contains(event.relatedTarget))root.open=false;});
  window.addEventListener('resize',()=>{if(root.open)this.position();});
 }
 position(){
  const r=this.trigger.getBoundingClientRect(),width=Math.min(300,innerWidth-16);
  this.menu.style.width=width+'px';this.menu.style.left=Math.min(r.left,innerWidth-width-8)+'px';
  this.menu.style.top=(r.bottom+6)+'px';this.menu.style.maxHeight=Math.max(80,Math.min(560,innerHeight-r.bottom-18))+'px';
 }
 update(boards,id,art,stateFor){
  this.menu.replaceChildren();
  const active=boards.find(board=>board.id===id);
  if(!active)return;
  this.trigger.querySelector('.board-picker-title').textContent=active.title;
  this.trigger.setAttribute('aria-label','Choose a board: '+active.title);
  paintEmblem(this.trigger.querySelector('canvas'),active,art);
  for(const board of boards){
   const row=document.createElement('button'),icon=document.createElement('canvas'),label=document.createElement('span');
   row.type='button';row.className='board-option';row.setAttribute('role','option');row.setAttribute('aria-selected',String(board.id===id));row.dataset.boardId=board.id;
   icon.setAttribute('aria-hidden','true');label.textContent=board.title;paintEmblem(icon,board,art);
   if(stateFor){const saved=stateFor(board),note=document.createElement('small');note.className='board-save-note';note.textContent=saved.label;note.dataset.state=saved.kind;label.append(note);}
   row.append(icon,label);row.onclick=()=>{this.root.open=false;this.onChoose(board.id);};this.menu.append(row);
  }
  if(this.root.open)this.position();
 }
}
