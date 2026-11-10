#!/usr/bin/env python3
"""Capture the real engine's ramp entry and four preview-only zoom timings.

Uses a staged single-ramp board to isolate the mouth and camera. All camera
variants must produce identical ball states for the entire crossing.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont
from boards import encode
from build_studio import GAME, ROOT, engine_inputs

sys.path.insert(0, str(ROOT / 'CHGame/tools/chsim'))
from fbimage import to_image, save_gif


def main():
    work = GAME / 'out/ramp-zoom-delays'
    out = GAME / 'docs/ramp-zoom-delays'
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    board = json.loads((GAME / 'boards/tables.json').read_text())[0]
    board.update(height=480, objects=[dict(kind='ramp', group=2, x=60, y=287,
                                        u=94, v=61, value=2500)], id=0x525a4f4d)
    boardfile = work / 'staged.pbt'
    boardfile.write_bytes(encode(board))
    probe = work / 'capture.cpp'
    probe.write_text(r'''#include <CHGame.h>
#include "Physics.h"
#include "Render.h"
#include <cstdio>
#include <cstdlib>
using namespace pinball;
extern "C" {void pb_init();uint8_t *pb_input();int pb_apply(unsigned);void pb_step(unsigned);}
int main(int argc,char **argv){
    pb_init();FILE *f=fopen(argv[1],"rb");if(!f)return 2;
    unsigned n=fread(pb_input(),1,960,f);fclose(f);if(!pb_apply(n))return 3;
    newGame(12345);bool diagonal=atoi(argv[3]);
    placeBall(0,diagonal?51:60,diagonal?301:313,diagonal?350:0,-500);
    game.camera=225;
    for(unsigned frame=0;frame<165;++frame){
        if(frame)pb_step(0);
        int camera=game.camera,zoom=game.zoom;
        if(diagonal){game.camera=230;game.zoom=256;}
        drawTable();char path[1024];snprintf(path,sizeof path,"%s/%03u.fb",argv[2],frame);
        f=fopen(path,"wb");if(!f)return 4;fwrite(gfx_fb,1,GFX_FB_BYTES,f);
        uint16_t colors[16];for(unsigned i=0;i<16;++i)colors[i]=gfx_paletteOut(i);
        fwrite(colors,1,sizeof colors,f);fclose(f);game.camera=camera;game.zoom=zoom;
        const auto &b=game.balls[0];
        printf("%u %d %d %d %d %d %u %d %d\n",frame,b.x,b.y,b.vx,b.vy,b.ramp,b.rampTicks,camera,zoom);
    }
}
''')
    flags, sources, _ = engine_inputs(work)
    compiler = os.environ.get('CXX', 'clang++')
    common = []
    for i, source in enumerate([s for s in sources if s != GAME / 'Physics.cpp'] + [probe]):
        obj = work / f'common-{i}.o'
        subprocess.run([compiler, *flags, '-c', source, '-o', obj], check=True, cwd=ROOT)
        common.append(obj)
    original = (GAME / 'Physics.cpp').read_text()
    anchor = 'game.zoomTicks = 44;  // the whole ride, including screen crossings'
    assert original.count(anchor) == 1
    traces, animations, results = [], [], []
    sequence = [0] * 12 + list(range(165)) + [164] * 18
    durations = [20 if i % 3 != 1 else 10 for i in range(len(sequence))]
    font = ImageFont.load_default(size=18)
    for delay in (0, 18, 30, 60):
        # Replace the ramp camera's override and clear the capture's specialHit
        # zoom until the chosen delay expires. Other special hits are untouched.
        source = original if not delay else original.replace(
            anchor, f'game.zoomTicks = game.balls[riding].rampTicks >= {delay} ? 44 : 0; // preview only')
        physics = work / f'Physics-{delay}.cpp'
        physics.write_text(source)
        obj, exe = work / f'physics-{delay}.o', work / f'capture-{delay}'
        subprocess.run([compiler, *flags, '-c', physics, '-o', obj], check=True, cwd=ROOT)
        subprocess.run([compiler, *map(str, common), obj, '-o', exe], check=True, cwd=ROOT)
        folder = work / str(delay)
        folder.mkdir(exist_ok=True)
        trace = subprocess.check_output([exe, boardfile, folder, '0'], text=True, cwd=ROOT)
        (folder / 'trace.txt').write_text(trace)
        states = [list(map(int, line.split())) for line in trace.splitlines()]
        motion = [s[:7] for s in states]
        traces.append(motion)
        assert motion == traces[0], 'camera preview changed ball physics'
        entry = next(s[0] for s in states if s[5] == 0)
        exit_frame = next(s[0] for s in states[entry:] if s[5] < 0)
        zoom_start = next(s[0] for s in states if s[8] > 256)
        assert zoom_start - entry == delay
        assert exit_frame - entry == 90
        name = 'Current' if not delay else f'+{delay / 60:g} s'
        frames = [to_image((folder / f'{f:03}.fb').read_bytes(), 1).convert('RGB')
                  .resize((384, 384), Image.Resampling.NEAREST) for f in range(165)]
        arranged = []
        for f in sequence:
            tile = Image.new('RGB', (408, 426), '#161c24')
            ImageDraw.Draw(tile).text((12, 8), name, fill='white', font=font)
            tile.paste(frames[f], (12, 34))
            arranged.append(tile)
        animations.append(arranged)
        save_gif(arranged, out / f'delay-{delay}.gif', durations)
        results.append(dict(label=name, delay_frames=delay, capture_frame=entry,
                            zoom_frame=zoom_start, exit_frame=exit_frame))
        print(f'{name}: entry {entry}, zoom {zoom_start}, exit {exit_frame}', flush=True)
        if not delay:
            diagnostic = work / 'diagonal'
            diagnostic.mkdir(exist_ok=True)
            trace = subprocess.check_output([exe, boardfile, diagnostic, '1'], text=True, cwd=ROOT)
            (diagnostic / 'trace.txt').write_text(trace)
            d = [list(map(int, line.split())) for line in trace.splitlines()]
            capture = next((s[0] for s in d if s[5] == 0), None)
            # With the lip-crossing fix this deliberately missed shot stays
            # below the deck. Keep the original bug captures for comparison.
            marker = 8 if capture is None else capture
            diagnostic_name = 'diagonal-entry-fixed' if capture is None else 'diagonal-entry'
            selected = list(range(max(0, marker - 5), marker + 3))
            sheet = Image.new('RGB', (4 * 228, 2 * 220), '#161c24')
            for j, f in enumerate(selected):
                image = to_image((diagnostic / f'{f:03}.fb').read_bytes(), 1).convert('RGB')
                image = image.crop((38, 52, 91, 92)).resize((212, 160), Image.Resampling.NEAREST)
                x, y = j % 4 * 228, j // 4 * 220
                sheet.paste(image, (x + 8, y + 50))
                draw = ImageDraw.Draw(sheet)
                draw.text((x + 8, y + 4), f'Frame {f}: ' + ('ON ramp' if d[f][5] >= 0 else 'BELOW ramp'), fill='white')
                draw.text((x + 8, y + 22), f'x={d[f][1]/256:.1f} y={d[f][2]/256:.1f}', fill='#bac3cf')
            sheet.save(out / (diagnostic_name + '.png'))
            diag_frames = [to_image((diagnostic / f'{f:03}.fb').read_bytes(), 1).convert('RGB')
                           .crop((32, 42, 96, 100)).resize((384, 348), Image.Resampling.NEAREST)
                           for f in list(range(marker + 18))]
            save_gif(diag_frames, out / (diagnostic_name + '.gif'), [70] * len(diag_frames))
            print('Diagonal side entry rejected' if capture is None else f'Diagonal capture frame {capture}', flush=True)
    sheets = []
    for f in range(len(sequence)):
        image = Image.new('RGB', (816, 852), '#161c24')
        for i in range(4):
            image.paste(animations[i][f], (i % 2 * 408, i // 2 * 426))
        sheets.append(image)
    save_gif(sheets, out / 'all-four.gif', durations)
    (out / 'validation.json').write_text(json.dumps(dict(staged=True,
        identical_ball_motion=True, fps=60, versions=results,
        motion_sha256=hashlib.sha256(json.dumps(traces[0]).encode()).hexdigest()), indent=2) + '\n')
    (out / 'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Ramp zoom timing</title>
<style>body{background:#161c24;color:white;font:17px system-ui;margin:24px}img{max-width:100%;image-rendering:pixelated}main{display:flex;flex-wrap:wrap;gap:16px}article{max-width:408px}</style>
<h1>Ramp zoom timing</h1><p>Staged shot rendered by the actual C++ game. Identical ball motion and speed; only zoom onset changes. Each ride continues to the configured exit. No timing variant has been applied to the game.</p>
<img src="all-four.gif" alt="Current, 0.3 second, 0.5 second and 1 second delay"><h2>0.3 s delay with a smooth zoom</h2><p>Generate the eased preview with tools/preview_ramp_smooth.py. The video runs at 60 fps, normal speed.</p><video controls loop playsinline width="512" src="smooth-03-realtime.mp4"></video><h2>Diagonal entry discrepancy before the fix</h2><p>Current production capture and drawing rules. Slow motion for inspection.</p><img src="diagonal-entry.gif"><img src="diagonal-entry.png">''')
    if (out / 'diagonal-entry-fixed.gif').exists():
        with (out / 'index.html').open('a') as page:
            page.write('<h2>After the front-lip fix</h2><p>This shot misses the front entrance. It remains below the ramp and cannot be captured later through the side.</p><img src="diagonal-entry-fixed.gif"><img src="diagonal-entry-fixed.png">')
    print(out / 'index.html')


if __name__ == '__main__':
    main()
