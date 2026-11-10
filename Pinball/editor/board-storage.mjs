import {copy,decode,editableBoard,encode,validate} from './model.mjs';
const same=(a,b)=>a===null&&b===null||!!a&&!!b&&a.length===b.length&&a.every((v,i)=>v===b[i]);
export function matchesSd(board,bytes){
 if(!bytes)return false;
 try{return same(encode(board),encode(editableBoard(decode(new Uint8Array(bytes),board.file))));}catch{return false;}
}
const key=b=>`${b.id}:${b.file}`;
export class BoardStorage{
 constructor({saved={},onChange=()=>{},delay=1500}={}){
  this.records=new Map();this.saved=saved.records||{};this.auto=saved.auto!==false;
  this.onChange=onChange;this.delay=delay;this.tail=Promise.resolve();this.epoch=0;
 }
 record(board){
  const k=key(board);let r=this.records.get(k);
  if(!r){r={...this.saved[k],id:board.id,file:board.file,dirty:!!this.saved[k]?.dirty};this.records.set(k,r);
   if(this.device&&this.inventory&&!this.checking){const item=this.inventory.find(i=>i.file===board.file);r.volume=this.volume;r.expected=item?.data||null;r.checkpoint=item?.checkpoint||null;r.error=item?.error;
    if(r.expected&&!matchesSd(board,r.expected))r.conflict='This SD board differs from your browser draft. Load the SD version or save a copy.';
   }
  }
  r.board=copy(board);return r;
 }
 export(){const records={};for(const [k,r] of this.records)records[k]={id:r.id,file:r.file,dirty:r.dirty,expected:r.expected,checkpoint:r.checkpoint,volume:r.volume,savedAt:r.savedAt};return {auto:this.auto,records};}
 notify(){this.onChange();}
 select(board){this.record(board);this.notify();}
 changed(board){for(const old of this.records.values())if(old.id===board.id&&old.file!==board.file){clearTimeout(old.timer);old.dirty=false;old.obsolete=true;}
  const r=this.record(board);r.obsolete=false;r.dirty=!matchesSd(board,r.expected);if(!r.dirty){r.conflict=null;r.error=null;}this.schedule(r);this.notify();}
 pending(){return [...this.records.values()].filter(r=>r.dirty);}
 view(board){
  const r=this.record(board),invalid=validate(board).errors.length>0;
  let kind,label;
  if(r.saving){kind='saving';label='Saving to SD…';}
  else if(invalid){kind='invalid';label='Not saved · fix board limits';}
  else if(r.conflict){kind='conflict';label='SD version needs review';}
  else if(r.error||this.error){kind='error';label='SD save needs attention';}
  else if(!this.device){kind=r.dirty?'pending':'offline';label=r.dirty?'Browser draft · not saved to SD':r.expected?'Last saved to SD · offline':'SD not checked · offline';}
  else if(this.checking){kind='checking';label='Checking SD…';}
  else if(matchesSd(board,r.expected)){kind='saved';label='Saved to SD';}
  else if(r.dirty){kind='pending';label=this.auto?'Waiting to auto-save':'Changes not saved to SD';}
  else if(r.expected){kind='conflict';label='Different version on SD';}
  else{kind='new';label='Not on SD yet';}
  return {kind,label,detail:r.conflict||r.error||this.error||'',revert:!!r.checkpoint?.length,savedAt:r.savedAt,canSave:!!this.device&&!this.checking&&!invalid&&!r.conflict&&!r.saving&&!this.error};
 }
 async connect(device){this.device=device;this.epoch++;await this.check();}
 disconnect(){this.device=null;this.epoch++;this.checking=false;for(const r of this.records.values())clearTimeout(r.timer);this.notify();}
 async check(){
  if(!this.device)return;this.checking=true;this.error=null;this.notify();
  try{
   const inventory=await this.device.inspectStorage();this.volume=inventory.volume;this.inventory=inventory.items;
   for(const r of this.records.values()){
    const item=inventory.items.find(i=>i.file===r.file),actual=item?.data||null;
    const changedCard=!!r.volume&&r.volume!==inventory.volume;
    const external=r.expected!==undefined&&!same(r.expected,actual);
    r.conflict=null;r.error=item?.error||null;
    if(!r.error&&actual&&!matchesSd(r.board,actual)&&(!r.dirty||r.expected===undefined||external||changedCard))r.conflict='This SD board differs from your browser draft. Load the SD version or save a copy.';
    if(!r.error&&r.dirty&&changedCard)r.conflict='A different SD card is connected. Review its board or save a copy.';
    if(!r.error&&r.dirty&&external&&!matchesSd(r.board,actual))r.conflict='This board changed or was removed on SD. Review it before saving.';
    r.volume=inventory.volume;r.expected=actual;r.checkpoint=item?.checkpoint||null;
    if(matchesSd(r.board,actual)){r.dirty=false;r.conflict=null;}
   }
  }catch(e){this.error=e.message;}
  finally{this.checking=false;for(const r of this.records.values())this.schedule(r);this.notify();}
 }
 setAuto(on){this.auto=on;for(const r of this.records.values()){clearTimeout(r.timer);this.schedule(r);}this.notify();}
 schedule(r){
  clearTimeout(r.timer);
  if(this.auto&&this.device&&!this.checking&&!this.error&&r.dirty&&!r.conflict&&!r.error&&!r.job&&!r.saving&&!validate(r.board).errors.length){r.timer=setTimeout(()=>this.save(r.board).catch(()=>{}),this.delay);}
 }
 async save(board){
  const r=this.record(board);clearTimeout(r.timer);
  if(r.job){await r.job;if(r.dirty)return this.save(r.board);return;}
  if(!this.device||this.checking||this.error)throw new Error(this.error||'Connect CHGame and check the SD card first.');
  if(r.conflict)throw new Error(r.conflict);
  const errors=validate(board).errors;if(errors.length)throw new Error(errors[0]);
  if(r.volume!==this.volume||r.expected===undefined){await this.check();if(r.conflict||this.error)throw new Error(r.conflict||this.error);}
  r.error=null;r.saving=true;this.notify();const epoch=this.epoch,device=this.device;
  const job=this.tail.then(async()=>{
   if(epoch!==this.epoch)throw new Error('CHGame disconnected before saving.');if(r.obsolete)return;
   const snapshot=copy(r.board),result=await device.save(snapshot.file,encode(snapshot),{volume:r.volume,expected:r.expected});
   r.expected=result.data;r.checkpoint=result.checkpoint;r.volume=result.volume;r.savedAt=Date.now();r.dirty=!matchesSd(r.board,result.data);
   this.inventory=this.inventory.filter(i=>i.file!==r.file).concat({file:r.file,data:result.data,checkpoint:result.checkpoint});
  }).catch(e=>{r.error=e.message;if(['conflict','card_changed'].includes(e.code))r.conflict=e.message;throw e;})
   .finally(()=>{r.saving=false;r.job=null;this.schedule(r);this.notify();});
  r.job=job;this.tail=job.catch(()=>{});return job;
 }
 async saveAll(){for(const r of this.pending()){try{await this.save(r.board);}catch{}}}
 async idle(){await this.tail;}
 async recover(board,checkpoint=false){
  const r=this.record(board);clearTimeout(r.timer);if(r.job)await r.job;
  if(!this.device||r.conflict||this.error)throw new Error(r.conflict||this.error||'Connect CHGame first.');
  const options={volume:r.volume,expected:r.expected};r.saving=true;this.notify();
  const device=this.device,epoch=this.epoch;
  const task=this.tail.then(()=>{if(this.epoch!==epoch)throw new Error('CHGame disconnected.');return checkpoint?device.checkpointSd(r.file,options):device.revertSd(r.file,options);});this.tail=task.catch(()=>{});
  try{const result=await task;r.expected=result.data;r.checkpoint=result.checkpoint;r.savedAt=Date.now();r.error=null;r.dirty=!matchesSd(r.board,result.data);
   this.inventory=this.inventory.filter(i=>i.file!==r.file).concat({file:r.file,data:result.data,checkpoint:result.checkpoint});return editableBoard(decode(new Uint8Array(result.data),r.file));}
  catch(e){r.error=e.message;if(['conflict','card_changed'].includes(e.code))r.conflict=e.message;throw e;}
  finally{r.saving=false;this.schedule(r);this.notify();}
 }
 sdBoard(board){const r=this.record(board);return r.expected?editableBoard(decode(new Uint8Array(r.expected),r.file)):null;}
 acceptSd(board){const r=this.record(board);r.conflict=null;r.error=null;r.dirty=false;this.notify();}
}
