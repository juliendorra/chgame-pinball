#!/usr/bin/env python3
"""Probe progressive shake, tilt and PWM on the actual release cart."""
import argparse,copy,json,sys,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];R=G.parent
sys.path[:0]=[str(R/'CHGame/tools/chsim'),str(G/'editor')]
from chdrivelib import SerialTransport
from protocol import LiveClient,encode
p=argparse.ArgumentParser();p.add_argument('--port',required=True);a=p.parse_args()
t=SerialTransport(a.port);c=LiveClient(t);report={'checks':[]}
version=json.loads((G/'chgame.json').read_text())['version'];out=G/f'out/device/v{version}';out.mkdir(parents=True,exist_ok=True)
boards=json.loads((G/'boards/tables.json').read_text());blank=copy.deepcopy(boards[0]);blank.update(objects=[],height=480,gravity=12,id=0x53484b45)
def check(v,label,detail=None):
 assert v,(label,detail)
 report['checks'].append({'check':label,'detail':detail});print('PASS:',label,detail or '',flush=True)
def shake():return list(map(int,c.request('N')[-1].split()[2:]))
def tap(mask):
 c.request('K '+str(mask));time.sleep(.04);c.request('K 0');time.sleep(.025)
def reset():c.request('K 0');c.request('Q 0');c.request('R');time.sleep(.025)
try:
 report['hello']=c.hello();check(version in report['hello'],'new release is running',report['hello'])
 c.upload(encode(blank));reset();tap(1);check(not c.state()['shooter'] and shake()[0]==0,'A launches before play')
 reset();tap(8);check(not c.state()['shooter'] and shake()[0]==0,'Down launches without shaking')
 reset();c.request('P 60,160');tap(1);s=c.state();check(s['vx']>0 and shake()[0]==1,'A shoves left, ball moves right',s['vx'])
 reset();c.request('P 60,160');tap(32);s=c.state();check(s['vx']<0 and shake()[0]==1,'Right shoves right, ball moves left',s['vx'])
 reset();c.request('P 60,160');c.request('K 1')
 for _ in range(3):time.sleep(.14);c.request('K 1')
 c.request('K 0');check(shake()[0]==1,'held input and heartbeat never escalate')
 time.sleep(.5);tap(32);check(shake()[0]==1,'slow taps reset the strength')
 reset();c.request('P 60,160')
 for level in range(1,4):
  tap(1 if level%2 else 32);s=shake();check(s[0]==level and s[5]==0,f'progressive level {level}',s)
 tap(32);s=shake();check(s[5]==3,'fourth rapid press tilts',s)
 c.request('K 18');time.sleep(.12);s=c.state();check(s['left']==s['right']==0,'tilt disables flippers')
 c.request('K 0');time.sleep(.5);check(shake()[5]==3,'tilt remains after wobble stops')
 # Add a scoring mechanism in place, retaining the tilted game state.
 scored=copy.deepcopy(blank);scored['objects']=[dict(kind='bumper',group=0,x=60,y=180,u=8,v=300,value=100)]
 c.upload(encode(scored));score=c.state()['score'];c.request('P 60,169');time.sleep(.15)
 check(c.state()['score']==score and shake()[5]==3,'tilted bumper cannot award score')
 c.request('P 60,467');time.sleep(1.7);s=c.state();check(s['lives']==2 and s['shooter'] and shake()[5]==0,'drain consumes ball and resets tilt',s)
 # Sample an uninterrupted active wobble and compare frame clocks.
 c.upload(encode(blank));reset();c.request('P 60,100');tap(1)
 first=c.state();start=time.monotonic();time.sleep(.35);last=c.state()
 fps=(last['frames']-first['frames'])/(time.monotonic()-start)
 check(56<=fps<=64,'active shake keeps the game near 60 fps',round(fps,2));report['shake_fps']=fps
 time.sleep(.4);s=shake();check(s[2]==s[3]==s[4]==0,'wobble settles to exact rest',s)
 r=list(map(int,c.request('E')[-1].split()[2:]));check(r[0]==r[1]==r[4]==0 and (r[2]>>18)&7==6,'PC0 PWM returns to zero with TIM2 CH4 remap intact',r)
 report['result']='passed'
finally:
 try:c.request('K 0');c.upload(encode(boards[-1]));c.request('R')
 finally:t.close();(out/'shake-hardware.json').write_text(json.dumps(report,indent=2)+'\n')
