#!/usr/bin/env python3
"""Read-only proof that the running game loaded migrated SD high scores.

Stages zero-score game-over screens, compares their BEST digit pixels with
the shared renderer and the migration report, and checks the journal bytes
are unchanged. Restarts the previous RAM board afterwards. No new firmware.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time

from build_studio import GAME,ROOT,WORK,engine_inputs
sys.path[:0]=[str(GAME/'editor'),str(ROOT/'CHGame/tools/chsim')]
from protocol import LiveClient,encode
from chdrivelib import SerialTransport
from update_cart_live import CartCard

DRIVER=r'''
#include <CHGame.h>
#include "Physics.h"
#include "Render.h"
#include <cstdio>
#include <cstdlib>
extern "C" void pb_init();
extern "C" unsigned char *pb_input();
extern "C" int pb_apply(unsigned);
int main(int argc,char **argv) {
    if(argc!=3)return 2;pb_init();FILE *f=fopen(argv[1],"rb");if(!f)return 3;
    unsigned n=fread(pb_input(),1,960,f);fclose(f);if(!pb_apply(n))return 4;
    pinball::game.score=0;gfx_resetClip();gfx_clear(0);
    pinball::drawGameOver(strtoul(argv[2],nullptr,10));
    fwrite(gfx_fb,1,GFX_FB_BYTES,stdout);
}
'''

def band(frame):
    return b''.join(frame[y*64+4:y*64+60] for y in range(78,97))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port')
    p.add_argument('--migration-report',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();migration=json.loads(a.migration_report.read_text())
    selected=next(s for s in migration['saves'] if s['game']=='Pinball')
    payload=bytes.fromhex(selected['selected']['payload'])
    expected={i:score for i,score in struct.iter_unpack('<II',payload[:192]) if i}
    work=WORK/'score-load';work.mkdir(parents=True,exist_ok=True)
    flags,sources,_=engine_inputs(work);driver=work/'expected.cpp';driver.write_text(DRIVER);exe=work/'expected'
    subprocess.run([os.environ.get('CXX','clang++'),*flags,*map(str,sources),str(driver),'-o',str(exe)],check=True,cwd=ROOT)
    spec=importlib.util.spec_from_file_location('score_prepare',ROOT/'chgame-sd-saves/tools/prepare.py')
    saves=importlib.util.module_from_spec(spec);spec.loader.exec_module(saves)
    client=LiveClient(SerialTransport(a.port));original=None;report={'result':'failed','staged_game_over':True,'checks':[]}
    try:
        report['hello']=client.hello();initial=client.state();original=client.board()
        client.request('K 0');client.request('Q 1');client.request('I');card=CartCard(client)
        journal=card.file(card.path(selected['target'])[2]);saves.validate(journal,selected['id'])
        assert hashlib.sha256(journal).hexdigest()==selected['sha256'],'Migrated journal differs before load check'
        boards=json.loads((GAME/'boards/tables.json').read_text())
        for stem in ('NEON','ORBITRON','PIRATES'):
            board=next(b for b in boards if b['file']==stem);best=expected[board['id']]
            fixture=work/(stem+'.pbt');fixture.write_bytes(encode(board))
            expected_frame=subprocess.check_output([str(exe),str(fixture),str(best)])
            client.upload(encode(board));client.request('R 12345');client.request('Q 0')
            for lives in (3,2,1):
                assert client.state()['lives']==lives
                client.request('P 64,'+str(board['height']-13))
                deadline=time.monotonic()+5
                while client.state()['lives']==lives:
                    if time.monotonic()>deadline:raise RuntimeError('Staged zero-score ball did not drain')
                    time.sleep(.04)
            time.sleep(.05);state=client.state();assert state['score']==state['lives']==0
            frame=bytes.fromhex(client.request('H')[-1].removeprefix('LIVE DATA '))
            assert len(frame)==8192 and band(frame)==band(expected_frame),f'{stem}: BEST pixels do not show migrated score {best}'
            (work/(stem+'-device.pixels')).write_bytes(frame)
            report['checks'].append({'board':stem,'best':best,'lcd_pixels_match':True,'score':0})
            print(f'PASS: {stem} displays migrated BEST {best}; staged score remains zero',flush=True)
        client.request('Q 1');client.request('I');after=CartCard(client)
        assert after.file(after.path(selected['target'])[2])==journal,'Read-only load test changed the journal'
        report.update(result='passed',save_file=selected['target'],save_sha256=selected['sha256'],journal_unchanged=True)
    finally:
        try:
            if original is not None:
                client.request('K 0');client.request('Q 1');client.upload(original);client.request('R');client.request('Q '+str(initial['paused']))
                report['ram_board_restored']=client.board()==original
        finally:
            client.t.close();a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
