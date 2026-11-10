#!/usr/bin/env python3
"""Render a preview-only delayed smoothstep zoom with real-time playback."""
import json
import os
import subprocess
import sys

from PIL import Image
from boards import encode
from build_studio import GAME, ROOT, engine_inputs

sys.path.insert(0, str(ROOT / 'CHGame/tools/chsim'))
from fbimage import to_image, save_gif


def main():
    work = GAME / 'out/ramp-smooth-zoom'
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
using namespace pinball;
extern "C" {void pb_init();uint8_t *pb_input();int pb_apply(unsigned);void pb_step(unsigned);}
int main(int argc,char **argv){
 pb_init();FILE *f=fopen(argv[1],"rb");if(!f)return 2;
 unsigned n=fread(pb_input(),1,960,f);fclose(f);if(!pb_apply(n))return 3;
 newGame(12345);placeBall(0,60,313,0,-500);game.camera=225;
 for(unsigned frame=0;frame<165;++frame){
  if(frame)pb_step(0);drawTable();char path[1024];snprintf(path,sizeof path,"%s/%03u.fb",argv[2],frame);
  f=fopen(path,"wb");if(!f)return 4;fwrite(gfx_fb,1,GFX_FB_BYTES,f);
  uint16_t colors[16];for(unsigned i=0;i<16;++i)colors[i]=gfx_paletteOut(i);
  fwrite(colors,1,sizeof colors,f);fclose(f);const auto &b=game.balls[0];
  printf("%u %d %d %d %d %d %u %d %d\n",frame,b.x,b.y,b.vx,b.vy,b.ramp,b.rampTicks,game.camera,game.zoom);
 }
}
''')
    flags, sources, _ = engine_inputs(work)
    compiler = os.environ.get('CXX', 'clang++')
    original = (GAME / 'Physics.cpp').read_text()
    anchor = 'game.zoomTicks = 44;  // the whole ride, including screen crossings'
    assert original.count(anchor) == 1
    modified = original.replace(anchor, 'game.zoomTicks = game.balls[riding].rampTicks >= 18 ? 44 : 0; // preview')
    zoom = 'game.zoom += clamp(zoomTarget - game.zoom, protectFlippers ? -64 : -16, 32);'
    assert modified.count(zoom) == 1
    # 0.3 s hold, then a 0.4 s cubic smoothstep with zero endpoint slope.
    modified = modified.replace(zoom, '''if(followRamp) {
        int t=clamp(int(game.balls[riding].rampTicks)-18,0,24);
        game.zoom=ONE+(128*t*t*(72-2*t)+6912)/13824;
    } else ''' + zoom)
    physics = work / 'Physics-smooth.cpp'
    physics.write_text(modified)
    sources = [physics if s == GAME / 'Physics.cpp' else s for s in sources]
    exe = work / 'capture'
    subprocess.run([compiler, *flags, *sources, probe, '-o', exe], check=True, cwd=ROOT)
    trace = subprocess.check_output([exe, boardfile, work], text=True, cwd=ROOT)
    (work / 'trace.txt').write_text(trace)
    states = [list(map(int, row.split())) for row in trace.splitlines()]
    capture = next(s[0] for s in states if s[5] == 0)
    exit_frame = next(s[0] for s in states[capture:] if s[5] < 0)
    assert exit_frame - capture == 90
    assert all(s[8] == 256 for s in states[capture:capture + 19])
    curve = [s[8] for s in states[capture + 18:capture + 43]]
    assert curve[0] == 256 and curve[-1] == 384
    assert all(a <= b for a, b in zip(curve, curve[1:]))
    assert max(b - a for a, b in zip(curve, curve[1:])) <= 9
    reference = GAME / 'out/ramp-zoom-delays/18/trace.txt'
    if reference.exists():
        baseline = [list(map(int, row.split()))[:7] for row in reference.read_text().splitlines()]
        assert [s[:7] for s in states] == baseline, 'zoom must not affect ball motion'
    images = []
    for f in range(165):
        image = to_image((work / f'{f:03}.fb').read_bytes(), 1).convert('RGB')
        image = image.resize((512, 512), Image.Resampling.NEAREST)
        image.save(work / f'{f:03}.png')
        images.append(image)
    # GIF's centisecond clock and browser minimum frame delay cannot reliably
    # represent 60 fps. Show every other frame at 30 fps, preserving real speed.
    gif_frames = images[::2]
    durations = [round((i + 1) * 10 / 3) * 10 - round(i * 10 / 3) * 10
                 for i in range(len(gif_frames))]
    assert abs(sum(durations)/1000 - len(images)/60) < 1/30
    save_gif(gif_frames, out / 'smooth-03-realtime.gif', durations)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '60', '-i', str(work / '%03d.png'),
                    '-c:v', 'libx264', '-crf', '15', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                    str(out / 'smooth-03-realtime.mp4')], check=True)
    report = dict(staged=True, applied_to_game=False, delay_seconds=0.3,
                  ease_seconds=0.4, curve='3t²−2t³', capture_frame=capture, exit_frame=exit_frame,
                  frames=165, video_fps=60, video_seconds=165/60,
                  gif_sample_fps=30, gif_seconds=sum(durations)/1000, zoom_samples=curve)
    (out / 'smooth-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
