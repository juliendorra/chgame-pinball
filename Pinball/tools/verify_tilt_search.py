#!/usr/bin/env python3
"""Exercise tilted stuck-ball recovery against a real enclosed-wall trap."""
import json
import os
import subprocess
from build_studio import GAME,ROOT,engine_inputs
out=GAME/'out/tilt-search';out.mkdir(parents=True,exist_ok=True)
flags,sources,_=engine_inputs();exe=out/'tilt-checks'
subprocess.run([os.environ.get('CXX','clang++'),*flags,'-fsanitize=undefined,bounds',f'-fsanitize-ignorelist={GAME}/tools/sanitizer.ignore','-fno-sanitize-recover=all',*map(str,sources),str(GAME/'tools/wasm/tilt_checks.cpp'),'-o',str(exe)],check=True,cwd=ROOT)
result=subprocess.check_output([exe],text=True,cwd=ROOT);print(result,end='')
(out/'report.json').write_text(json.dumps(dict(result='passed',checks=result.strip()),indent=2)+'\n')
