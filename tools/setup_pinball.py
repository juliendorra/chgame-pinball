#!/usr/bin/env python3
"""Set up the standalone firmware toolchain; web builds need no board package."""
from pathlib import Path
import platform
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
def run(*args):subprocess.run(list(map(str,args)),cwd=ROOT,check=True)
if sys.argv[1:2]==['native-toolchain']:
    run(sys.executable,ROOT/'tools/build_current_gcc.py','--activate',*sys.argv[2:])
else:
    for name in ('git','uv','arduino-cli'):
        if not shutil.which(name):raise SystemExit(f'Install {name} and add it to PATH first.')
    if not (ROOT/'.venv/bin/python').exists():run('uv','venv','--python',sys.executable,ROOT/'.venv')
    run('uv','pip','install','--python',ROOT/'.venv/bin/python','-r',ROOT/'requirements.txt')
    run('arduino-cli','core','update-index')
    run('arduino-cli','core','install','CHGame:ch32v@0.3.0')
    if platform.system()=='Darwin' and platform.machine()=='arm64':
        run(sys.executable,ROOT/'tools/build_current_gcc.py','--activate')
