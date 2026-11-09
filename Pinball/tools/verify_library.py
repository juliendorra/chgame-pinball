#!/usr/bin/env python3
"""Check all menu crests against source sprites while another table is active."""
import argparse,hashlib,json,os,sys
from pathlib import Path
G=Path(__file__).resolve().parents[1];R=G.parent
sys.path[:0]=[str(R/'CHGame/tools/chsim'),str(G/'editor'),str(G/'tools')]
from chdrivelib import Driver,SimTransport
from protocol import LiveClient,encode
from boards import image
from sprites import INK
from fbimage import to_image
p=argparse.ArgumentParser();p.add_argument('--exe',type=Path,default=G/'out/verify/sim-verify');a=p.parse_args()
out=G/'out/library';out.mkdir(parents=True,exist_ok=True)
boards=json.loads((G/'boards/tables.json').read_text());art=list(json.loads((G/'sprites/board_borders.json').read_text()).values())
files={b['file']+'.PBT':encode(b) for b in boards};image(out/'boards.img',files);os.environ['CHSD_CARD']=str(out/'boards.img')
t=SimTransport(a.exe);d=Driver(t,'MPIN');c=LiveClient(t);checks=0;signatures=set()
def check(value,label):
 global checks
 assert value,label
 checks+=1
def tap(mask):d.buttons(mask);d.frames(1);d.buttons(0);d.frames(1)
def pixel(data,x,y):return data[y*64+x//2]>>((x&1)*4)&15
try:
 d.handshake();d.frames(1)
 # Keep pirate active; navigation must use the preview's theme and palette.
 c.upload(encode(boards[-1]));d.frames(1);tap(128)
 choices=[boards[0]]+boards
 for index,board in enumerate(choices):
  if index:tap(32)
  shot=d.shot();skin=art[board['theme']];accents=[4,4,14,10,10,13,8,11,10]
  for y,row in enumerate(skin['emblem']):
   for x,ink in enumerate(row):
    expected=0 if ink=='.' else accents[board['theme']] if ink=='c' else INK[ink]
    for dy in range(4):
     for dx in range(4):check(pixel(shot,70+x*4+dx,41+y*4+dy)==expected,f'{board["title"]}: menu crest {x},{y}: {pixel(shot,70+x*4+dx,41+y*4+dy)} != {expected}')
  signature=bytes(pixel(shot,x,y) for y in range(41,73) for x in range(70,118));signatures.add(hashlib.sha256(signature).hexdigest())
  to_image(shot,4).save(out/(str(index)+'-'+board['file']+'.png'))
  check(pixel(shot,69,41)==0 and pixel(shot,118,41)==0,'crest shares preview felt')
 check(len(signatures)==9,'nine distinct themed menu crests')
 # Back to the suspended game; menu browsing did not replace it.
 tap(2);s=c.state();check(s['id']==boards[-1]['id'],'B resumes the suspended pirate table')
 print(f'PASS: {checks} library checks; every crest matches editable art, including previews differing from the active board')
 (out/'report.json').write_text(json.dumps(dict(checks=checks,themes=len(signatures),result='passed'),indent=2)+'\n')
finally:
 d.buttons(0);assert t.close()==0,t.bugs
