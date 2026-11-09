"""The visual menu's own pictures: the defaults card preparation uses
(spec/card.md) when a cart has none of its own.

    spec/assets/cover-default.png    the cart's cover, the splash at power-on
    spec/assets/about-default.png    the about page (B at the top): how the menu works
    spec/assets/menu-default.png     the text menu's picture (docs/menu-image.md)
    spec/assets/system/*.png         the screens SYSTEM.PIC carries after the about page:
                                     installed (the program in flash, when no card entry
                                     holds it), game (a game without a picture), folder (a
                                     folder without a cover), error-1 .. error-5

Each is painted by its recipe in tools/art/menu/ (cover.py, about.py,
installed.py, game.py, folder.py, error.py, menu.py), whose draw() (draw(n)
for the errors) returns the image (docs/cover-art.md); cover, game and
folder share the scene in sdscene.py, menu the panel and keys in listbg.py
with the casino card's text-menu picture. Edit a recipe and run this;
the PNGs are never edited by hand. This is a change to the card format's
shared assets: run `python tools/chcart/fixtures.py` afterwards.

    python tools/menuart.py [--sheet out/menuart.png]
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boxart as bx  # noqa: E402

ASSETS = HERE.parent / "spec" / "assets"
RECIPES = HERE / "art" / "menu"
SYSTEM = ASSETS / "system"

# The errors: what install.h's codes mean to a player (docs/sd-menu.md)
ERRORS = {
    1: ("CARD ERROR", ["THE CARD STOPPED", "ANSWERING.", "", "RESEAT IT AND", "TRY AGAIN."]),
    2: ("FILE DAMAGED", ["THE GAME'S FILE IS", "DAMAGED. NOTHING", "WAS ERASED.", "", "COPY IT AGAIN."]),
    3: ("NOT A GAME", ["THE FILE HOLDS A", "BOOTLOADER, NOT A", "GAME. NOTHING WAS", "ERASED."]),
    4: ("INSTALL FAILED", ["THE CARD FAILED", "PARTWAY. THE OLD", "GAME IS GONE, BUT", "NO HALF GAME RUNS.", "PICK A GAME AGAIN."]),
    5: ("CAN'T INSTALL", ["DAMAGED, MADE FOR", "ANOTHER BOARD, OR", "FOR A NEWER MENU.", "NOTHING WAS", "ERASED."]),
}

# Each picture: its recipe in tools/art/menu/ and draw()'s arguments
PICTURES = {ASSETS / "cover-default.png": ("cover", ()), ASSETS / "about-default.png": ("about", ()),
            ASSETS / "menu-default.png": ("menu", ()),
            SYSTEM / "installed.png": ("installed", ()), SYSTEM / "game.png": ("game", ()),
            SYSTEM / "folder.png": ("folder", ()),
            **{SYSTEM / f"error-{n}.png": ("error", (n,)) for n in ERRORS}}


def chg_logo():
    """The CHGAME logo as 1 bpp rows ('#' ink): tools/art/chglogo.py keeps
    the master and dresses it."""
    sys.path.insert(0, str(HERE / "art"))
    import chglogo
    return list(chglogo.LOGO_ROWS)


def draw(path):
    """The picture its recipe draws."""
    name, args = PICTURES[path]
    spec = importlib.util.spec_from_file_location(f"menuart_{name}", RECIPES / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.draw(*args)


def main(argv):
    for path in PICTURES:
        bx.save(draw(path), path)
        print(f"drew {path.relative_to(HERE.parent)}")
    if "--sheet" in argv:
        out = argv[argv.index("--sheet") + 1]
        print(bx.sheet(list(PICTURES), out, scale=2, cols=5))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
