"""python -m artkit show RECIPE.py[:func] [--name N] [--out DIR]

Runs a recipe's draw() (or `func`) and writes, for looking at:
    DIR/N_1x.png       the picture itself
    DIR/N_4x.png       4x, nearest neighbour
    DIR/N_menu.png     3x, as the menu shows it installed and installing: the
                       1-pixel border (in one of the rainbow's colours) and
                       the install bar half full
then runs the house checks (artkit.lint). DIR is out/art by default; N the
recipe's sketch name (or the file's stem).
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from artkit import lint as L  # noqa: E402


def load(spec):
    path, func = spec, ""
    head, _, tail = spec.rpartition(":")
    if head and tail.isidentifier():             # RECIPE.py:func (not a drive letter's colon)
        path, func = head, tail
    p = pathlib.Path(path).resolve()
    s = importlib.util.spec_from_file_location(f"recipe_{p.parent.parent.name}_{p.stem}", p)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return p, getattr(mod, func or "draw")


def menu_view(im):
    from PIL import Image, ImageDraw
    a = im.convert("RGB").copy()
    b = a.copy()
    d = ImageDraw.Draw(b)
    d.rectangle((0, 0, 127, 127), outline=(0, 200, 255))
    d.rectangle((8, 110, 119, 119), outline=(255, 0, 255))
    d.rectangle((9, 111, 118, 118), fill=(0, 0, 0))
    d.rectangle((10, 112, 63, 117), fill=(255, 0, 255))
    out = Image.new("RGB", (128 * 2 + 4, 128), (40, 40, 40))
    out.paste(a, (0, 0))
    out.paste(b, (132, 0))
    return out.resize((out.width * 3, out.height * 3), Image.NEAREST)


def show(spec, name=None, out=None):
    from PIL import Image
    p, fn = load(spec)
    t0 = time.time()
    res = fn()
    dt = time.time() - t0
    im = res.image() if hasattr(res, "image") else res
    if not isinstance(im, Image.Image):
        import boxart
        im = boxart.image(im)
    name = name or (p.parent.parent.name if p.parent.name == "tools" else p.stem)
    out = pathlib.Path(out or (HERE.parents[1] / "out" / "art"))
    out.mkdir(parents=True, exist_ok=True)
    im.save(out / f"{name}_1x.png")
    im.resize((512, 512), Image.NEAREST).save(out / f"{name}_4x.png")
    menu_view(im).save(out / f"{name}_menu.png")
    notes, stats = L.lint(out / f"{name}_1x.png")
    print(f"{name}: drawn in {dt:.1f} s -> {out / (name + '_4x.png')}")
    print(f"   {stats}")
    for n in notes:
        print("   ", n)
    return 1 if any(n.startswith("ERROR") for n in notes) else 0


def main(argv):
    if not argv or argv[0] != "show" or len(argv) < 2:
        print(__doc__)
        return 2
    name = argv[argv.index("--name") + 1] if "--name" in argv else None
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    return show(argv[1], name, out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
