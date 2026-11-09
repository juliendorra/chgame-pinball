#!/usr/bin/env python3
"""Build a review gallery of every current popup using the actual C++ renderer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from build_studio import GAME, ROOT, engine_inputs
from boards import encode
sys.path.insert(0,str(ROOT/'CHGame/tools/chsim'))
from fbimage import to_image
from PIL import Image, ImageDraw, ImageFont, ImageSequence

def publish_gallery(source, destination):
    """Keep the review page and lossless native-resolution captures in docs."""
    report=json.loads((source/'layout-checks.json').read_text())
    assert report['renderer_sha256']==hashlib.sha256((GAME/'Render.cpp').read_bytes()).hexdigest(), 'Regenerate stale captures first'
    manifest=json.loads((source/'gallery.json').read_text())
    destination.mkdir(parents=True,exist_ok=True)
    dest=destination/'assets';dest.mkdir(exist_ok=True)
    for theme in manifest['themes']:
        for case in manifest['cases']:
            stem=f"t{theme['id']}-{case['slug']}"
            for suffix in ('.png','-lcd.png'):
                with Image.open(source/'assets'/(stem+suffix)) as image:
                    image=image.convert('RGB')
                    native=image.resize((128,image.height*128//image.width),Image.Resampling.NEAREST)
                    assert native.resize(image.size,Image.Resampling.NEAREST).tobytes()==image.tobytes()
                    native.save(dest/(stem+suffix),optimize=True)
            with Image.open(source/'assets'/(stem+'.gif')) as animation:
                frames=[];durations=[]
                for frame in ImageSequence.Iterator(animation):
                    image=frame.convert('RGB')
                    native=image.resize((128,image.height*128//image.width),Image.Resampling.NEAREST)
                    assert native.resize(image.size,Image.Resampling.NEAREST).tobytes()==image.tobytes()
                    frames.append(native);durations.append(frame.info.get('duration',100))
                frames[0].save(dest/(stem+'.gif'),save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2,optimize=True)
    page=(GAME/'tools/popup-gallery/index.html').read_text()
    # Embed metadata so the preserved page also works when opened as a file.
    data=json.dumps(manifest,separators=(',',':')).replace('<',r'\u003c')
    page=page.replace("const data=await(await fetch('gallery.json')).json();",'const data='+data+';')
    (destination/'index.html').write_text(page)
    for name in ('gallery.json','layout-checks.json'):(destination/name).write_bytes((source/name).read_bytes())
    (destination/'README.md').write_text(f"# Captured Pinball messages\n\nOpen `index.html`, or serve this directory as a static site. The page includes all {len(manifest['cases'])} captured states in nine themes, their animations, and full LCD images.\n\nThese are actual C++ renderer captures at the native LCD resolution; CSS enlarges pixels without smoothing. Captures are stored losslessly at native resolution to avoid committing enlarged duplicates.\n\nRegenerate after changing game messages:\n\n```sh\npython3 Pinball/tools/preview_popups.py\npython3 Pinball/tools/preview_popups.py --publish-only\n```\n\n`--check-layout` runs the margin, target-sprite gap, and score-caption padding regressions without regenerating the images. `layout-checks.json` records the checked renderer hash.\n")
    print(f'Preserved {len(manifest["cases"])*len(manifest["themes"])} captured states in {destination}')

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--publish-only',action='store_true',help='Preserve current verified captures under docs/popups without rerendering')
parser.add_argument('--check-layout',action='store_true',help='Check every layout without regenerating images')
args=parser.parse_args()
OUT=GAME/'out/popup-gallery'
OUT.mkdir(parents=True,exist_ok=True)
if args.publish_only:
    publish_gallery(OUT,GAME/'docs/popups')
    raise SystemExit(0)
frames_dir=OUT/'frames';frames_dir.mkdir(exist_ok=True)
assets=OUT/'assets';assets.mkdir(exist_ok=True)
boards=json.loads((GAME/'boards/tables.json').read_text())
for b in boards:(OUT/f'theme-{b["theme"]}.pbt').write_bytes(encode(b))
cases=[]
def add(slug,title,group,description,bonus=0,arg=0,mask=0,mult=1,mode=0,value=0,kind=0,overview=False,view=0,footer=""):
    cases.append(dict(slug=slug,title=title,group=group,description=description,bonus=bonus,arg=arg,mask=mask,mult=mult,mode=mode,value=value,kind=kind,overview=overview,view=view,footer=footer))
add('saucer','SAUCER BONUS','Bonuses','Saucer capture · KEEP GOING!',bonus=1,overview=True)
add('kickback','KICKBACK!','Bonuses','Outlane rescue · BALL SAVED',bonus=2,overview=True)
add('double','DOUBLE SCORE!','Bonuses','Single-ball scoop · BIG POINTS!',bonus=4,mode=600,overview=True)
add('ready','MULTIBALL READY','Bonuses','All three target banks lit · SHOOT SCOOP!',bonus=5,overview=True)
add('multiball','MULTIBALL!','Bonuses','Three balls released · 3 BALLS!',bonus=6,mode=1800,overview=True)
add('jackpot','SUPER JACKPOT!','Bonuses','Scoop during multiball scoring window · BIG POINTS!',bonus=8,mode=600,overview=True)
add('stuck','BALL STUCK!','Help','▶ OR A SHAKE · console button order; remains until the stalled ball moves.',bonus=9,overview=True)
for seconds,why in [(4,'Saucer'),(6,'Lane set'),(8,'Launch'),(10,'Multiball')]:
    add(f'save-{seconds}',f'BALL SAVE · {seconds} seconds','Bonuses',why,bonus=7,arg=seconds,overview=True)
for effective in (2,3,4,5,6,8,10):
    base=effective if effective<=5 else effective//2
    add(f'multiplier-{effective}',f'BONUS UP! · ×{effective}','Multipliers','Lane-set award; double scoring stacks with the base multiplier.',bonus=3,arg=effective,mult=base,mode=600 if effective>5 else 0,overview=effective==2)
for mask in range(7):
    missing=' + '.join(chr(65+g) for g in range(3) if not mask&(1<<g))
    add(f'lanes-{mask}',f'Light {missing}','Lane mission','Missing lamps and their letters; next reward ×2.',bonus=3,arg=128|mask,mask=mask,overview=mask in (0,1,3))
for effective in (3,4,5,6,8,10):
    base=effective-1 if effective<=5 else effective//2-1
    add(f'goal-{effective}',f'Lane goal · ×{effective}','Lane mission','Next effective multiplier, including an active double-score window.',bonus=3,arg=128,mult=base,mode=600 if effective>5 else 0)
for mask in (0,1,3):
    add(f'lanes-save-{mask}','Lane goal · BALL SAVE','Lane mission','At the ×5 base cap, lane sets still grant a ball-save window.',bonus=3,arg=128|mask,mask=mask,mult=5,overview=mask==3)
source=(GAME/'Physics.cpp').read_text()
for array,kind,label in [('milestones',1,'Score milestones'),('lucky',2,'Lucky scores')]:
    block=re.search(rf'{array}\[\]\s*=\s*\{{([^}}]+)\}}',source).group(1)
    for raw in block.split(','):
        value=int(raw.strip());add(f'score-{kind}-{value}',f'{value:,}',label,'SCORE MILESTONE!' if kind==1 else 'LUCKY SCORE!',value=value,kind=kind,overview=value in (5000,7777))
for view,title in [(1,'PAUSE · Sound on'),(2,'PAUSE · Sound off'),(3,'GAME OVER'),(4,'SHAKE · 2/3'),(5,'DANGER · 3/3'),(6,'TILT')]:
    add(f'overlay-{view}',title,'Other overlays','Existing game overlay or persistent shake/tilt alert.',view=view,overview=view in (1,3,6))
add('gameover-max','GAME OVER · 8-digit scores','Other overlays','Large themed score digits and controls, including the eight-digit maximum.',view=3,value=99999999)
# Include the short alerts too, even though these use the footer rather than
# the large popup band. Read their wording directly from the live sources.
alerts=[]
for file in ('Physics.cpp','Pinball.ino'):
    text=(GAME/file).read_text()
    for match in re.finditer(r'announce\((.*?)\);',text,re.S):
        if text[max(0,match.start()-5):match.start()]=='void ':continue
        for message in re.findall(r'"([^"\n]+)"',match.group(1)):
            if message not in alerts:alerts.append(message)
for i,message in enumerate(alerts):
    add(f'footer-{i}',message,'Footer alerts','Short status message shown at the bottom of the LCD.',view=7,footer=message)
(OUT/'cases.txt').write_text(''.join(' '.join(str(c[k]) for k in ('slug','bonus','arg','mask','mult','mode','value','kind','view'))+' '+c['footer']+'\n' for c in cases))
flags,sources,_=engine_inputs();exe=OUT/'popup-preview'
probe=OUT/'Render-probed.cpp'
probe.write_text('#include "popup_layout_probe.h"\n#define text35x2 checkedPopupText\n#define sprite4 checkedPopupSprite\n'+(GAME/'Render.cpp').read_text())
flags.append(f'-I{GAME}/tools/wasm')
sources=[probe if p==GAME/'Render.cpp' else p for p in sources]
sources.append(GAME/'tools/wasm/popup_layout_probe.cpp')
subprocess.run([os.environ.get('CXX','clang++'),*flags,'-fsanitize=undefined,bounds',f'-fsanitize-ignorelist={GAME}/tools/sanitizer.ignore','-fno-sanitize-recover=all',*map(str,sources),str(GAME/'tools/wasm/popup_preview.cpp'),'-o',str(exe)],check=True,cwd=ROOT)
result=subprocess.check_output([exe,OUT/'cases.txt',OUT,'-' if args.check_layout else frames_dir],text=True,cwd=ROOT)
print(result,end='',flush=True)
(OUT/'layout-checks.json').write_text(json.dumps(dict(result='passed',checks=result.strip(),renderer_sha256=hashlib.sha256((GAME/'Render.cpp').read_bytes()).hexdigest(),themes=len(boards),cases=len(cases),frames_per_case=12),indent=2)+'\n')
if args.check_layout:raise SystemExit(0)
for b in boards:
    theme=b['theme']
    for c in cases:
        name=f't{theme}-{c["slug"]}'
        frames=[to_image((frames_dir/f'{name}-{f:02}.fb').read_bytes(),1).convert('RGB') for f in range(12)]
        chosen=frames[4 if c['bonus'] else 5]
        rect=(0,116,128,128) if c['view']>=4 else (0,0,128,128) if c['view'] else (0,0,128,58)
        chosen.crop(rect).save(assets/f'{name}.png')
        chosen.resize((512,512),Image.Resampling.NEAREST).save(assets/f'{name}-lcd.png')
        crops=[f.crop(rect).resize((512,(rect[3]-rect[1])*4),Image.Resampling.NEAREST) for f in frames]
        duration=(84 if c['bonus'] or c['view'] else 36)/60*1000/12
        crops[0].save(assets/f'{name}.gif',save_all=True,append_images=crops[1:],duration=round(duration),loop=0,disposal=2)
    print(f'Rendered {b["title"]}: {len(cases)} popups',flush=True)
for p in frames_dir.glob('*.fb'):p.unlink()
# Contact sheets are layouts of exact framebuffer captures, not redrawn mockups.
font_path='/System/Library/Fonts/Supplemental/Arial.ttf'
font=ImageFont.truetype(font_path,16)
small=ImageFont.truetype(font_path,12)
def sheet(name,items,title):
    w=280;h=286 if any(c['view']==3 for c in items) else 158
    im=Image.new('RGB',(w*3+32,70+h*((len(items)+2)//3)), '#10121b');d=ImageDraw.Draw(im)
    d.text((16,15),title,font=font,fill='#ffffff');d.text((16,40),'Actual game renderer · Neon Pursuit · click the gallery to animate',font=small,fill='#9da6b9')
    for i,c in enumerate(items):
        x=16+(i%3)*w;y=70+(i//3)*h
        d.text((x,y),c['title'],font=font,fill='#ffffff')
        pic=Image.open(assets/f't0-{c["slug"]}.png')
        if c['view'] in (1,2):pic=pic.crop((0,28,128,86))
        elif c['view']==3:pic=pic.crop((0,12,128,128))
        pic=pic.resize((256,pic.height*2),Image.Resampling.NEAREST)
        im.paste(pic,(x,y+24+(h-42-pic.height)//2))
    im.save(OUT/name)
sheet('all-types.png',[c for c in cases if c['overview']],'Every popup layout: bonuses, lane goals and scores')
sheet('all-score-values.png',[c for c in cases if c['kind']],'All score milestones and lucky numbers')
manifest=dict(themes=[dict(id=b['theme'],title=b['title']) for b in boards],cases=cases,renderer='Actual Pinball C++ drawTable(), scripted presentation states; no hand-drawn UI replicas',frames_per_popup=12)
(OUT/'gallery.json').write_text(json.dumps(manifest,indent=2)+'\n')
page=(GAME/'tools/popup-gallery/index.html').read_text()
(OUT/'index.html').write_text(page)
print(f'Gallery: {OUT}/index.html · {len(cases)} variants × {len(boards)} themes')
