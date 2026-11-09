#!/usr/bin/env python3
"""Require readable shake impacts and strength feedback on the actual LCD."""
import argparse,copy,json,sys,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];sys.path[:0]=[str(G.parent/'CHGame/tools/chsim'),str(G/'editor')]
from chdrivelib import SerialTransport
from protocol import LiveClient,encode
boards=json.loads((G/'boards/tables.json').read_text());b=copy.deepcopy(boards[0]);b.update(objects=[],height=480,gravity=12,id=0x53484b45)
p=argparse.ArgumentParser();p.add_argument('--port',required=True);a=p.parse_args()
version=json.loads((G/'chgame.json').read_text())['version'];out=G/f'out/device/v{version}';out.mkdir(parents=True,exist_ok=True)
t=SerialTransport(a.port);c=LiveClient(t);checks=[]
def check(v,label):assert v,label;checks.append(label);print('PASS:',label,flush=True)
def tap(key):c.request('K '+str(key));time.sleep(.035);c.request('K 0');time.sleep(.025)
def pixel(data,x,y):return data[y*64+x//2]>>((x&1)*4)&15
try:
 check(version in c.hello(),'installed version')
 c.upload(encode(b))
 for key in (1,32):
  for level in (1,5):
   c.request('K 0');c.request('Q 0');c.request('R');c.request('P 60,100')
   for i in range(level-1):tap(1 if i%2 else 32)
   c.request('K '+str(key));time.sleep(.025);c.request('K 0');c.request('Q 1');time.sleep(.025)
   state=list(map(int,c.request('N')[-1].split()[2:]));shot=bytes.fromhex(c.request('H')[-1].removeprefix('LIVE DATA '))
   check(state[0]==level and state[-1]==0,f'level {level}, key {key}, no tilt')
   check(0<state[2]<=41 and abs(state[3])<=6 and abs(state[4])<=1,'bounded visible jolt')
   print('Captured shake state / edge:',state,[pixel(shot,x,15) for x in (0,1,126,127)],flush=True)
   check(any(pixel(shot,x,15)==1 for x in (0,1)) and any(pixel(shot,x,15)==1 for x in (126,127)),'bright white edge impact on actual LCD')
   check(all(pixel(shot,3+i*6,125)==((6 if level==5 else 10) if i<level else 5) for i in range(5)),'large level meter and red danger color on actual LCD')
   time.sleep(.09);check(bytes.fromhex(c.request('H')[-1].removeprefix('LIVE DATA '))==shot,'pause holds effect pixels steady')
 (out/'feedback-hardware.json').write_text(json.dumps(dict(result='passed',checks=checks),indent=2)+'\n')
finally:
 try:c.request('K 0');c.upload(encode(boards[-1]));c.request('Q 0');c.request('R')
 finally:t.close()
