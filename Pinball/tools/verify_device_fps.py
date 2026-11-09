#!/usr/bin/env python3
"""Measure real CHGame render/physics rates with RAM-only ramp fixtures.

Restarts the current table after the test; SD boards and saves are untouched.
python3 Pinball/tools/verify_device_fps.py --port /dev/cu.usbmodem101 --out result.json
"""
import argparse
import json
from pathlib import Path
import sys
import time

GAME=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(GAME/'editor'),str(GAME/'tools'),str(GAME.parent/'CHGame/tools/chsim')]
from boards import encode
from protocol import LiveClient,decode
from chdrivelib import SerialTransport

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',help='Auto-detect CHGame when omitted');p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=3);p.add_argument('--min-hz',type=float,default=57)
    a=p.parse_args()
    if not 1<=a.seconds<=30 or not 0<=a.min_hz<=60:p.error('Use 1–30 seconds and a 0–60 Hz threshold.')
    c=LiveClient(SerialTransport(a.port));original=None;report={'samples':[]}
    try:
        report['hello']=c.hello();initial=c.state();original=c.board();board=decode(original)
        report.update(board=board['title'],duration_seconds=a.seconds,minimum_hz=a.min_hz)
        def ramp(x,group):return dict(kind='ramp',group=group,x=x,y=board['height']-50,u=85 if not group else 25,v=80,value=0)
        cases=[('original',board['objects']),('without_ramps',[o for o in board['objects'] if o['kind']!='ramp']),
               ('one_visible_ramp',[ramp(44,0)]),('two_visible_ramps',[ramp(28,0),ramp(88,1)]),('empty',[])]
        for name,objects in cases:
            c.request('K 0');c.request('Q 1');c.upload(encode({**board,'objects':objects}));c.request('R 12345');c.request('Q 0')
            time.sleep(.2)
            t0=time.monotonic();start=c.state();t1=time.monotonic()
            time.sleep(a.seconds)
            t2=time.monotonic();end=c.state();t3=time.monotonic()
            elapsed=(t2+t3-t0-t1)/2
            sample=dict(case=name,seconds=elapsed,render_hz=(end['frames']-start['frames'])/elapsed,
                        physics_hz=(end['ticks']-start['ticks'])/elapsed,camera=end['camera'])
            report['samples'].append(sample)
            print(f"{name}: render {sample['render_hz']:.2f} Hz, physics {sample['physics_hz']:.2f} Hz",flush=True)
        report['result']='passed' if all(s['physics_hz']>=a.min_hz and s['render_hz']>=a.min_hz for s in report['samples']) else 'failed'
    finally:
        try:
            if original is not None:
                c.request('K 0');c.request('Q 1');c.upload(original);c.request('R');c.request('Q '+str(initial['paused']))
                report['restored_state']=c.state();report['table_restored']=c.board()==original
        finally:
            c.t.close();a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
    if report['result']!='passed':raise SystemExit('FAIL: console update rate below the requested threshold')
    print('PASS: console timing regression checks; original table restored',flush=True)

if __name__=='__main__':main()
