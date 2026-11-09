"""The casino card's own pictures (tools/sdcard/casino.json): the cart's
cover, which is the splash at power-on, one cover per genre folder, and the
text menu's picture.

    python tools/sdcard/covers.py [--sheet OUT.png]     -> tools/sdcard/art/*.png, tools/sdcard/menu.png

Each is painted by its recipe in tools/sdcard/art/src/<name>.py, whose
draw() returns the image (docs/cover-art.md): cover, the folders cards,
casino, dice, board, tiles, words and apps (one family: folderkit.py holds
their shared look), and menu (the text menu's picture, written to
tools/sdcard/menu.png). Edit a recipe and run this; the PNGs are never
edited by hand.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))                  # the repository's tools/
import boxart as bx  # noqa: E402

ART = HERE / "art"
SRC = ART / "src"
ORDER = ["cover", "cards", "casino", "dice", "board", "tiles", "words", "apps", "menu"]


def target(name):
    return HERE / "menu.png" if name == "menu" else ART / f"{name}.png"


def from_recipe(name):
    """The picture art/src/<name>.py draws."""
    f = SRC / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"cover_{name}", f)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.draw()


def main(argv):
    ART.mkdir(exist_ok=True)
    out = [bx.save(from_recipe(name), target(name)) for name in ORDER]
    for p in out:
        print(p)
    if "--sheet" in argv:
        print(bx.sheet(out, argv[argv.index("--sheet") + 1], scale=2, cols=5))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
