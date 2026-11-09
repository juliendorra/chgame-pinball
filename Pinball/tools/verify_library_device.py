#!/usr/bin/env python3
"""Check actual CHGame board picker crests against the editable theme sprites."""
import argparse,json,sys,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];R=G.parent
sys.path[:0]=[str(R/'CHGame/tools/chsim'),str(G/'editor'),str(G/'tools')]
from chdrivelib import SerialTransport
from protocol import LiveClient,encode
from sprites import INK
p=argparse.ArgumentParser();p.add_argument('--port',required=True);a=p.parse_args()
boards=json.loads((G/'boards/tables.json').read_text());art=list(json.loads((G/'sprites/board_borders.json').read_text()).values())
byfile={b['file']:b for b in boards};accents=[4,4,14,10,10,13,8,11,10]
version=json.loads((G/'chgame.json').read_text())['version'];out=G/f'out/device/v{version}';out.mkdir(parents=True,exist_ok=True)
t=SerialTransport(a.port);c=LiveClient(t);checks=0

def check(value,label):
 global checks
 assert value,label
 checks+=1

def tap(mask):
 c.request('K '+str(mask));time.sleep(.06);c.request('K 0');time.sleep(.04)

def pixel(data,x,y):return data[y*64+x//2]>>((x&1)*4)&15
try:
 hello=c.hello();check(version in hello,'installed version')
 entries=c.boards();c.upload(encode(boards[-1]));time.sleep(.03);tap(128)
 for entry in entries:
  if entry['index']:tap(32)
  board=byfile.get(entry['file'])
  if board is None:continue
  shot=bytes.fromhex(c.request('H')[-1].removeprefix('LIVE DATA '));check(len(shot)==8192,'complete framebuffer')
  for y,row in enumerate(art[board['theme']]['emblem']):
   for x,ink in enumerate(row):
    expected=0 if ink=='.' else accents[board['theme']] if ink=='c' else INK[ink]
    for dy in range(4):
     for dx in range(4):check(pixel(shot,70+x*4+dx,41+y*4+dy)==expected,f'{board["title"]}: crest {x},{y}')
  print('PASS: '+board['title']+' menu crest',flush=True)
 tap(2);check(c.state()['id']==boards[-1]['id'],'B resumes original board')
 # Re-enter and move from the final library entry to the real SD pirate board.
 tap(128);pirate=next(e['index'] for e in entries if e['file']=='PIRATES')
 for _ in range(len(entries)-1-pirate):tap(16)
 tap(1);c.request('R');check(c.board()==encode(boards[-1]),'SD pirate board is ready')
 report=dict(hello=hello,checks=checks,entries=len(entries),result='passed')
 (out/'library-hardware.json').write_text(json.dumps(report,indent=2)+'\n')
 print(f'PASS: {checks} actual-device menu checks',flush=True)
finally:
 try:c.request('K 0')
 finally:t.close()
