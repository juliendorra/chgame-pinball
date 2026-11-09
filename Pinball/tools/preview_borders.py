#!/usr/bin/env python3
"""Render the actual upper and lower playfield for every themed border skin."""
import json
import os
from pathlib import Path
import sys
from PIL import Image,ImageDraw

GAME=Path(__file__).resolve().parents[1];ROOT=GAME.parent
sys.path.insert(0,str(ROOT/'CHGame/tools/chsim'))
sys.path.insert(0,str(GAME/'tools'))
from sim_build import build
from chdrivelib import Driver,SimTransport
from fbimage import to_image
from boards import image,encode

specs=json.loads((GAME/'boards/tables.json').read_text())
out=GAME/'out/borders';out.mkdir(parents=True,exist_ok=True)
card=out/'boards.img';image(card,{t['file']+'.PBT':encode(t) for t in specs})
os.environ['CHSD_CARD']=str(card)
t=SimTransport(build(GAME));d=Driver(t,'MPIN')
atlas=Image.new('RGB',(792,468),(17,24,36));draw=ImageDraw.Draw(atlas)
try:
 d.handshake();d.frames(1)
 for index,spec in enumerate(specs,1):
  d.cmd(f'F {index}');d.frames(1);lower=to_image(d.shot(),1)
  d.cmd('M -24');d.cmd('W 256');upper=to_image(d.shot(),1)
  upper.save(out/(spec['file']+'-top.png'));lower.save(out/(spec['file']+'-lower.png'))
  x=((index-1)%3)*264;y=((index-1)//3)*156
  draw.text((x+4,y+3),spec['title'],fill=(230,235,245))
  atlas.paste(upper,(x+3,y+20));atlas.paste(lower,(x+133,y+20))
finally:
 assert t.close()==0,t.bugs
atlas.save(GAME/'docs/borders.png')
print('Rendered all nine top/side skins from the real game: Pinball/docs/borders.png')
