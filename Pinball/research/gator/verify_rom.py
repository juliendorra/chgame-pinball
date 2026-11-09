#!/usr/bin/env python3
"""Execute 'Gator's original collision instructions with controlled CPU/RAM inputs.

Requires PyBoy 2.9.0. No ROM bytes are included. The supplied ROM is read-only;
the five-byte CALL/idle trampoline exists only in emulated work RAM.
"""
import argparse
from collections import Counter
import hashlib
import io
import json
import math
from pathlib import Path
from pyboy import PyBoy

ROM_SHA256='d84a2382b358d83a0891d40b2de65494f060d8be1a048d5aa8721282218b04b6'


def signed(n,bits=16):
    return n-(1<<bits) if n&(1<<(bits-1)) else n


def rng_step(state):
    # Independently expressed feedback decoded from ROM0:1037-1056.
    for _ in range(11):
        feedback=1 ^ ((state>>15)&1) ^ (state&1) ^ ((state>>1)&1)
        state=((state<<1)|feedback)&65535
    return state


class Runner:
    def __init__(self,rom):
        self.p=PyBoy(str(rom),window='null',sound_emulated=False,log_level='ERROR',
                     ram_file=io.BytesIO(),rtc_file=io.BytesIO())
        self.p.set_emulation_speed(0)
        self.p.memory[0xff50]=1 # disable boot ROM; no game/UI boot needed
        self.p.memory[0xffff]=0
        self.p.memory[0xff40]=0

    def word(self,addr,value=None):
        if value is not None:
            self.p.memory[addr]=value&255;self.p.memory[addr+1]=(value>>8)&255
        return self.p.memory[addr]|(self.p.memory[addr+1]<<8)

    def run(self,address,*,vx=256,vy=768,mode=0,state=0x1234,force=0,flag=0,x=64*256):
        p=self.p;r=p.register_file
        p.memory[0xc000:0xc005]=[0xcd,address&255,address>>8,0x18,0xfe]
        p.memory[0xff80:0xffff]=[0]*0x7f
        p.memory[0xff50]=1;p.memory[0xffff]=0;p.memory[0xff40]=0
        self.word(0xff8a,x);self.word(0xff8c,100*256)
        self.word(0xff8e,vx);self.word(0xff90,vy)
        self.word(0xffb9,state);self.word(0xffb1,force)
        p.memory[0xffae]=mode;p.memory[0xff98]=flag
        p.memory[0xffce]=0x10 # return at 2c52, without scene/render processing
        p.memory[0xffa2]=0 # upward-facing contact normal; no rotation ambiguity
        r.PC=0xc000;r.SP=0xdffe;r.A=0;r.F=0;r.HL=0x4567
        r.B=(vx>>8)&255;r.C=vx&255;r.D=(vy>>8)&255;r.E=vy&255
        p.tick(1,False,False)
        assert r.PC==0xc003 and r.SP==0xdffe,(hex(r.PC),hex(r.SP))
        return dict(bc=signed((r.B<<8)|r.C),de=signed((r.D<<8)|r.E),
                    vx=signed(self.word(0xff8e)),vy=signed(self.word(0xff90)),
                    x=self.word(0xff8a),y=self.word(0xff8c),rng=self.word(0xffb9),
                    no_collision=p.memory[0xff9a])


def live_trace(rom):
    p=PyBoy(str(rom),window='null',sound_emulated=False,log_level='ERROR',
            ram_file=io.BytesIO(),rtc_file=io.BytesIO())
    p.set_emulation_speed(0);events=[];pending={}
    def before(_):
        if p.memory[0xffae]!=0x80:return
        r=p.register_file
        pending.update(vx=signed((r.B<<8)|r.C),
                       rng=p.memory[0xffb9]|p.memory[0xffba]<<8,
                       x=p.memory[0xff8b],y=p.memory[0xff8d],stage=p.memory[0xffce])
    def delta(_):
        r=p.register_file;d=signed(r.HL)
        state=p.memory[0xffb9]|p.memory[0xffba]<<8
        assert state==rng_step(pending['rng'])
        assert d==signed(state&255,8)>>2
        events.append(dict(pending,delta_q8=d,next_rng=state))
    p.hook_register(0,0x36d0,before,None)
    p.hook_register(0,0x36e6,delta,None)
    p.tick(1200,False,False)
    # Normal controls only; hold long enough for this game's polling cadence.
    for key in ('start','a','start','a','down','a','a'):
        p.button_press(key);p.tick(60,False,False)
        p.button_release(key);p.tick(60,False,False)
    p.stop(save=False)
    assert events,'No natural powered-contact event reached'
    return events


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('rom',type=Path)
    a.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[2]/'out/references/gator')
    args=a.parse_args();raw=args.rom.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==ROM_SHA256,'This mapping is for USA/Europe SHA256 '+ROM_SHA256
    assert len(raw)==65536
    runner=Runner(args.rom);rows=[]
    # These calls execute the original ROM, not a replacement physics routine.
    for state in range(0,65536,61):
        next_state=rng_step(state);delta=signed(next_state&255,8)>>2
        kwargs=dict(state=state,vx=256,vy=768)
        passive=runner.run(0x2c0e,**kwargs)
        assert passive['vx']==256 and passive['vy']==-288 and passive['rng']==state
        powered=runner.run(0x2c0e,mode=0x80,force=256,**kwargs)
        assert powered==runner.run(0x2c0e,mode=0x80,force=256,**kwargs)
        assert powered['vx']==256+delta and powered['vy']==-544 and powered['rng']==next_state
        flipper=runner.run(0x2c0e,mode=0xff,force=256,**kwargs)
        assert flipper['vx']==64 and flipper['vy']==-328 and flipper['rng']==state
        rows.append(dict(seed=state,delta_q8=delta,powered=powered))
    # Ordinary-wall damping flag and separating-contact early exit.
    for flag,numerator in ((0,3),(1,2)):
        r=runner.run(0x3602,vy=768,flag=flag)
        assert r['bc']==256 and r['de']==-768*numerator//8
    r=runner.run(0x3602,vy=-768)
    assert r['bc']==256 and r['de']==-768 and r['no_collision']==255
    # The minimum nonzero X rule is a separate deterministic anti-stall bias.
    for x,want in ((32,32),(100,-32)):
        r=runner.run(0x2c0e,vx=0,mode=0,x=x*256)
        assert r['vx']==want and r['rng']==0x1234
    # Normal-mode gravity and no horizontal drag in this movement routine.
    for vx in (-100,1,100):
        r=runner.run(0x3639,vx=vx,vy=300)
        assert r['vx']==vx and r['vy']==311
        assert r['x']==64*256+vx and r['y']==100*256+311
    runner.p.stop(save=False)
    # Enumerate the decoded 16-bit PRNG mapping, with ROM execution above as oracle.
    mapping=[rng_step(s) for s in range(65536)]
    assert len(set(mapping))==65536
    counts=Counter(signed(s&255,8)>>2 for s in mapping)
    assert set(counts)==set(range(-32,32)) and set(counts.values())=={1024}
    natural=live_trace(args.rom);assert natural==live_trace(args.rom)
    result=dict(rom_sha256=ROM_SHA256,pyboy='2.9.0',result='passed',
        original_rom_collision_cases=len(rows)*4,
        tested_seed_states=len(rows),decoded_rng_states=len(mapping),
        powered_horizontal_delta_q8=[-32,31],powered_horizontal_delta_px=[-32/256,31/256],
        ordinary_wall_randomness='none in verified response path',
        default_normal_restitution='3/8',alternate_normal_restitution='1/4',
        normal_gravity_q8_per_update=11,
        anti_zero_vx='if X velocity is exactly zero, force +32 Q8 left of x=72, otherwise -32 Q8',
        natural_powered_contacts=natural,
        illustrative_angle_bounds_degrees={str(speed):[
            math.degrees(math.atan2(-32/256,speed)),math.degrees(math.atan2(31/256,speed))]
            for speed in (1,2,4)},
        limitations='Collision-focused disassembly and isolated original-code tests, plus a natural-play trace; not a complete semantic decompilation of the entire game.')
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (args.out/'collision-cases.json').write_text(json.dumps(rows,indent=2)+'\n')
    assert hashlib.sha256(args.rom.read_bytes()).hexdigest()==ROM_SHA256
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
