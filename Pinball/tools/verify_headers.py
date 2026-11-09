#!/usr/bin/env python3
"""Require large themed roof decorations in both LCD and Studio overview."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

GAME=Path(__file__).resolve().parents[1];ROOT=GAME.parent
sys.path[:0]=[str(ROOT/'CHGame/tools/chsim'),str(GAME/'editor'),str(GAME/'tools')]
from chdrivelib import Driver,SimTransport
from protocol import LiveClient,encode
from sprites import INK

p=argparse.ArgumentParser();p.add_argument('--exe',type=Path,default=GAME/'out/verify/sim-verify');a=p.parse_args()
out=GAME/'out/headers';out.mkdir(parents=True,exist_ok=True)
specs=json.loads((GAME/'boards/tables.json').read_text())
skins=list(json.loads((GAME/'sprites/board_borders.json').read_text()).values())
colors=[4,4,14,10,10,13,8,11,10]
t=SimTransport(a.exe);d=Driver(t,'MPIN');c=LiveClient(t)
checks=[];signatures=set()
def check(value,label):
    assert value,label
    checks.append(label)
def pixel(data,x,y):return data[y*64+x//2]>>((x&1)*4)&15
try:
    d.handshake();d.frames(1)
    for spec,skin in zip(specs,skins):
        c.upload(encode(spec));d.frames(1);d.cmd('M -24');d.cmd('W 256');shot=d.shot()
        for row in ('-25','-2147483648','4294967272','99999999999999999'):
            try:c.request('M '+row);raise AssertionError('invalid camera row accepted: '+row)
            except RuntimeError:pass
            check(d.shot()==shot,spec['title']+' rejects invalid camera row '+row)
        marks=0
        for y,row in enumerate(skin['emblem']):
            for x,ink in enumerate(row):
                if ink=='.':continue
                color=colors[spec['theme']] if ink=='c' else INK[ink]
                for dy in range(3):
                    for dx in range(3):
                        check(pixel(shot,46+x*3+dx,14+y*3+dy)==color,f"{spec['title']} crest pixel {x},{y}:{dx},{dy}")
                        marks+=color not in (0,2)
        check(marks>250,spec['title']+' has a large, recognizable central crest')
        region=bytes(pixel(shot,x,y) for y in range(14,38) for x in range(46,82))
        signatures.add(hashlib.sha256(region).hexdigest())
        t.send('H');header=d.expect('OVERVIEW ');n=int(header.split()[1]);data=t.read(n);d.expect('OK')
        check(n==(spec['height']+24)*64+32,spec['title']+' overview includes all header rows')
        check(data[:24*64]==shot[12*64:36*64],spec['title']+' Studio header matches the LCD renderer')
        # The felt surrounding the large crest must be the board's own BG,
        # with no opaque panel behind the decoration.
        check(pixel(shot,10,13)==0 and pixel(shot,116,13)==0,spec['title']+' header shares the felt background')
        d.cmd('M 0');d.cmd('J 64,14,0,0');d.frames(4)
        line=d.query('V','PIN ');state={k:int(v) for k,v in (part.split('=') for part in line.split()[1:])}
        check(state['camera']==-24,spec['title']+' live camera reveals the full crest at the top')
    check(len(signatures)==9,'all nine large themed headers are visually distinct')
    (out/'report.json').write_text(json.dumps({'checks':len(checks),'result':'passed','themes':len(signatures)},indent=2)+'\n')
    print(f'PASS: {len(checks)} header checks, nine distinct themes, shared felt, camera reveal and matching Studio header')
finally:
    assert t.close()==0,t.bugs
