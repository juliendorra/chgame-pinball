#!/usr/bin/env python3
"""Measure real ramp-render cost at fixed cameras, then restore the RAM board.

No SD files are changed. The original board is restored and its game restarted.
Paused samples isolate rendering (the same pause panel is included in every
sample). Active samples also measure physics and the ordinary follow camera.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time

GAME=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(GAME/'editor'),str(GAME.parent/'CHGame/tools/chsim')]
from protocol import LiveClient,encode
from chdrivelib import SerialTransport

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--port');p.add_argument('--seconds',type=float,default=1.5)
 p.add_argument('--stress-ramps',type=int,nargs='*',default=[4,6,8,12],help='Additional crowded rendering fixtures (not playable layout proposals)')
 p.add_argument('--min-active-hz',type=float,help='Fail if an original user board falls below this active render/physics rate; stress layouts remain informational')
 p.add_argument('--active-only',action='store_true',help='Skip paused camera sweeps for a focused post-upload gameplay gate')
 p.add_argument('--out',type=Path,required=True);p.add_argument('--label',default='baseline')
 a=p.parse_args();assert 1<=a.seconds<=10
 assert all(3<n<=56 for n in a.stress_ramps),'stress fixtures support 4..56 ramps'
 assert a.min_active_hz is None or 0<=a.min_active_hz<=60
 specs=json.loads((GAME/'boards/tables.json').read_text())
 c=LiveClient(SerialTransport(a.port));original=None
 report={'label':a.label,'renderer_sha256':hashlib.sha256((GAME/'Render.cpp').read_bytes()).hexdigest(),'seconds':a.seconds,'samples':[],'result':'running'}
 try:
  report['hello']=c.hello();initial=c.state();original=c.board()
  def measure(board,variant,camera,active=False):
   t0=time.monotonic();start=c.state();t1=time.monotonic();time.sleep(a.seconds)
   t2=time.monotonic();end=c.state();t3=time.monotonic();elapsed=(t2+t3-t0-t1)/2
   s={'board':board['file'],'variant':variant,'camera':camera,'active':active,'render_hz':(end['frames']-start['frames'])/elapsed,'physics_hz':(end['ticks']-start['ticks'])/elapsed,'camera_start':start['camera'],'camera_end':end['camera']}
   report['samples'].append(s)
   print(f"{s['board']:8} {variant:12} camera={camera:4} {'play' if active else 'render'} {s['render_hz']:6.2f} Hz, physics {s['physics_hz']:6.2f}",flush=True)
  for stem in ('ORBITRON','PIRATES'):
   b=next(b for b in specs if b['file']==stem);ramps=[o for o in b['objects'] if o['kind']=='ramp'];others=[o for o in b['objects'] if o['kind']!='ramp']
   variants=[('none',[]),('original',ramps)]
   if len(ramps)==3:variants += [('first_two',ramps[:2])]+[('only_'+str(i+1),[r]) for i,r in enumerate(ramps)]
   if stem=='ORBITRON':
    for count in a.stress_ramps:
     # Keep the ordinary objects. Spread valid ramps across both sides,
     # deliberately overlapping to measure worst-case overdraw as well as
     # curves outside the viewport. Never save these stress boards to SD.
     parts=copy.deepcopy(ramps)
     for i in range(count-len(parts)):
      parts.append({'kind':'ramp','x':18+(i*17)%79,'y':230+(i*13)%111,
                    'u':12+(i*23)%89,'v':30+(i*11)%100,'group':i%2,'value':1800})
     variants.append(('stress_'+str(count),parts))
   cameras=[-24,40,140,230,b['height']-108]
   for name,parts in ([] if a.active_only else variants):
    fixture=copy.deepcopy(b);fixture['objects']=others+parts
    c.request('K 0');c.upload(encode(fixture));c.request('R 19088743');c.request('Q 1')
    for camera in cameras:
     c.request('M '+str(camera));time.sleep(.06);measure(b,name,camera)
   # Same seed and input through the ordinary gameplay clock; not a paused
   # render benchmark and not an estimate of human fun.
   active_variants=[('original',ramps),('first_two',ramps[:2])]
   if stem=='ORBITRON':active_variants += [(name,parts) for name,parts in variants if name.startswith('stress_')]
   for name,parts in active_variants:
    if name=='first_two' and len(ramps)<3:continue
    fixture=copy.deepcopy(b);fixture['objects']=others+parts;c.upload(encode(fixture));c.request('R 19088743');c.request('Q 0');c.request('K 8');time.sleep(.05);c.request('K 0');time.sleep(.1)
    measure(b,name,-999,True)
  originals=[s for s in report['samples'] if s['active'] and s['variant']=='original']
  report['minimum_active_hz']=a.min_active_hz
  report['result']='measured' if a.min_active_hz is None else 'passed' if all(min(s['render_hz'],s['physics_hz'])>=a.min_active_hz for s in originals) else 'failed'
 finally:
  try:
   if original is not None:
    c.request('K 0');c.request('Q 1');c.upload(original);c.request('R');c.request('Q '+str(initial['paused']));report['board_restored']=c.board()==original
  finally:c.t.close();a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
 if report['result']=='failed':raise SystemExit('FAIL: an original user board missed the configured active FPS limit')
if __name__=='__main__':main()
