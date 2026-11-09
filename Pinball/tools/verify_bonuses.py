#!/usr/bin/env python3
"""Check actual game bonus triggers and export LCD animation frames for review."""
import json
import os
from pathlib import Path
import subprocess
import sys
from build_studio import GAME,ROOT,WORK,engine_inputs
sys.path.insert(0,str(ROOT/'CHGame/tools/chsim'))
from fbimage import to_image

out=GAME/'out/bonuses';out.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
for pattern in ('*.fb','*.png','bonus-preview.gif'):
    for old in out.glob(pattern):old.unlink()
flags,sources,_=engine_inputs();exe=out/'bonus-checks'
subprocess.run([os.environ.get('CXX','clang++'),*flags,'-fsanitize=undefined,bounds',
    f'-fsanitize-ignorelist={GAME}/tools/sanitizer.ignore','-fno-sanitize-recover=all',
    *map(str,sources),str(GAME/'tools/wasm/bonus_checks.cpp'),'-o',str(exe)],check=True,cwd=ROOT)
result=subprocess.check_output([exe,out],text=True,cwd=ROOT);print(result,end='')
for p in out.glob('*.fb'):to_image(p.read_bytes(),4).save(p.with_suffix('.png'))
frames=[to_image(p.read_bytes(),4) for p in sorted(out.glob('animation-*.fb'))]
frames[0].save(out/'bonus-preview.gif',save_all=True,append_images=frames[1:],duration=67,loop=0,disposal=2)
(out/'report.json').write_text(json.dumps(dict(result='passed',checks=result.strip(),screenshots=[p.name for p in sorted(out.glob('*.png'))]),indent=2)+'\n')
