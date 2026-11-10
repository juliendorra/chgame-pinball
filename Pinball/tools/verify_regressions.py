#!/usr/bin/env python3
"""Post-build deterministic plays and drawing-work ceilings for real C++ code.

Host work counters catch excessive drawing calls; only the physical-console
test establishes actual 60 Hz performance. No host milliseconds become MCU FPS.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from boards import encode
from build_studio import GAME, ROOT, WORK, engine_inputs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=GAME/'out/regressions/report.json')
    p.add_argument('--renderer',type=Path,default=GAME/'Render.cpp',help='Alternate renderer for regression reproduction')
    a=p.parse_args();work=WORK/'regressions';work.mkdir(parents=True,exist_ok=True)
    flags,sources,_=engine_inputs(work)
    renderer=work/'Render-budget.cpp'
    renderer.write_text('#include "render_budget.h"\n#define gfx_line budgetLine\n#define gfx_pixel budgetPixel\n#define gfx_hline budgetHline\n#define sprite4 budgetSprite\n'+a.renderer.read_text())
    sources=[renderer if s==GAME/'Render.cpp' else s for s in sources]
    exe=work/'regressions'
    subprocess.run([os.environ.get('CXX','clang++'),*flags,f'-I{GAME}/tools/wasm',
                    '-fsanitize=undefined,bounds',f'-fsanitize-ignorelist={GAME}/tools/sanitizer.ignore',
                    '-fno-sanitize-recover=all',*map(str,sources),str(GAME/'tools/wasm/render_budget.cpp'),'-o',str(exe)],check=True,cwd=ROOT)
    boards=json.loads((GAME/'boards/tables.json').read_text());paths=[]
    for b in boards:
        path=work/(b['file']+'.pbt');path.write_bytes(encode(b));paths.append(path)
    result=subprocess.run([str(exe),*map(str,paths)],capture_output=True,text=True,timeout=180)
    records=[json.loads(line) for line in result.stdout.splitlines()]
    report=dict(result='passed' if result.returncode==0 else 'failed',
                renderer_sha256=hashlib.sha256(a.renderer.read_bytes()).hexdigest(),
                scope='27 perimeter ramp entries and floating-arrow layers; stuck-ball help, filled control triangle, slow rolling, pause, multiball and tilt recovery; 54 seeded plays repeated exactly; all nine layout sweeps at 1x/1.5x; 1/2/3/4/6/8/12 long ramps',
                limits=records[0]['limits'] if records else {},
                limitation='Deterministic API work ceilings, not MCU timing or a human fun score. Run verify_device_fps.py on installed firmware.',
                records=records,error=result.stderr.strip())
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
    if result.returncode:raise SystemExit(result.stderr or 'Regression suite failed')
    print('PASS: post-build plays and drawing budgets: '+json.dumps(records[-1]))


if __name__=='__main__':main()
