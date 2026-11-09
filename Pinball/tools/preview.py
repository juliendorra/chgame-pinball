#!/usr/bin/env python3
"""Record the deterministic pirate showcase and assemble its documentation GIF."""
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageChops

GAME = Path(__file__).resolve().parents[1]
ROOT = GAME.parent
out = GAME / "out/preview"
subprocess.run([sys.executable, str(ROOT / "pinball.py"), "boards", "--image", str(GAME / "out/pinball.img")], check=True)
subprocess.run([sys.executable, str(ROOT / "pinball.py"), "run", "tools/scripts/preview.txt", "out/preview",
                "--card", str(GAME / "out/pinball.img")], check=True)
with Image.open(out / "paused.png") as a, Image.open(out / "still_paused.png") as b:
    assert not ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox(), "pause changed the image"
frames, durations = [], []
for name, hold in (("library_return.png", 900), ("pirate_upper.png", 750), ("rubber_flex.gif", None),
                   ("pirate_play.gif", None), ("ramp_full.gif", None),
                   ("score_pop.gif", None), ("special_zoom.gif", None)):
    with Image.open(out / name) as source:
        for index in range(source.n_frames if hasattr(source, "n_frames") else 1):
            source.seek(index)
            frames.append(source.convert("RGB").resize((256, 256), Image.Resampling.NEAREST))
            durations.append(hold or source.info.get("duration", 33))
(GAME / "docs").mkdir(exist_ok=True)
dest = GAME / "docs/gameplay.gif"
frames[0].save(dest, save_all=True, append_images=frames[1:], duration=durations, loop=0)
print(dest)
