#!/usr/bin/env python3
"""Compare real C++ arrow treatments on the selected short-funnel ramp.

Variants are private renderer/sprite snapshots. Only the selected mouth
profile is applied to the game; an arrow treatment remains a review choice.
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
from sprites import pack, cast_shadow

sys.path.insert(0,str(ROOT/'CHGame/tools/chsim'))
from fbimage import to_image, save_gif


def stamp(base, arrow, x, y):
    rows=[list(r) for r in base]
    for yy,row in enumerate(arrow):
        for xx,c in enumerate(row):
            if c!='.':rows[y+yy][x+xx]=c
    return [''.join(r) for r in rows]


def main():
    work=GAME/'out/ramp-arrow-alternatives';work.mkdir(parents=True,exist_ok=True)
    out=GAME/'docs/ramp-arrow-alternatives';out.mkdir(parents=True,exist_ok=True)
    render=(GAME/'Render.cpp').read_text().replace('    drawRampMarkers();\n','');header=(GAME/'SpriteData.h').read_text()
    profile=[int(n) for n in re.search(r'rampWidths\[19\] PB_SPRITE=\{([^}]+)',render)[1].split(',')]
    assert profile==[6,6,5,4]+[3]*15, 'select short-funnel 04 before comparing arrows'
    current=json.loads((GAME/'sprites/ramp-before-hover.json').read_text())[0]
    floor=[r.replace('c','i') for r in current]
    clear=['.'*15]*17
    compact=['..c..','.ccc.','ccccc','..c..','..c..','..c..']
    hover=['...c...','..ccc..','.ccccc.','ccccccc','..ccc..','..ccc..','..ccc..','..ccc..']
    slim=['.c.','ccc','.c.','.c.','.c.']
    outline=['...c...','..cic..','.ciiic.','cciiicc','..cic..','..cic..','..ccc..']
    designs=[
        dict(name='Previous large',note='Painted on the floor',floor=current),
        dict(name='Compact',note='5 px painted arrow',floor=stamp(floor,compact,5,5)),
        dict(name='Small and higher',note='3 px arrow up the throat',floor=stamp(floor,slim,6,1)),
        dict(name='Hover above',note='Floating over the track',floor=floor,marker=stamp(clear,hover,4,4),x=3,y=-14,bob=True),
        dict(name='Hover beside',note='Keeps clear of the ball',floor=floor,marker=stamp(clear,hover,4,4),x=-14,y=0,bob=True),
        dict(name='Open outline',note='7 px hollow floor arrow',floor=stamp(floor,outline,4,4)),
    ]
    board=json.loads((GAME/'boards/tables.json').read_text())[0]
    board.update(height=480,objects=[dict(kind='ramp',group=2,x=60,y=240,u=90,v=140,value=0)],id=0x52415252)
    boardfile=work/'entry.pbt';boardfile.write_bytes(encode(board))
    probe=work/'capture.cpp'
    probe.write_text('''#include <CHGame.h>
#include "Physics.h"
#include "Render.h"
#include <cstdio>
using namespace pinball;
extern "C" {void pb_init();uint8_t *pb_input();int pb_apply(unsigned);void pb_step(unsigned);}
int main(int argc,char **argv){pb_init();FILE *f=fopen(argv[1],"rb");if(!f)return 2;unsigned n=fread(pb_input(),1,960,f);fclose(f);if(!pb_apply(n))return 3;newGame(12345);
for(unsigned frame=0;frame<150;++frame){if(frame==30)placeBall(0,60,254,0,-500);if(frame)pb_step(0);int camera=game.camera,zoom=game.zoom;game.camera=172;game.zoom=256;drawTable();char path[1024];snprintf(path,sizeof path,"%s/%03u.fb",argv[2],frame);f=fopen(path,"wb");if(!f)return 4;fwrite(gfx_fb,1,GFX_FB_BYTES,f);uint16_t colors[16];for(unsigned i=0;i<16;++i)colors[i]=gfx_paletteOut(i);fwrite(colors,1,sizeof colors,f);fclose(f);game.camera=camera;game.zoom=zoom;const auto &b=game.balls[0];printf("%d %d %d %d %d\\n",b.x,b.y,b.vx,b.vy,b.ramp);}}
''')
    flags,sources,_=engine_inputs(work);compiler=os.environ.get('CXX','clang++')
    objects=[]
    for i,source in enumerate([s for s in sources if s!=GAME/'Render.cpp']+[probe]):
        obj=work/f'common-{i}.o'
        subprocess.run([compiler,*flags,'-c',source,'-o',obj],check=True,cwd=ROOT);objects.append(obj)
    traces=[];animations=[]
    for i,d in enumerate(designs):
        variant=work/str(i);variant.mkdir(exist_ok=True)
        # Metadata anchors remain 15x17, including transparent padding.
        frames=[pack(d['floor'],40,trim=True)]
        if 'marker' in d:frames.append(pack(cast_shadow(d['marker'],[1,2]),40,trim=True))
        data=''.join(f'static const uint8_t ramp_{n}[] PB_SPRITE = {{'+','.join(map(str,b))+'};\n' for n,b in enumerate(frames))
        h=re.sub(r'static const uint8_t ramp_0\[\] PB_SPRITE = .*?(?=static const uint8_t \*const ramp_frames)',lambda _:data,header,count=1,flags=re.S)
        h=re.sub(r'(ramp_frames\[\] PB_SPRITE = )\{[^}]+\}',lambda m:m[1]+'{'+','.join(f'ramp_{n}' for n in range(len(frames)))+'}',h,count=1)
        h=re.sub(r'\{ramp_frames, \d+, 15, 17\}',f'{{ramp_frames, {len(frames)}, 15, 17}}',h,count=1)
        (variant/'SpriteData.h').write_text(h)
        (variant/'ThemeData.h').write_bytes((GAME/'ThemeData.h').read_bytes())
        source=render
        if 'marker' in d:
            marker=f'''    for(unsigned i=0;i<table.h.count;++i)if(table.objects[i].kind==Ramp){{
        const Object &o=table.objects[i];
        static const int8_t bob[]={{0,-1,-2,-1}};
        elementSprite(SPR_RAMP,1,o.x+({d['x']}),sy(o.y+({d['y']})+bob[(game.ticks/10)%4]),CYAN);
    }}
'''
            # A hover marker clears the rails. The physical ball keeps its
            # normal top layer, so a marker cannot conceal a riding ball.
            source=source.replace('    drawBalls(true);',marker+'    drawBalls(true);',1)
        cpp=variant/'Render.cpp';cpp.write_text(source);obj=variant/'render.o';exe=variant/'capture'
        subprocess.run([compiler,*flags,'-c',cpp,'-o',obj],check=True,cwd=ROOT)
        subprocess.run([compiler,*map(str,objects),obj,'-o',exe],check=True,cwd=ROOT)
        trace=subprocess.check_output([exe,boardfile,variant],text=True,cwd=ROOT);traces.append(trace)
        assert trace==traces[0], 'arrow treatment changed real ball physics'
        assert any(line.endswith(' 0') for line in trace.splitlines()), 'ball must enter the ramp'
        native=[to_image((variant/f'{f:03}.fb').read_bytes(),1).convert('RGB').crop((28,35,100,119)) for f in range(150)]
        images=[im.resize((288,336),Image.Resampling.NEAREST) for im in native]
        animations.append(images);durations=[20 if f%3!=1 else 10 for f in range(150)]
        save_gif(images,out/f'{i:02}.gif',durations);images[0].save(out/f'{i:02}.png')
        print(f'{i:02} {d["name"]}: same real ball trace, 150 frames',flush=True)
    sheets=[];font=ImageFont.load_default(size=18);small=ImageFont.load_default(size=13)
    for frame in range(150):
        sheet=Image.new('RGB',(960,768),'#15191f');draw=ImageDraw.Draw(sheet);draw.fontmode='1'
        for i,d in enumerate(designs):
            x=i%3*320;y=i//3*384
            draw.text((x+12,y+5),f'{i:02} {d["name"]}',font=font,fill='white')
            draw.text((x+12,y+28),d['note'],font=small,fill='#bac3cf')
            sheet.paste(animations[i][frame],(x+16,y+48))
        sheets.append(sheet)
    save_gif(sheets,out/'all-six.gif',durations);sheets[0].save(out/'all-six.png')
    report=dict(result='passed',selected_mouth='04 Short funnel',profile=profile,physics_identical=True,frames=150,
                trace_sha256=hashlib.sha256(traces[0].encode()).hexdigest(),
                renderer_sha256=hashlib.sha256(render.encode()).hexdigest(),
                versions=[dict(number=i,**d) for i,d in enumerate(designs)])
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    cards=''.join(f'<article><h2>{i:02} {d["name"]}</h2><p>{d["note"]}</p><img src="{i:02}.gif"></article>' for i,d in enumerate(designs))
    (out/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Ramp arrow comparison</title><style>body{background:#15191f;color:#eee;font:16px system-ui;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}article{background:#222b32;padding:16px;border-radius:12px}img{width:288px;max-width:100%;image-rendering:pixelated}h2{font-size:20px}</style><h1>Arrow treatments on ramp entry 04</h1><p>Actual C++ rendering and ball capture. Same short-funnel entrance, approach, speed and physics. Fixed camera; 30 frames idle, then the ball enters and completes the ramp. 00 is the current arrow. Other treatments are review previews.</p><main>'''+cards+'</main>')
    print(out/'index.html')


if __name__=='__main__':main()
