#!/usr/bin/env python3
"""Install an already validated paired build, then enforce console FPS limits."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

GAME=Path(__file__).resolve().parents[1];ROOT=GAME.parent
sys.path.insert(0,str(ROOT/'CHGame/tools'))
import device


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port');p.add_argument('--debug',action='store_true');p.add_argument('--arduino',action='store_true')
    a=p.parse_args();folder=GAME/'build'/('debug' if a.debug else 'release')
    firmware=folder/'Pinball.ino.bin'
    subprocess.run([sys.executable,GAME/'tools/build_studio.py','--check','--firmware',firmware],check=True,cwd=ROOT)
    manifest=json.loads((GAME/'build/studio/build.json').read_text())
    report={'sourceHash':manifest['sourceHash'],'firmware_sha256':hashlib.sha256(firmware.read_bytes()).hexdigest(),'result':'failed'}
    out=GAME/'out/install-validation';out.mkdir(parents=True,exist_ok=True)
    try:
        device.upload(GAME,folder,a.port,arduino=a.arduino)
        time.sleep(1)
        subprocess.run([sys.executable,GAME/'tools/verify_device_fps.py','--out',out/'fps.json',
                        *(['--port',a.port] if a.port else [])],check=True,cwd=ROOT)
        report['timing']=json.loads((out/'fps.json').read_text());report['result']='passed'
    finally:
        (out/'installed.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: installed paired firmware and physical-console FPS gate.')


if __name__=='__main__':main()
