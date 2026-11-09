#!/usr/bin/env python3
"""Compare real flipper collisions with independently rasterized visible art."""
import json
import math
import os
from pathlib import Path
import sys

GAME = Path(__file__).resolve().parents[1]
ROOT = GAME.parent
sys.path.insert(0,str(ROOT/'CHGame/tools/chsim'))
sys.path.insert(0,str(GAME/'tools'))
from sim_build import build
from chdrivelib import Driver,SimTransport
from sprites import flipper_pose,convex_hull


def decode(data):
    out=set();at=2
    for y in range(data[1]):
        n=data[at];at+=1;x=0
        for run in data[at:at+n]:
            width=(run>>4)+1
            if run&15 != 15:
                out.update((xx,y) for xx in range(x,x+width))
            x+=width
        at+=n
    return out


def distance(point,spans):
    x,y=point
    return math.sqrt(min(max(a-.5-x,0,x-b-.5)**2+max(abs(y-row)-.5,0)**2 for a,b,row in spans))


def main():
    os.environ['CHSIM_FLAGS']=(f'-fsanitize=undefined,bounds -fsanitize-ignorelist={GAME / "tools/sanitizer.ignore"} '
                               '-fno-sanitize-recover=all -fno-omit-frame-pointer')
    out=GAME/'out/verify';out.mkdir(parents=True,exist_ok=True)
    t=SimTransport(build(GAME,out=out/'sim-flippers'));d=Driver(t,'MPIN')
    art=json.loads((GAME/'sprites/element_sprites.json').read_text())['flipper'][0]
    spec=json.loads((GAME/'sprites/flipper.json').read_text())
    count=0;largest_error=0;worst=None
    def state():
        return {k:int(v) for k,v in (s.split('=') for s in d.query('V','PIN ').split()[1:])}
    def probe(side,level,old,length,x,y,vx,vy):
        qx,qy=round(x*256),round(y*256)
        d.cmd(f'I {side},{level},{old},{length},{qx},{qy},{vx},{vy}')
        s=state()
        return s,((s['xq']-64*256)/256,(s['yq']-200*256)/256),(qx/256,qy/256)
    try:
        d.handshake();d.frames(1);d.cmd('F 0')
        for side in range(2):
            for pose in range(9):
                level=round(pose*255/8)
                angle=spec['rest_angle']+pose*(spec['raised_angle']-spec['rest_angle'])/8
                data,ax,ay,_=flipper_pose(art,angle,side,None,spec['pivot'])
                opaque=decode(data)
                for length in range(16,27):
                    scale=length*256//23
                    pixels=set()
                    for x,y in opaque:
                        for xx in range(x*scale//256,(x+1)*scale//256):
                            for yy in range(y*scale//256,(y+1)*scale//256):
                                pixels.add((xx-ax*scale//256,yy-ay*scale//256))
                    outline=convex_hull((2*x+i,2*y+j) for x,y in pixels for i in (-1,1) for j in (-1,1))
                    spans=[]
                    for row in sorted({y for x,y in pixels}):
                        xs=sorted(x for x,y in pixels if y==row);a=last=xs[0]
                        for x in xs[1:]:
                            if x!=last+1:spans.append((a,last,row));a=x
                            last=x
                        spans.append((a,last,row))
                    for a,b in zip(outline,outline[1:]+outline[:1]):
                        dx,dy=b[0]-a[0],b[1]-a[1];norm=math.hypot(dx,dy)
                        nx,ny=dy/norm,-dx/norm
                        mx,my=(a[0]+b[0])/4,(a[1]+b[1])/4
                        vx,vy=round(-nx*700),round(-ny*700)
                        def at_gap(gap):
                            lo,hi=0.,8.
                            for _ in range(18):
                                mid=(lo+hi)/2
                                if distance((mx+nx*mid,my+ny*mid),spans)<gap:lo=mid
                                else:hi=mid
                            return mx+nx*hi,my+ny*hi
                        # A clear miss less than one pixel outside the ball's
                        # true radius may not bounce off an invisible bat.
                        x,y=at_gap(4.9);s,p,initial=probe(side,level,level,length,x,y,vx,vy)
                        assert p==initial and (s['vx'],s['vy'])==(vx,vy),('false contact',side,pose,length,a,b,p,initial)
                        # A visible overlap must resolve to the rubber face.
                        x,y=at_gap(3.1);s,p,initial=probe(side,level,level,length,x,y,vx,vy)
                        assert p!=initial,('missed overlap',side,pose,length,a,b,p)
                        gap=distance(p,spans);error=abs(gap-4)
                        if error>largest_error:largest_error=error;worst=(side,pose,length,p,gap)
                        assert error<.5,('contact disagrees with visible art',side,pose,length,p,gap)
                        count+=2
        # A full fast stroke must hit a stationary ball it sweeps across.
        for side in range(2):
            x=-18 if side else 18
            s,p,_=probe(side,255,0,23,x,-1,0,100)
            assert s['vy'] < -1000,('swept flipper missed ball',side,s)
        report={'result':'passed','cases':count,'sizes':list(range(16,27)),'poses_per_side':9,
                'maximum_visual_contact_error_pixels':round(largest_error,4),'worst_case':worst,
                'method':'Real isolated engine collisions compared to opaque pixel squares, excluding shadows; each boundary edge checked for near miss and overlap; both sides and all allowed SD flipper sizes.'}
        (out/'flipper-collision.json').write_text(json.dumps(report,indent=2)+'\n')
        print(f'PASS: {count} visible-art collision probes, both sides, all nine poses and all eleven sizes; maximum visible contact error {largest_error:.3f}px')
    finally:
        assert t.close()==0,t.bugs


if __name__=='__main__':main()
