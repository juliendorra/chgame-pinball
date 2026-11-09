#!/usr/bin/env python3
"""Check progressive shake against the real solver, compositor and score art."""
import argparse
import copy
import json
from pathlib import Path
import sys
G=Path(__file__).resolve().parents[1];R=G.parent
sys.path[:0]=[str(R/'CHGame/tools/chsim'),str(G/'editor'),str(G/'tools')]
from chdrivelib import Driver,SimTransport
from protocol import LiveClient,encode
from sprites import INK
p=argparse.ArgumentParser();p.add_argument('--exe',type=Path,default=G/'out/verify/sim-verify');a=p.parse_args()
t=SimTransport(a.exe);d=Driver(t,'MPIN');c=LiveClient(t);checks=0
boards=json.loads((G/'boards/tables.json').read_text())
blank=copy.deepcopy(boards[0]);blank.update(objects=[],height=480,gravity=12,id=0x53484b45)
def check(v,label):
 global checks
 assert v,label
 checks+=1
def state():
 return {k:int(v) for k,v in (p.split('=') for p in d.query('V','PIN ').split()[1:])}
def tap(mask):
 d.buttons(mask);d.frames(1);d.buttons(0);d.frames(1)
def reset():
 d.buttons(0);c.request('Q 0');c.request('R');d.frames(1)
def ball(y=180):d.cmd(f'J 60,{y},0,0')
def overview():
 t.send('H');n=int(d.expect('OVERVIEW ').split()[1]);data=t.read(n);d.expect('OK');return data
def pixel(data,x,y):return data[y*64+x//2]>>((x&1)*4)&15
try:
 d.handshake();d.frames(1);c.upload(encode(blank));d.frames(1)
 for key in (1,8):
  reset();tap(key);s=state();check(not s['shooter'] and s['shake_level']==0,'A/Down launches without shaking')
 reset();tap(32);check(state()['shake_level']==0 and state()['shooter'],'no prelaunch shake')
 # Only fresh press edges escalate, even with repeated USB key heartbeats.
 reset();ball();d.buttons(1);d.frames(1)
 check(state()['shake_level']==1 and state()['vx']>0,'left shove gives rightward inertia')
 for _ in range(10):d.buttons(1);d.frames(1)
 check(state()['shake_level']==1 and state()['tilt']==0,'held/repeated key is one shove')
 d.buttons(0);d.frames(50);check(state()['shake_ticks']==0 and state()['shake_x']==state()['shake_y']==0,'700 ms animation settles')
 tap(32);check(state()['shake_level']==1,'combo resets after 420 ms')
 # Last accepted 60 Hz boundary is 25 frames (417 ms); frame 26 resets.
 for gap,expected in ((25,2),(26,1)):
  reset();ball();d.buttons(1);d.frames(1);d.buttons(0);d.frames(gap-1)
  d.buttons(32);d.frames(1);check(state()['shake_level']==expected,f'combo boundary at {gap} frames')
 reset();ball();tap(32);check(state()['vx']<0,'right shove gives leftward inertia')
 reset();ball();tap(33);check(state()['shake_level']==1 and state()['vx']<0,'simultaneous keys count one shove')
 # Compare vertical dynamics with an identical unshaken ball.
 reset();ball();d.frames(1);vy=state()['vy']
 reset();ball();d.buttons(1);d.frames(1);check(state()['vy']==vy,'shake preserves gravity and has no vertical impulse')
 # Repeat alternating nudges so the ball stays away from cabinet walls.
 reset();ball()
 for n in range(1,4):
  ball()
  tap(1 if n%2 else 32);s=state();check(s['shake_level']==n and s['tilt']==0,f'progression level {n}')
  strength=2*n-1;expected=int(int(strength*256*1023/1024)*1023/1024)
  check(abs(s['vx'])==expected,f'level {n} maps to old strength {strength}, including unchanged maximum')
 score=s['score'];tap(32);s=state();check(s['tilt']==3 and s['save']==0,'fourth rapid tap tilts and cancels ball save')
 d.buttons(18);d.frames(5);check(state()['left']==state()['right']==0,'tilt disables both flippers')
 d.cmd('O 10000');check(state()['score']==score,'tilt refuses score awards')
 d.buttons(0);d.frames(60);check(state()['tilt']==3,'tilt persists beyond shake decay')
 d.cmd('J 61,490,0,300');d.frames(1);s=state();check(s['lives']==2 and s['shooter'] and s['tilt']==0 and s['shake_level']==0,'drain clears tilt and serves next ball')
 # Pausing freezes the shake window, waveform and physics.
 reset();ball();tap(1);c.request('Q 1');s=state();d.frames(10);q=state()
 check(all(q[k]==s[k] for k in ('ticks','shake_window','shake_ticks','shake_x','shake_y','xq','yq')),'pause freezes shake and physics')
 # Every drain settles the cabinet, including the last life / game over.
 reset()
 for life in (2,1,0):
  d.cmd('J 61,490,0,0');d.buttons(1);d.frames(1);d.buttons(0);d.frames(1);s=state()
  check(s['lives']==life and s['shake_ticks']==s['shake_level']==s['shake_x']==s['shake_y']==0,'drain settles cabinet, lives='+str(life))
 check(state()['over']==1,'last-life shake cannot freeze a displaced game-over board')
 reset()
 # First-tap motion is visible, with bounded rendering-only amplification.
 reset();ball(100);d.buttons(1);d.frames(1);d.buttons(0)
 peak=0
 for _ in range(42):
  s=state();peak=max(peak,abs(s['shake_x']))
  check(abs(s['shake_x'])<=6 and abs(s['shake_y'])<=1,'jolt stays within compositor padding')
  d.frames(1)
 check(peak>=3,'even the first shove moves the board at least three pixels')
 # High-contrast edge pulses and a three-segment footer exist in both directions.
 for key in (1,32):
  for level in (1,2,3):
   reset();ball(100)
   for n in range(level-1):tap(1 if n%2 else 32)
   d.buttons(key);d.frames(1);d.buttons(0);s=state();shot=d.shot()
   check(s['shake_level']==level,'fixture reaches visual level '+str(level))
   for x in (0,1,126,127):check(pixel(shot,x,15)==1,'immediate white cabinet edge pulse')
   color=6 if level==3 else 9 if level==2 else 10
   for n in range(3):check(pixel(shot,3+n*9,125)==(color if n<level else 5),'large footer strength segment')
   # A second warm pulse appears after the dark interval, then clears.
   d.frames(12);shot=d.shot()
   for x in (0,126):check(pixel(shot,x,15)==(6 if level==3 else 10),'second edge pulse shows warning strength')
   c.request('Q 1');d.frames(1);before=d.shot();frozen=state();overview()
   check(d.shot()==before and state()['shake_ticks']==frozen['shake_ticks'],'overview preserves the live effect and its age')
   d.frames(20);check(d.shot()==before,'pause freezes visual impact effects')
   c.request('Q 0');d.frames(45);check(state()['shake_ticks']==0,'shake feedback expires')
 # Captured balls follow their mechanism, not a cabinet shove.
 for kind in ('ramp','saucer'):
  b=copy.deepcopy(blank)
  b['objects']=[dict(kind=kind,group=0,x=60,y=180,u=90 if kind=='ramp' else 8,v=80 if kind=='ramp' else 0,value=100)]
  c.upload(encode(b));d.frames(1);reset();d.cmd(f'J 60,{192 if kind=="ramp" else 180},0,-200');d.frames(1)
  first=state();check(first['ramp']>=0 if kind=='ramp' else first['hold']>0,kind+' captures ball')
  tap(1);s=state();check(s['vx']==first['vx'] and s['vy']==first['vy'],kind+' rider gets no free-ball impulse')
 c.upload(encode(blank));d.frames(1)
 # Pixel-exact shifted image against the native unshifted full-board render.
 c.request('Q 0');reset();ball();shifted=set()
 for n in range(3):tap(1 if n%2 else 32)
 for _ in range(22):
  s=state();dx,dy=s['shake_x'],s['shake_y'];camera=s['camera']
  if (dx,dy) not in shifted:
   full=overview();shot=d.shot();shifted.add((dx,dy))
   for y in range(12,120):
    for x in range(5,123):
     sx,sy=x-dx,y-dy
     expected=pixel(full,sx,sy-12+camera+24) if 0<=sx<128 and 12<=sy<120 else 0
     check(pixel(shot,x,y)==expected,f'pixel shift {dx},{dy} at {x},{y}')
   # Same header render appears in overview and remains independent of shake.
   check(len(full)==(blank['height']+24)*64+32,'overview has no inserted seams or rows')
  d.frames(1)
 check(len(shifted)>=4,'multiple positive/negative displacements covered')
 # All 90 editable score glyphs are unchanged after lossless packing.
 fonts=list(json.loads((G/'sprites/score_digits.json').read_text()).values())
 colors=[4,4,14,10,10,13,8,11,10]
 for theme,font in enumerate(fonts):
  b=copy.deepcopy(blank);b['theme']=theme;b['id']+=theme+1;c.upload(encode(b));d.frames(1)
  for digit,rows in enumerate(font):
   reset();d.cmd(f'O {digit}');d.frames(1);shot=d.shot()
   for y,row in enumerate(rows):
    for x,ink in enumerate(row):
     expected=7 if ink=='.' else colors[theme] if ink=='c' else INK[ink]
     check(pixel(shot,3+x,y)==expected,f'score glyph {theme}:{digit} pixel {x},{y}')
 print(f'PASS: {checks} shake/tilt/packed-score checks; {len(shifted)} compositor displacements, 90 glyphs')
 out=G/'out/shake';out.mkdir(parents=True,exist_ok=True)
 (out/'report.json').write_text(json.dumps(dict(checks=checks,result='passed',displacements=sorted(shifted),glyphs=90),indent=2)+'\n')
finally:
 d.buttons(0);assert t.close()==0,t.bugs
