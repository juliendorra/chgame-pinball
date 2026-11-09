#!/usr/bin/env python3
"""Check rumble registers and themed emblems on the actual release firmware."""
import argparse
import json
from pathlib import Path
import struct
import sys
import time

GAME=Path(__file__).resolve().parents[1];ROOT=GAME.parent
sys.path[:0]=[str(ROOT/'CHGame/tools/chsim'),str(GAME/'editor')]
from chdrivelib import SerialTransport,SimTransport,Driver
from protocol import LiveClient,encode
from fbimage import to_image

p=argparse.ArgumentParser();p.add_argument('--port',required=True);p.add_argument('--exe',type=Path,default=GAME/'out/editor/pinball-studio');a=p.parse_args()
version=json.loads((GAME/'chgame.json').read_text())['version']
out=GAME/f'out/device/v{version}';out.mkdir(parents=True,exist_ok=True)
report={'checks':[]}
def check(value,label,detail=None):
    assert value,(label,detail)
    report['checks'].append({'check':label,'detail':detail});print('PASS:',label,detail or '',flush=True)
def pixel(f,x,y):return (f[y*64+x//2]>>((x&1)*4))&15

t=SerialTransport(a.port);c=LiveClient(t)
sim=SimTransport(a.exe);d=Driver(sim,'MPIN');native=LiveClient(sim)
try:
    report['hello']=c.hello();check(version in report['hello'],'installed release identifies itself as '+version)
    d.handshake();d.frames(1)
    old=c.board();specs=json.loads((GAME/'boards/tables.json').read_text())
    c.upload(encode(specs[-1]));c.request('R')
    def rumble():return list(map(int,c.request('E')[-1].split()[2:]))
    r=rumble();check(r[:2]==[0,0] and r[4]==0,'new game starts with PWM off',r)
    check((r[2]>>18)&7==6 and r[3]&15==11,'GPIO1/PC0 is TIM2 CH4 full-remap, alternate-function push-pull',r)
    c.request('K 1');time.sleep(.04);c.request('K 0');time.sleep(.012)
    r=rumble();check(r[0]==150 and 0<r[1]<=90 and r[4]==150000//255,'launch produces the configured hardware PWM pulse',r)
    time.sleep(.13);r=rumble();check(r[:2]==[0,0] and r[4]==0,'timer interrupt shuts PWM off after launch',r)
    c.request('R');bumper=next(o for o in specs[-1]['objects'] if o['kind']=='bumper')
    c.request(f"P {bumper['x']},{bumper['y']-bumper['u']-3}");time.sleep(.02)
    r=rumble();check(r[0]==210 and r[4]==210000//255,'actual bumper contact produces stronger PWM',r)
    c.request('Q 1');time.sleep(.02);r=rumble();check(r[:2]==[0,0] and r[4]==0,'pause immediately stops vibration',r)
    c.request('Q 0')
    for spec in specs:
        data=encode(spec);c.upload(data);c.request('R');c.request('P 64,20');c.request('M -24');time.sleep(.02)
        state=c.state();check(state['camera']==-24 and state['zoom']==256,'full header is visible: '+spec['title'])
        fb=bytes.fromhex(c.request('H')[-1].removeprefix('LIVE DATA '));check(len(fb)==8192,'release framebuffer transfer is complete')
        native.upload(data);native.request('R');native.request('P 64,20');native.request('M -24');d.frames(1)
        shot=d.shot();expected=shot[:8192]
        actual=[pixel(fb,x,y) for y in range(14,38) for x in range(46,82)]
        reference=[pixel(expected,x,y) for y in range(14,38) for x in range(46,82)]
        check(actual==reference,'large top crest matches Studio: '+spec['title'])
        check(sum(v not in (0,2) for v in actual)>250,'large crest has recognizable detail: '+spec['title'])
        # Keep both of the smaller rail-cheek emblems too.
        for x0 in (0,112):
            actual=[pixel(fb,x,y) for y in range(43,54) for x in range(x0,x0+16)]
            reference=[pixel(expected,x,y) for y in range(43,54) for x in range(x0,x0+16)]
            check(actual==reference,'LCD emblem matches Studio: '+spec['title']+(' left' if x0==0 else ' right'))
            check(sum(v not in (0,2) for v in actual)>30,'emblem has visible detail: '+spec['title'])
        to_image(fb+shot[8192:],4).save(out/(spec['file']+'-top.png'))
    c.upload(encode(specs[-1]));c.request('R');c.request('Q 1');c.request('M -24')
    first=c.state();start=time.monotonic();time.sleep(2);last=c.state()
    fps=(last['frames']-first['frames'])/(time.monotonic()-start)
    report['paused_header_fps']=fps
    # Pause redraws the full overlay; gameplay's 60 Hz budget is checked
    # separately by verify_shake_device.py while physics and wobble run.
    check(55<=fps<=63,'static full-header pause overlay stays above 55 fps',round(fps,2))
    c.request('Q 0');c.request('R')
    report['result']='passed'
finally:
    try:c.request('K 0')
    except Exception:pass
    t.close();assert sim.close()==0,sim.bugs
    (out/'effects-hardware.json').write_text(json.dumps(report,indent=2)+'\n')
