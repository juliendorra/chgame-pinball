#!/usr/bin/env python3
"""Compare the previous flipper and ten designs through the game's pose generator.

Does not change the shipping sprite or collision masks.
"""
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont
from sprites import flipper_pose, INK

GAME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GAME.parent / 'CHGame/tools/chsim'))
from fbimage import save_gif


def unpack(data):
    w, h = data[:2]
    image = Image.new('P', (w, h), 15)
    at = 2
    for y in range(h):
        count = data[at]; at += 1
        x = 0
        for run in data[at:at + count]:
            for _ in range((run >> 4) + 1):
                image.putpixel((x, y), run & 15); x += 1
        at += count
    return image


def main():
    designs = json.loads((GAME / 'sprites/flipper-alternatives.json').read_text())
    assert len(designs) == 10
    previous = json.loads((GAME / 'sprites/flipper-previous.json').read_text())['frames']
    active = json.loads((GAME / 'sprites/element_sprites.json').read_text())['flipper']
    assert active==designs[9]['frames'], 'design 10 is the active game flipper'
    designs.insert(0,dict(name='Previous',description='The earlier game sprite, preserved as the reference. Design 10 is now active.',frames=previous))
    config = json.loads((GAME / 'sprites/flipper.json').read_text())
    theme = json.loads((GAME / 'boards/tables.json').read_text())[0]
    palette = [tuple(int(c, 16) * 17 for c in rgb) for rgb in theme['palette']]
    palette[2] = tuple((int(c, 16) >> 1) * 17 for c in theme['palette'][0])
    out = GAME / 'docs/flipper-alternatives'; out.mkdir(parents=True, exist_ok=True)
    # Actual button response: +72/frame on press, -56/frame on release.
    levels = [0] * 18 + [72, 144, 216, 255] + [255] * 12 + [199, 143, 87, 31, 0] + [0] * 18
    poses = [(v * 8 + 127) // 255 for v in levels]
    # GIF centiseconds approximate a 60 Hz clock without speeding the stroke up.
    durations = [20 if i % 3 != 1 else 10 for i in range(len(poses))]
    all_frames = []
    for number, design in enumerate(designs):
        rows = design['frames'][0]
        assert len(rows) == 13 and all(len(row) == 32 for row in rows)
        opaque = {(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c != '.'}
        if number:
            assert opaque == {(x, 12-y) for x, y in opaque}, 'balanced alternative silhouette'
        assert all(c in INK for row in rows for c in row)
        for pose in range(9):
            angle=config['rest_angle']+pose*(config['raised_angle']-config['rest_angle'])/8
            masks=[]
            for side in range(2):
                data,ax,ay,_=flipper_pose(rows,angle,side,None,config['pivot'])
                sprite=unpack(data)
                masks.append({(x-ax,y-ay) for y in range(sprite.height) for x in range(sprite.width) if sprite.getpixel((x,y))!=15})
            assert masks[1]=={(-x,y) for x,y in masks[0]}, 'mirrored collision silhouettes'
        frames = []
        for pose in poses:
            angle = config['rest_angle'] + pose * (config['raised_angle'] - config['rest_angle']) / 8
            image = Image.new('RGB', (128, 64), palette[0])
            draw = ImageDraw.Draw(image)
            # Same playfield palette; guide context stays behind moving bats.
            for x, end in [(18,30),(100,94)]:
                draw.line([(x+2,4),(x+2,24),(end+2,39)], fill=palette[2], width=5)
                draw.line([(x,1),(x,21),(end,36)], fill=palette[3], width=3)
                draw.line([(x-1,1),(x-1,21),(end-1,36)], fill=palette[14], width=1)
            for side, pivot_x in enumerate((30, 94)):
                data, ax, ay, _ = flipper_pose(rows, angle, side, [2, 3], config['pivot'])
                sprite = unpack(data)
                for y in range(sprite.height):
                    for x in range(sprite.width):
                        ink = sprite.getpixel((x,y))
                        px, py = pivot_x-ax+x, 36-ay+y
                        if ink != 15 and 0 <= px < 128 and 0 <= py < 64:
                            image.putpixel((px,py), palette[ink])
            frames.append(image)
        all_frames.append(frames)
        save_gif([f.resize((512,256),Image.Resampling.NEAREST) for f in frames],
                 out / f'{number:02}.gif', durations)
        frames[0].resize((512,256),Image.Resampling.NEAREST).save(out / f'{number:02}.png')
    sheets = []; comparisons = []
    for frame in range(len(poses)):
        sheet = Image.new('RGB', (768, 1120), '#15191f'); draw = ImageDraw.Draw(sheet); draw.fontmode='1'
        for i, design in enumerate(designs[1:]):
            x, y = (i % 2) * 384, (i // 2) * 224
            draw.text((x+12,y+5), f'{i+1:02}  {design["name"]}', fill='white',font=ImageFont.load_default(size=17))
            sheet.paste(all_frames[i+1][frame].resize((384,192),Image.Resampling.NEAREST),(x,y+28))
        sheets.append(sheet)
        comparison=Image.new('RGB',(768,1344),'#15191f')
        reference=ImageDraw.Draw(comparison);reference.fontmode='1'
        reference.text((204,5),'00  Previous',fill='white',font=ImageFont.load_default(size=17))
        comparison.paste(all_frames[0][frame].resize((384,192),Image.Resampling.NEAREST),(192,28))
        comparison.paste(sheet,(0,224));comparisons.append(comparison)
    save_gif(sheets, out/'all-ten.gif', durations)
    sheets[0].save(out/'all-ten.png')
    save_gif(comparisons,out/'comparison.gif',durations)
    comparisons[0].save(out/'comparison.png')
    pair=[]
    for frame in range(len(poses)):
        image=Image.new('RGB',(768,552),'#15191f');draw=ImageDraw.Draw(image);draw.fontmode='1'
        for col,(number,label) in enumerate([(0,'00 Previous'),(10,'10 Active: Full curved bat')]):
            x=col*384;native=all_frames[number][frame]
            draw.text((x+16,8),label,fill='white',font=ImageFont.load_default(size=18))
            image.paste(native.resize((384,192),Image.Resampling.NEAREST),(x,36))
            draw.text((x+16,240),'Same left flipper, enlarged',fill='#b8c4ce',font=ImageFont.load_default(size=14))
            image.paste(native.crop((23,13,65,48)).resize((336,280),Image.Resampling.NEAREST),(x+24,266))
        pair.append(image)
    save_gif(pair,out/'current-vs-10.gif',durations);pair[0].save(out/'current-vs-10.png')
    cards = ''.join(f'<article><h2>{i:02} · {d["name"]}</h2><img src="{i:02}.gif"><p>{d["description"]}</p></article>' for i,d in enumerate(designs))
    (out/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Flipper comparison: design 10 selected</title>
<style>body{background:#15191f;color:#eee;font:16px system-ui;margin:24px;max-width:1100px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}article{background:#222b32;padding:16px;border-radius:12px}h2{font-size:20px}img{width:100%;image-rendering:pixelated}p{line-height:1.5}</style>
<h1>Flipper comparison: design 10 selected</h1><p>10, Full curved bat, is now the active game sprite. 00 preserves the previous design; 01–10 have balanced source outlines. All use the same palette, pivot, press/release timing, pose generator and board-tinted shadows.</p><main>'''+cards+'</main>')
    print(f'Reviewed previous sprite and ten designs, 198 generated poses: {out / "index.html"}')


if __name__ == '__main__':
    main()
