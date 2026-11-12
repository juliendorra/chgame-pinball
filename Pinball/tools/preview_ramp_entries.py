#!/usr/bin/env python3
"""Render five narrower ramp entries and the previous wide one with real ball motion.

Only the deck-width profile differs; the fixed preview camera keeps the
entry visible. The game, capture physics, sprite and ball speed are shared.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont
from boards import encode
from build_studio import GAME, ROOT, engine_inputs

sys.path.insert(0,str(ROOT/'CHGame/tools/chsim'))
from fbimage import to_image,save_gif


def main():
    work=GAME/'out/ramp-entry-alternatives';work.mkdir(parents=True,exist_ok=True)
    out=GAME/'docs/ramp-entry-alternatives';out.mkdir(parents=True,exist_ok=True)
    render=(GAME/'Render.cpp').read_text()
    pattern=r'(rampWidths\[19\] PB_SPRITE=)\{([^}]+)\}'
    match=re.search(pattern,render);assert match
    current=[int(v) for v in match[2].split(',')]
    designs=[dict(name='Previous wide',profile=[8,8,7,5]),
             dict(name='Slightly narrower',profile=[7,7,6,5]),
             dict(name='Compact mouth',profile=[6,6,6,5]),
             dict(name='Long funnel',profile=[7,7,7,6,5,4]),
             dict(name='Short funnel',profile=[6,6,5,4]),
             dict(name='Quick taper',profile=[7,6,5,4])]
    for d in designs:
        d['profile']+= [3]*(19-len(d['profile']))
        d['selected']=d['profile']==current
    board=json.loads((GAME/'boards/tables.json').read_text())[0]
    board.update(height=480,objects=[dict(kind='ramp',group=2,x=60,y=240,u=90,v=140,value=0)],id=0x52454e54)
    boardfile=work/'entry.pbt';boardfile.write_bytes(encode(board))
    probe=work/'capture.cpp'
    probe.write_text('''#include <CHGame.h>
#include "Physics.h"
#include "Render.h"
#include <cstdio>
using namespace pinball;
extern "C" {void pb_init();uint8_t *pb_input();int pb_apply(unsigned);void pb_step(unsigned);}
int main(int argc,char **argv){pb_init();FILE *f=fopen(argv[1],"rb");if(!f)return 2;unsigned n=fread(pb_input(),1,sizeof(pinball::Table),f);fclose(f);if(!pb_apply(n))return 3;newGame(12345);placeBall(0,60,254,0,-500);
for(unsigned frame=0;frame<60;++frame){if(frame)pb_step(0);int camera=game.camera,zoom=game.zoom;game.camera=172;game.zoom=256;drawTable();char path[1024];snprintf(path,sizeof path,"%s/%02u.fb",argv[2],frame);f=fopen(path,"wb");if(!f)return 4;fwrite(gfx_fb,1,GFX_FB_BYTES,f);uint16_t colors[16];for(unsigned i=0;i<16;++i)colors[i]=gfx_paletteOut(i);fwrite(colors,1,sizeof colors,f);fclose(f);game.camera=camera;game.zoom=zoom;const auto &b=game.balls[0];printf("%d %d %d %d %d\\n",b.x,b.y,b.vx,b.vy,b.ramp);}}
''')
    flags,sources,_=engine_inputs(work);compiler=os.environ.get('CXX','clang++')
    objects=[]
    for i,source in enumerate([s for s in sources if s!=GAME/'Render.cpp']+[probe]):
        obj=work/f'common-{i}.o'
        subprocess.run([compiler,*flags,'-c',source,'-o',obj],check=True,cwd=ROOT);objects.append(obj)
    traces=[];animations=[];font=ImageFont.load_default(size=17)
    sequence=[0]*12+list(range(60))+[59]*6
    durations=[20 if i%3!=1 else 10 for i in range(len(sequence))]
    for i,design in enumerate(designs):
        source=work/f'Render-{i}.cpp';source.write_text(re.sub(pattern,lambda m:m[1]+'{'+','.join(map(str,design['profile']))+'}',render,count=1))
        obj=work/f'render-{i}.o';exe=work/f'capture-{i}';framesdir=work/str(i);framesdir.mkdir(exist_ok=True)
        subprocess.run([compiler,*flags,'-c',source,'-o',obj],check=True,cwd=ROOT)
        subprocess.run([compiler,*map(str,objects),obj,'-o',exe],check=True,cwd=ROOT)
        trace=subprocess.check_output([exe,boardfile,framesdir],text=True,cwd=ROOT);traces.append(trace)
        assert trace==traces[0], 'width preview changed ball physics'
        assert any(line.endswith(' 0') for line in trace.splitlines()), 'ball must actually enter the ramp'
        native=[to_image((framesdir/f'{f:02}.fb').read_bytes(),1).convert('RGB').crop((16,12,112,116)) for f in range(60)]
        frames=[native[f].resize((288,312),Image.Resampling.NEAREST) for f in sequence];animations.append(frames)
        save_gif(frames,out/f'{i:02}.gif',durations);frames[0].save(out/f'{i:02}.png')
        design.update(number=i,deck_width=design['profile'][0]*2+1)
        print(f'Rendered {i}: {design["name"]}, {design["deck_width"]} px deck; same real ball trace',flush=True)
    sheets=[]
    for f in range(len(sequence)):
        sheet=Image.new('RGB',(960,704),'#15191f');draw=ImageDraw.Draw(sheet);draw.fontmode='1'
        for i,d in enumerate(designs):
            x=i%3*320;y=i//3*352
            draw.text((x+10,y+5),f'{i:02} {d["name"]}'+(' *' if d['selected'] else ''),fill='white',font=font)
            draw.text((x+10,y+25),f'{d["deck_width"]} px deck',fill='#bac3cf',font=ImageFont.load_default(size=13))
            sheet.paste(animations[i][f],(x+16,y+40))
        sheets.append(sheet)
    save_gif(sheets,out/'all-six.gif',durations);sheets[0].save(out/'all-six.png')
    cards=''.join(f'<article><h2>{i:02} {d["name"]}'+(' · Selected' if d['selected'] else '')+f'</h2><p>{d["deck_width"]} px deck</p><img src="{i:02}.gif"></article>' for i,d in enumerate(designs))
    (out/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Ramp entry comparison</title><style>body{background:#15191f;color:#eee;font:16px system-ui;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}article{background:#222b32;padding:16px;border-radius:12px}img{width:100%;image-rendering:pixelated}h2{font-size:20px}</style><h1>Previous wide entry and five narrower versions</h1><p>Actual C++ rendering and ball capture. Same approach, physics, speed and entrance sprite. Camera fixed for comparison. Width labels describe the deck, excluding the rails. The selected profile is marked with a star. <a href="../ramp-arrow-alternatives/index.html">Compare arrow treatments.</a></p><main>'''+cards+'</main>')
    (out/'validation.json').write_text(json.dumps(dict(result='passed',physics_identical=True,frames=60,versions=designs,trace_sha256=hashlib.sha256(traces[0].encode()).hexdigest()),indent=2)+'\n')
    print(out/'index.html')


if __name__=='__main__':main()
