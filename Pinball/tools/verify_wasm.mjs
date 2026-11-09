// Replay the same edits and inputs through native C++ and WASM. Compare bytes,
// including every state field, PBT readback and full-board rendered pixels.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {encode,copy,rampPoint,editableBoard} from '../editor/model.mjs';
import {readState,STATE_FIELDS} from '../editor/wasm-engine.mjs';
const [dist,native]=process.argv.slice(2);
const {default:create}=await import(pathToFileURL(path.resolve(dist,'engine.mjs')));
const wasm=fs.readdirSync(dist).find(name=>name.endsWith('.wasm'));
const m=await create({wasmBinary:fs.readFileSync(path.join(dist,wasm))});m._pb_init();
assert.equal(m._pb_state_count(),STATE_FIELDS.length);
const boards=JSON.parse(fs.readFileSync(path.join(dist,'assets/boards.json')));
const inputs=[],outputs=[];let snapshots=0,steps=0,edits=0;
const u32=n=>{const b=Buffer.alloc(4);b.writeUInt32LE(n>>>0);return b;};
const physics=JSON.parse(fs.readFileSync(path.join(dist,'assets/physics.json')));
const physicsKeys=['spin_grip','spin_forget','scatter_passive','scatter_powered','scatter_eject'];
const configPtr=m._pb_physics(),compiledPhysics=Array.from(m.HEAP32.slice(configPtr>>2,(configPtr>>2)+5));
assert.deepEqual(compiledPhysics,physicsKeys.map(k=>physics[k]),'compiled WASM physics must match the shared build settings');
inputs.push(Buffer.from('C'));outputs.push(Buffer.from(m.HEAPU8.slice(configPtr,configPtr+20)));
console.log('Compiled physics:',JSON.stringify(physics));
function load(b,corrupt=false){
 const bytes=encode(b);if(corrupt)bytes[bytes.length-1]^=1;
 inputs.push(Buffer.from('L'),u32(bytes.length),bytes);m.HEAPU8.set(bytes,m._pb_input());
 const ok=m._pb_apply(bytes.length);outputs.push(u32(ok));assert.equal(ok,Number(!corrupt));edits++;
 if(ok){
  // Palette changes must be visible even before a physics tick is due.
  const pixels=m._pb_render(),size=m._pb_render_size(),palette=new DataView(m.HEAPU8.buffer,pixels+size-32,32);
  for(let i=0;i<16;i++){
   const c=palette.getUint16(i*2,true),rgb=((c>>12)<<8)|(((c>>7)&15)<<4)|((c>>1)&15);
   const expected=i===2?(parseInt(b.palette[0],16)>>1)&0x777:parseInt(b.palette[i],16);
   assert.equal(rgb,expected,`immediate theme palette ${i}`);
  }
  snapshot();
 }
}
function step(mask=0){inputs.push(Buffer.from('S'),u32(mask));m._pb_step(mask);steps++;}
function place(x,y,vx=0,vy=0){inputs.push(Buffer.from('J'),...[x,y,vx,vy].map(u32));outputs.push(u32(m._pb_place(x,y,vx,vy)));}
function command(op,value=0){inputs.push(Buffer.from(op));if(op==='Q'){inputs.push(u32(value));m._pb_pause(value);}else{inputs.push(u32(value));m._pb_restart(value);}}
function snapshot(){
 inputs.push(Buffer.from('G'));const at=m._pb_state();outputs.push(Buffer.from(m.HEAPU8.slice(at,at+STATE_FIELDS.length*4)));
 const before=readState(m),p=m._pb_render(),n=m._pb_render_size();outputs.push(u32(n),Buffer.from(m.HEAPU8.slice(p,p+n)));assert.deepEqual(readState(m),before,'overview must not mutate game state');
 const lcd=m._pb_lcd(),lcdSize=m._pb_lcd_size();outputs.push(u32(lcdSize),Buffer.from(m.HEAPU8.slice(lcd,lcd+lcdSize)));
 const t=m._pb_table(),size=m._pb_table_size();outputs.push(u32(size),Buffer.from(m.HEAPU8.slice(t,t+size)));snapshots++;
}
function lcdSnapshot(){
 inputs.push(Buffer.from('H'));const at=m._pb_lcd(),n=m._pb_lcd_size(),image=m.HEAPU8.slice(at,at+n);
 outputs.push(u32(n),Buffer.from(image));return image;
}
for(const [i,base] of boards.entries()){
 const b=copy(base);load(b);step();snapshot();
 step(8);step(); // fixed launch release
 for(let f=0;f<240;f++){step((f%37<8?16:0)|(f%47<8?2:0));if(f%30===0)snapshot();}
 place(60,b.height-100,70,150);step();
 const before=readState(m);b.objects[0].x+=1;load(b);const after=readState(m);
 for(const k of ['xq','yq','vx','vy','score','lives','ticks'])assert.equal(after[k],before[k],`live move preserves ${k}`);
 step(18);snapshot();assert.equal(readState(m).left>0,true);assert.equal(readState(m).right>0,true);
 b.objects.splice(0,1);load(b);step();snapshot(); // delete while playing
 load(base);step(); // undo geometry, not the gameplay timeline
 b.theme=(i+1)%9;b.palette=copy(boards[b.theme].palette);load(b);step();snapshot();
 const valid=readState(m);load(b,true);assert.deepEqual(readState(m),valid,'invalid edits are atomic');snapshot();
 command('Q',1);const frozen=readState(m);for(let f=0;f<12;f++)step(18);assert.equal(readState(m).ticks,frozen.ticks);assert.equal(readState(m).rng,frozen.rng,'pause freezes RNG');snapshot();command('Q',0);
 for(const o of b.objects.filter(o=>o.kind==='ramp')){
  place(o.x,o.y,0,-500);step();snapshot();
  const without=copy(b);without.objects=without.objects.filter(p=>p!==o&&!(p.kind==='ramp'&&p.x===o.x&&p.y===o.y));load(without);assert.equal(readState(m).ramp,-1,'deleted ramp releases rider');step();snapshot();load(b);
 }
 command('R');step();snapshot();
}
// Lane goals are the same live mission in the LCD and the editor ABI.
const laneBoard=copy(boards[0]);laneBoard.id=0x4c414e45;laneBoard.height=480;
laneBoard.objects=[0,1,2].map(group=>({kind:'lane',group,x:25+group*30,y:180,u:8,v:0,value:100}));
load(laneBoard);assert.equal(readState(m).lane_groups,7);assert.equal(readState(m).lane_goal,2);
step(8);step();assert.equal(readState(m).bonus_next,3);assert.equal(readState(m).bonus_next_arg,128);snapshot();
command('R',12345);
for(let g=0;g<3;g++){
 place(25+g*30,180);step();const state=readState(m);
 if(g<2){assert.equal(state.lanes,(1<<(g+1))-1);assert.equal(state.bonus,3);assert.equal(state.bonus_arg,128|state.lanes);}
 else {assert.equal(state.mult,2);assert.equal(state.lanes,0);assert.equal(state.lane_goal,3);assert.equal(state.bonus_next_arg,2);}
 snapshot();
}
laneBoard.objects.pop();load(laneBoard);assert.equal(readState(m).lane_groups,3,'draft missing a lane cannot advertise an impossible mission');snapshot();
console.log('Lane mission: missing A/B/C sprites, real set progress, next multiplier, launch tutorial and incomplete drafts match native/WASM.');
// Slings are editable hardware, not cabinet art. Both runtimes execute every
// contact and edit; moved/deleted faces must not leave invisible colliders.
const rubbers=editableBoard(copy(boards[8]));rubbers.objects=rubbers.objects.filter(o=>o.kind==='rubber');
function ballState(){const s=readState(m);return [s.xq,s.yq,s.vx,s.vy,s.spin_q16];}
const legacyRubbers=copy(rubbers);legacyRubbers.flags=0;legacyRubbers.objects=[];
function slingTrace(b){load(b);command('R',6789);place(41,b.height-63,-300,0);const trace=[];for(let i=0;i<24;i++){step();trace.push(ballState());}snapshot();return trace;}
assert.deepEqual(slingTrace(rubbers),slingTrace(legacyRubbers),'default editable slings preserve legacy rebound and spin');
rubbers.objects=[{kind:'rubber',group:0,x:40,y:180,u:15,v:27,value:50}];load(rubbers);command('R',6789);place(51,192,-300,0);step();
assert.ok(readState(m).score>=50,'moved rubber powers the ball and scores at its new position');snapshot();
const hit=ballState();rubbers.objects=[];load(rubbers);command('R',6789);place(51,192,-300,0);step();assert.notDeepEqual(ballState(),hit,'deleted rubber has no ghost collider');snapshot();
place(41,rubbers.height-63,-300,0);step();const removed=ballState();
load(legacyRubbers);command('R',6789);place(41,rubbers.height-63,-300,0);step();assert.notDeepEqual(ballState(),removed,'deleting both does not restore a hard-coded pair');snapshot();
rubbers.objects=[{kind:'rubber',group:1,x:88,y:150,u:24,v:40,value:0}];load(rubbers);command('R',6789);place(67,178,300,0);for(let i=0;i<30;i++)step();snapshot();
console.log('Editable rubber: legacy trajectory/pixels, relocated powered contact, resize, mirror, live removal and no ghost cabinet colliders match native/WASM.');
// Exercise an occupied ramp explicitly, including an index shift on insertion.
const fixture=copy(boards[0]);fixture.id=0x57534d31;
const ramp={kind:'ramp',x:35,y:200,u:90,v:80,value:1000,group:0};fixture.objects=[ramp];
load(fixture);place(35,201,0,-500);step();assert.equal(readState(m).ramp,0,'ramp fixture must actually capture the ball');snapshot();
const riding=readState(m);fixture.theme=8;fixture.palette=copy(boards[8].palette);load(fixture);
assert.equal(readState(m).ramp,0);assert.equal(readState(m).xq,riding.xq);assert.equal(readState(m).yq,riding.yq);
fixture.objects.unshift({kind:'bumper',x:75,y:260,u:8,v:280,value:100,group:0});load(fixture);assert.equal(readState(m).ramp,1,'unchanged ramp rider follows its new index');
fixture.objects.pop();load(fixture);assert.equal(readState(m).ramp,-1,'deleting occupied ramp releases ball');step();snapshot();
// Ramp rail pixels must stay in front of a ground-level ball and flippers.
const layered=copy(boards[0]);layered.id=0x5241494c;layered.objects=[];
load(layered);place(100,300);const emptyPtr=m._pb_render(),empty=m.HEAPU8.slice(emptyPtr,emptyPtr+m._pb_render_size());
layered.objects=[{kind:'ramp',x:35,y:220,u:75,v:120,value:1000,group:2}];load(layered);
const railPtr=m._pb_render(),railImage=m.HEAPU8.slice(railPtr,railPtr+m._pb_render_size());
const pixel=(data,x,y)=>data[(y+24)*64+(x>>1)]>>((x&1)*4)&15;
const arrowArt=JSON.parse(fs.readFileSync(path.join(dist,'assets/elements.json'))).ramp[1];
function arrowShadow(o,x,y){
 const bob=[0,-1,-2,-1][Math.floor(readState(m).ticks/10)&3];
 const ink=arrowArt[y-(o.y+4+bob-8)-2]?.[x-(o.x-1-7)-1];
 return ink!==undefined&&ink!=='.';
}
// A solid deck, including the widening throat, must replace the felt all
// the way to the exit. Check both curve directions and the central ramp.
for(const group of [0,1,2]){
 const deck=copy(layered);deck.objects[0].group=group;load(deck);
 const ptr=m._pb_render(),image=m.HEAPU8.slice(ptr,ptr+m._pb_render_size());snapshot();
 for(let t=16;t<=256;t+=4){
  const p=rampPoint(deck.objects[0],t/256),x=Math.trunc(p.x),y=Math.trunc(p.y);
  for(let dx=-1;dx<=1;dx++)assert.ok([3,5,14].includes(pixel(image,x+dx,y)),`opaque ramp deck: group ${group}, t ${t}, x ${dx}`);
 }
 for(let y=221;y<=228;y++)for(let x=32;x<=38;x++)assert.ok((arrowShadow(deck.objects[0],x,y)?[2,3,4,5,14]:[3,4,5,14]).includes(pixel(image,x,y)),'opaque flared entry floor, allowing only the floating marker shadow');
}
load(layered);
const railPixels=[];
for(let y=130;y<215;y++)for(let x=20;x<85;x++)if(pixel(railImage,x,y)!==pixel(empty,x,y))railPixels.push([x,y]);
assert.ok(railPixels.length>100,'fixture contains visible ramp rails');
place(45,187);snapshot();let ballPtr=m._pb_render(),ballImage=m.HEAPU8.slice(ballPtr,ballPtr+m._pb_render_size());
for(const [x,y] of railPixels)assert.equal(pixel(ballImage,x,y),pixel(railImage,x,y),'ball is below ramp rails');
layered.objects.push({kind:'flippers',x:30,y:180,u:94,v:23,value:0,group:0});load(layered);snapshot();
const batPtr=m._pb_render(),batImage=m.HEAPU8.slice(batPtr,batPtr+m._pb_render_size());
for(const [x,y] of railPixels)assert.equal(pixel(batImage,x,y),pixel(railImage,x,y),'flippers are below ramp rails');
// A rider must move to the top layer for the whole ride, then return below
// the rails when released. Compare the same ball position on the ground.
const ridingBoard=copy(boards[0]);ridingBoard.id=0x52494445;
ridingBoard.objects=[{kind:'ramp',x:35,y:220,u:75,v:120,value:1000,group:2}];
load(ridingBoard);place(35,221,0,-500);step();assert.equal(readState(m).ramp,0);
for(let i=0;i<35;i++)step();
const rider=readState(m),riderPtr=m._pb_render(),riderImage=m.HEAPU8.slice(riderPtr,riderPtr+m._pb_render_size());snapshot();
assert.equal(rider.ramp,0,'test ball is on the ramp');
place(rider.x,rider.y);assert.equal(readState(m).ramp,-1);
const groundPtr=m._pb_render(),groundImage=m.HEAPU8.slice(groundPtr,groundPtr+m._pb_render_size());snapshot();
let exposed=0;for(let y=rider.y-4;y<=rider.y+4;y++)for(let x=rider.x-4;x<=rider.x+4;x++)if(pixel(riderImage,x,y)!==pixel(groundImage,x,y))exposed++;
assert.ok(exposed>=8,`ramp rider is visible above the rails (${exposed} exposed pixels)`);
console.log(`Ramp elevation: grounded ball and flippers below rails; rider above rails (${exposed} pixels).`);
// The launch flap opens only at the exit, then settles shut. Pausing also
// freezes the hinge, and an incoming ball must seat it against the stop.
const shooter=copy(boards[0]);shooter.id=0x464c4150;shooter.objects=[];
load(shooter);assert.equal(readState(m).shooter_flap,0);step(8);step();
let opened=false,closed=false,paused=false;const poses=new Set();
for(let i=0;i<150;i++){
 step();const s=readState(m);poses.add(s.shooter_flap);
 if(s.shooter_flap){opened=true;if(!paused){command('Q',1);const frozen=readState(m);for(let j=0;j<6;j++)step();assert.deepEqual(readState(m).shooter_flap,frozen.shooter_flap);command('Q',0);paused=true;}}
 else if(opened)closed=true;
 if(i%3===0&&i<65)snapshot();
}
assert.ok(opened&&closed&&poses.has(80)&&poses.size>=10,'flap opens and visibly swings back shut');
command('R');step(8);step();for(let i=0;i<100&&!readState(m).shooter_flap;i++)step();
assert.ok(readState(m).shooter_flap>0);place(108,65,100,500);step();
assert.equal(readState(m).shooter_flap,0,'incoming ball seats the flap');assert.ok(readState(m).x<=108,'flap still blocks return into launcher');snapshot();
console.log(`Shooter flap: ${poses.size} hinge positions, automatic close, pause and one-way return passed.`);
// Hooded scoop: entry is directional, the held ball disappears, and the
// eject becomes visible through the lower mouth. The saucer stays open.
const cups=copy(boards[0]);cups.id=0x43555053;
cups.objects=[{kind:'scoop',x:44,y:190,u:8,v:0,value:1000,group:0}];
load(cups);command('R',12345);
place(44,178,0,500);step();assert.equal(readState(m).hold,0);assert.ok(readState(m).vy<0,'solid scoop back rebounds the ball');snapshot();
place(32,190,500,0);step();assert.equal(readState(m).hold,0);assert.ok(readState(m).vx<0,'solid scoop shoulder rebounds the ball');snapshot();
place(44,196,0,500);step();assert.equal(readState(m).hold,0,'outgoing ball cannot enter the scoop');
const cupWhites=()=>{const p=m._pb_render(),im=m.HEAPU8.slice(p,p+m._pb_render_size());let n=0;for(let y=190;y<=204;y++)for(let x=39;x<=49;x++)if(pixel(im,x,y)===1)n++;return n;};
place(44,196,0,-500);step();assert.equal(readState(m).hold,30);assert.ok(cupWhites()>0,'ball visibly enters the mouth');snapshot();
for(let i=0;i<5;i++)step();assert.equal(readState(m).hold,25);assert.equal(cupWhites(),0,'captured scoop ball is beneath the hood');snapshot();
command('Q',1);const hiddenHold=readState(m).hold;for(let i=0;i<12;i++)step();assert.equal(readState(m).hold,hiddenHold);snapshot();command('Q',0);
for(let i=0;i<21;i++)step();assert.equal(readState(m).hold,4);assert.ok(cupWhites()>0,'ball emerges through the mouth before release');snapshot();
for(let i=0;i<4;i++)step();assert.equal(readState(m).hold,0);assert.equal(readState(m).x,52);assert.equal(readState(m).y,204);snapshot();
cups.objects[0].kind='saucer';load(cups);command('R',12345);place(44,190);step();assert.equal(readState(m).hold,60);assert.ok(cupWhites()>0,'held saucer ball remains visible');snapshot();
for(let i=0;i<35;i++)step();assert.equal(readState(m).hold,25);assert.ok(cupWhites()>0,'saucer stays visible during the scoop-hidden interval');snapshot();
console.log('Scoop: front-only capture, solid hood, hidden hold, paused timing and animated mouth eject; saucer ball stays visible.');
// The saucer advertises the next actual award, including during cooldown.
// Its metal bowl must remain unchanged when its reward lamp changes.
command('R',12345);
const saucer=cups.objects[0];let bowl;
function checkSaucerLamp(ink){
 const p=m._pb_render(),im=m.HEAPU8.slice(p,p+m._pb_render_size());
 const metal=[];
 for(let y=saucer.y-8;y<=saucer.y+8;y++)for(let x=saucer.x-8;x<=saucer.x+8;x++){
  if(y===saucer.y-5&&Math.abs(x-saucer.x)<=4)assert.equal(pixel(im,x,y),ink,'saucer lamp advertises next reward');
  else metal.push(pixel(im,x,y));
 }
 if(bowl)assert.deepEqual(metal,bowl,'reward changes only the lamp, not the bowl');else bowl=metal;
 snapshot();
}
place(85,120);checkSaucerLamp(4);
for(const [index,lamp] of [10,11,4].entries()){
 const before=readState(m).score;place(saucer.x,saucer.y);step();
 assert.equal(readState(m).score-before,saucer.value*[2,3,1][index],'advertised saucer reward is awarded');
 if(index===2)assert.equal(readState(m).save,240,'green lamp leads to four-second ball save');
 place(85,120);checkSaucerLamp(lamp);
 for(let t=0;t<240;t++){place(85,120);step();}
 checkSaucerLamp(lamp);
}
console.log('Saucer lamps: cyan points, gold larger points, green ball save; real reward cycle, steady bowl and cooldown pixels match native/WASM.');
// Reach the real end-of-game screen through three drains. Capture the LCD
// before overview rendering so this checks the sketch's actual overlay.
for(const [theme,base] of boards.entries()){
 const end=copy(base);end.id=0x454e4400+theme;end.objects=[];load(end);command('R',12345);
 for(let ball=0;ball<3;ball++){place(60,end.height-13,0,1000);for(let i=0;i<16;i++)step();}
 assert.equal(readState(m).over,1,'three unsaved drains reach game over');
 const image=lcdSnapshot(),ink=(x,y)=>image[y*64+(x>>1)]>>((x&1)*4)&15;
 assert.equal(ink(3,40),[4,4,14,10,10,13,8,11,10][theme],'game-over outline uses the table accent');
 let title=0,retry=0,tables=0;
 for(let y=20;y<30;y++)for(let x=10;x<118;x++)if(ink(x,y)===1)title++;
 for(let y=99;y<109;y++)for(let x=10;x<118;x++)if(ink(x,y)===1)retry++;
 for(let y=112;y<122;y++)for(let x=10;x<118;x++)if(ink(x,y)===4)tables++;
 assert.ok(title>=100 && retry>=100 && tables>=100,'game-over title and both actions use large glyphs');
}
console.log('Game over: real three-ball drains, large themed panel and complete LCD pixels match native/WASM in all nine themes.');
// Real target-bank/scoop contacts drive the bonus queue in both targets.
const bonusBoard=copy(boards[0]);bonusBoard.id=0x424F4E55;
bonusBoard.objects=[...[24,60,96].map((x,group)=>({kind:'target',x,y:60,u:8,v:6,value:100,group})),
 {kind:'scoop',x:60,y:190,u:8,v:0,value:1000,group:0}];
load(bonusBoard);command('R',12345);
for(const o of bonusBoard.objects.slice(0,3)){place(o.x,o.y-4,0,512);step();}
assert.equal(readState(m).target,7);snapshot();
place(60,196,0,-500);step();let celebration=readState(m);
assert.equal(celebration.balls,3);assert.equal(celebration.save,600);
assert.equal(celebration.mult,1);assert.equal(celebration.effective_mult,2,'multiball HUD includes double scoring');
assert.equal(celebration.bonus,7);assert.equal(celebration.bonus_arg,10);assert.equal(celebration.bonus_next,6);snapshot();
command('Q',1);const frozenBonus=readState(m);for(let i=0;i<12;i++)step();
assert.equal(readState(m).bonus_ticks,frozenBonus.bonus_ticks);snapshot();command('Q',0);
for(let i=1;i<=84;i++){step();if([2,8,16,32,64,84].includes(i))snapshot();}
assert.equal(readState(m).bonus,6,'multiball banner follows the immediate ten-second save notice');
for(let i=0;i<160;i++){step();if(i%20===0)snapshot();}
place(60,196,0,-500);step();assert.equal(readState(m).bonus,8,'actual multiball scoop hit announces jackpot');snapshot();
console.log('Bonus announcements: multiball/save queue, pause, entry/exit frames and real jackpot; native/WASM LCD pixels included.');
// Refreshing an existing temporary mode is not a new popup-worthy reward.
const refreshBoard=copy(boards[0]);refreshBoard.id=0x52454652;refreshBoard.height=480;
refreshBoard.objects=[40,80].map(x=>({kind:'scoop',group:0,x,y:190,u:8,v:0,value:100}));
load(refreshBoard);command('R',12345);place(40,196,0,-500);step();
assert.equal(readState(m).bonus,4);assert.equal(readState(m).bonus_ticks,84);
for(let i=0;i<12;i++){place(60,220);step();}
const beforeRefresh=readState(m);place(80,196,0,-500);step();const refreshed=readState(m);
assert.equal(refreshed.effective_mult,2);assert.equal(refreshed.score,beforeRefresh.score+200);
assert.equal(refreshed.bonus_ticks,beforeRefresh.bonus_ticks-1,'active double-score banner must not restart');snapshot();
for(let i=0;i<250;i++){place(60,220);step();}
assert.equal(readState(m).bonus_ticks,0);place(40,196,0,-500);step();
assert.equal(readState(m).effective_mult,2);assert.equal(readState(m).bonus_ticks,0,'repeat hit remains silent after the initial banner ends');snapshot();
for(let i=0;i<601;i++){place(60,220);step();}
assert.equal(readState(m).effective_mult,1);place(80,196,0,-500);step();
assert.equal(readState(m).bonus,4);assert.equal(readState(m).bonus_ticks,84,'new double-score window after expiry announces normally');snapshot();
console.log('Temporary bonus announcements: first activation, silent timer refresh, expired banner and fresh post-expiry reward match native/WASM.');
// Actual key-driven tilt inside a closed pocket must finish the ball.
const tiltTrap=copy(boards[0]);tiltTrap.id=0x54494c54;tiltTrap.height=480;tiltTrap.gravity=12;
tiltTrap.objects=[[35,180,85,180],[35,140,35,180],[85,140,85,180],[35,140,85,140]].map(([x,y,u,v])=>({kind:'wall',group:0,x,y,u,v,value:0}));
load(tiltTrap);command('R',12345);place(60,175);
for(let i=0;i<4;i++){step(i%2?32:1);step();}
assert.equal(readState(m).tilt,3,'six real shoves tilt inside the trap');snapshot();
for(let i=0;i<900 && readState(m).lives===3;i++){step(18);if(i%120===0)snapshot();}
const recoveredTilt=readState(m);assert.equal(recoveredTilt.lives,2,'stuck tilted ball cannot freeze the turn');
assert.equal(recoveredTilt.tilt,0);assert.equal(recoveredTilt.shooter,1);assert.equal(recoveredTilt.score,0);snapshot();
console.log('Tilt search: real trapped ball, key-driven tilt, automatic turn advance and zero points match native/WASM.');
// Explicit seeds reproduce the whole collision sequence; drawing frequency
// must not affect gameplay randomness. A different seed changes the rebound.
const scatterBoard=copy(boards[0]);scatterBoard.id=0x53434154;
scatterBoard.objects=[{kind:'bumper',x:64,y:140,u:8,v:280,value:180,group:0}];load(scatterBoard);
function seededRun(seed,extraDraws=false){
 command('R',seed);assert.equal(readState(m).seed,seed>>>0);place(64,128,0,600);const trace=[];
 for(let i=0;i<60;i++){
  step(i%23<4?16:0);
  const state=readState(m);delete state.frame;trace.push(state);
  if(extraDraws){m._pb_render();m._pb_render();assert.equal(readState(m).rng,state.rng);}
  if(i%10===0)snapshot();
 }
 return trace;
}
const replayA=seededRun(0x12345678),replayB=seededRun(0x12345678,true);
assert.deepEqual(replayB,replayA,'same seed/inputs must reproduce physics regardless of render frequency');
const replayC=seededRun(0x87654321);
if(physics.scatter_powered)assert.notEqual(replayC[0].vx,replayA[0].vx,'enabled scatter changes the first bumper rebound with the seed');
else {
 const motion=trace=>trace.map(s=>[s.xq,s.yq,s.vx,s.vy,s.spin_q16]);
 assert.deepEqual(motion(replayC),motion(replayA),'disabled synthetic variation makes bumper trajectories independent of seed');
}
if(physics.spin_grip){
 command('R',12345);place(61,128,250,600);step();
 assert.notEqual(readState(m).spin_q16,0,'an oblique bumper hit must generate contact spin');snapshot();
 for(let i=0;i<4;i++)step();assert.notEqual(readState(m).spin_q16,0,'light spin persists between contacts');snapshot();
}
command('R',12345);const seedBefore=readState(m);const retheme=copy(scatterBoard);retheme.theme=1;retheme.palette=copy(boards[1].palette);load(retheme);
assert.equal(readState(m).rng,seedBefore.rng);assert.equal(readState(m).seed,seedBefore.seed);
const blank=copy(scatterBoard);blank.objects=[];load(blank);command('R',12345);place(11,180,-200,0);step();
assert.equal(readState(m).rng,12345,'gentle resting contact does not consume RNG');
command('R',12345);place(11,180,-800,0);step();assert.notEqual(readState(m).rng,12345,'firm passive rebound consumes RNG');snapshot();
command('R');const autoSeed=readState(m).seed;command('R');assert.notEqual(readState(m).seed,autoSeed,'new games get fresh session seeds');
console.log('Physics model: compiled configuration, repeatable impacts, seed-independent motion with scatter disabled, contact spin, rendering independence and live edits passed.');
const result=spawnSync(native,[],{input:Buffer.concat(inputs),maxBuffer:64*1024*1024});
assert.equal(result.status,0,`Native replay failed: signal=${result.signal}, error=${result.error?.message ?? 'none'}\n${result.stderr?.toString()}`);if(result.stderr?.length)console.log(result.stderr.toString().trim());const expected=Buffer.concat(outputs);
if(!expected.equals(result.stdout)){
 let at=0;while(at<expected.length&&expected[at]===result.stdout[at])at++;
 throw new Error(`Native/WASM discrepancy at byte ${at}: WASM=${expected[at]} native=${result.stdout[at]} (lengths ${expected.length}/${result.stdout.length})`);
}
console.log(`Native/WASM parity: ${boards.length} boards, ${steps} ticks, ${edits} live edits, ${snapshots} complete state/pixel snapshots.`);
