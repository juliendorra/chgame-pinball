#!/usr/bin/env python3
"""Exercise the real portable rumble state machine with a controlled clock."""
from pathlib import Path
import os
import shutil
import subprocess

game=Path(__file__).resolve().parents[1]
out=game/'out/rumble';out.mkdir(parents=True,exist_ok=True)
(out/'Arduino.h').write_text('#include <stdint.h>\nuint32_t millis();\n')
(out/'test.cpp').write_text(r'''
#include <cassert>
#include "Rumble.h"
static uint32_t clockMs;
uint32_t millis() { return clockMs; }
int main() {
 using namespace rumble;
 begin(); assert(level()==0 && remaining()==0);
 pulse(180,70); assert(level()==180 && remaining()==70);
 clockMs=69; assert(level()==180 && remaining()==1);
 clockMs=70; assert(level()==0 && remaining()==0);
 pulse(200,65535); assert(remaining()==500);
 clockMs+=500; assert(level()==0);
 pulse(220,80,2); pulse(110,100,1); assert(level()==220 && remaining()==80);
 pulse(120,40,2); assert(level()==120 && remaining()==40);
 setEnabled(false); assert(level()==0); pulse(200,50); assert(level()==0);
 setEnabled(true); pulse(255,40); assert(level()==255); stop(); assert(level()==0);
 pulse(0,40); assert(level()==0); pulse(255,0); assert(level()==0);
 for(unsigned i=0;i<7;++i) { play(Effect(i)); assert(level()>0 && remaining()<=500); clockMs+=501; assert(level()==0); }
 play(Effect(255)); assert(level()==0);
 clockMs=0xfffffff0u; update(); pulse(180,40); clockMs=24; assert(level()==0);
}
''')
cxx=os.environ.get('CHSIM_CXX') or shutil.which('clang++') or shutil.which('c++')
subprocess.run([cxx,'-std=c++17','-DCHSIM','-fsanitize=undefined,bounds','-fno-sanitize-recover=all',
               '-I'+str(out),'-I'+str(game/'src/rumble'),str(out/'test.cpp'),str(game/'src/rumble/Rumble.cpp'),'-o',str(out/'test')],check=True)
subprocess.run([str(out/'test')],check=True)
print('PASS: rumble boot-off, exact expiry, 500 ms cap, priorities, disable, stop, all effects and clock wrap')
