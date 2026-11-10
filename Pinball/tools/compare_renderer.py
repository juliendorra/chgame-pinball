#!/usr/bin/env python3
"""Compare exact LCD bytes before/after a renderer optimization, including ramps.

Use --reference with an unchanged copy of Render.cpp; neither executable
communicates with hardware. Both use the current physics, assets and SDK.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess

from boards import encode
from build_studio import GAME, ROOT, WORK, engine_inputs

DRIVER=r'''
#include <CHGame.h>
#include "Physics.h"
#include "Render.h"
#include <cstdio>
#include <cstring>
#include <initializer_list>
using namespace pinball;
extern "C" void pb_init();
extern "C" unsigned char *pb_input();
extern "C" int pb_apply(unsigned);
static unsigned frames;
static void sweep() {
    for(unsigned zoom:{256u,320u,384u})for(int camera=-HEADER_HEIGHT;camera<=table.h.height-108;camera+=7) {
        for(int shake:{-2,0,2})for(unsigned phase=0;phase<4;++phase) {
            newGame(12345);game.camera=camera;game.zoom=zoom;
            game.ticks=camera+HEADER_HEIGHT+phase*31;
            game.shakeX=shake;game.shakeY=-shake;game.shakeTicks=shake?24:0;
            for(auto &b:game.balls)b.active=false;
            if(phase) {
                placeBall(0,56,camera+54,0,0);
                if(phase==2)game.balls[0].ramp=0;
                if(phase==3){game.score=123456;game.scorePopValue=123456;game.scorePopTicks=30;}
            }
            drawTable();fwrite(gfx_fb,1,GFX_FB_BYTES,stdout);++frames;
        }
    }
}
int main(int argc,char **argv) {
    pb_init();
    for(int a=1;a<argc;++a) {
        FILE *f=fopen(argv[a],"rb");if(!f)return 2;
        unsigned n=fread(pb_input(),1,960,f);fclose(f);if(!pb_apply(n))return 3;
        sweep();
    }
    table.h.height=400;
    for(unsigned count:{1u,2u,3u,4u,6u,8u,12u}) {
        table.h.count=count;
        for(unsigned i=0;i<count;++i)table.objects[i]={Ramp,uint8_t(i%3),
            int16_t(18+(i*17)%79),int16_t(230+(i*13)%111),
            int16_t(12+(i*23)%89),int16_t(30+(i*11)%100),1800};
        sweep();
    }
    fprintf(stderr,"Compared %u complete LCD frames\n",frames);
}
'''

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',type=Path,required=True)
    a=p.parse_args();work=WORK/'renderer-comparison';work.mkdir(parents=True,exist_ok=True)
    driver=work/'compare.cpp';driver.write_text(DRIVER)
    flags,sources,_=engine_inputs(work)
    paths=[]
    import json
    for board in json.loads((GAME/'boards/tables.json').read_text()):
        dest=work/(board['file']+'.pbt');dest.write_bytes(encode(board));paths.append(dest)
    images=[]
    for label,renderer in [('before',a.reference.resolve()),('after',GAME/'Render.cpp')]:
        executable=work/label
        current=[renderer if s==GAME/'Render.cpp' else s for s in sources]
        subprocess.run([os.environ.get('CXX','clang++'),*flags,*map(str,current),str(driver),'-o',str(executable)],check=True,cwd=ROOT)
        image=work/(label+'.pixels')
        with image.open('wb') as stream:subprocess.run([str(executable),*map(str,paths)],check=True,stdout=stream)
        images.append(image)
    subprocess.run(['cmp',*map(str,images)],check=True)
    digest=hashlib.file_digest(images[0].open('rb'),'sha256').hexdigest()
    print(f'PASS: {images[0].stat().st_size:,} identical LCD bytes; SHA256 {digest}')

if __name__=='__main__':main()
