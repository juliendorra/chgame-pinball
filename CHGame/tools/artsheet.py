"""One sheet of every picture the menus show, for review (docs/cover-art.md).

    python tools/artsheet.py [OUT.png]                    everything -> out/art-review.png
    python tools/artsheet.py --compare OUT.png NAME ...   before (git HEAD) and after, side by side
    python tools/artsheet.py --gallery                    the docs' galleries: docs/cover-art.png (the
                                                          casino card: its cover, folders, games, apps)
                                                          and docs/cover-art-defaults.png (every cart's)

Sections:
- the casino cart's cover (the splash) and its folders
- the games and the apps, in the card's order
- the menu's own screens (the spec's defaults)
- the text menu's pictures, the default every cart falls back on and the
  casino card's own, each with the list drawn on it
- the built-in icons as the bootloader draws them (8x, in the rainbow colour)
- a strip of everything at its real size

NAME for --compare is a sketch (CHYacht), a casino picture (cover, cards, ...,
menu) or a default (about, installed, game, folder, error-1 .. error-5,
cover-default, menu-default).
"""
from __future__ import annotations

import io
import json
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
EXAMPLES = ROOT / "platform" / "board" / "arduino" / "CHGame" / "libraries" / "CHGame" / "examples"
SD = HERE / "sdcard"
ASSETS = ROOT / "spec" / "assets"
ICONS = ROOT / "platform" / "bootloader" / "art" / "icons"

BG = (22, 22, 26)
INK = (230, 226, 214)
DIM = (140, 136, 128)
GOLD = (255, 204, 34)


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def sketch_dir(name):
    for sub in ("Games", "Apps"):
        d = EXAMPLES / sub / name
        if d.is_dir():
            return d
    return None


def card_order():
    """The casino card's games, in its order, with their folders."""
    c = json.loads((SD / "casino.json").read_text(encoding="utf-8"))
    return [(g["sketch"], g.get("folder", "")) for g in c["games"]]


def title_of(sketch):
    d = sketch_dir(sketch)
    try:
        return json.loads((d / "chgame.json").read_text(encoding="utf-8")).get("title", sketch)
    except Exception:
        return sketch


def path_of(name):
    """A picture by its review name."""
    d = sketch_dir(name)
    if d:
        return d / "docs" / "cart.png"
    if name == "menu":
        return SD / "menu.png"
    if name == "menu-default":
        return ASSETS / "menu-default.png"
    if (SD / "art" / f"{name}.png").exists():
        return SD / "art" / f"{name}.png"
    if name == "cover-default":
        return ASSETS / "cover-default.png"
    if name == "about":
        return ASSETS / "about-default.png"
    if (ASSETS / "system" / f"{name}.png").exists():
        return ASSETS / "system" / f"{name}.png"
    raise SystemExit(f"no picture called {name!r}")


def icon_screen(name):
    """A built-in icon as the visual menu draws it: 8x at (16, 8), colour 15
    on black (here in one of the rainbow's colours)."""
    im = Image.open(ICONS / f"{name}.png").convert("L")
    out = Image.new("RGB", (128, 128), (0, 0, 0))
    d = ImageDraw.Draw(out)
    for y in range(12):
        for x in range(12):
            if im.getpixel((x, y)) >= 128:
                d.rectangle((16 + x * 8, 8 + y * 8, 23 + x * 8, 15 + y * 8), fill=(255, 0, 255))
    return out


def text_menu(path):
    from chcart import background
    return background.preview(path.read_bytes(), scale=1)


def sections():
    """[(heading, [(label, PIL image)])]."""
    cart = [("COVER / SPLASH", Image.open(SD / "art" / "cover.png"))]
    for f in ("cards", "casino", "dice", "board", "tiles", "words", "apps"):
        p = SD / "art" / f"{f}.png"
        if p.exists():
            cart.append((f.upper(), Image.open(p)))
    games, apps = [], []
    for sk, folder in card_order():
        d = sketch_dir(sk)
        if not d or not (d / "docs" / "cart.png").exists():
            continue
        item = (title_of(sk).upper(), Image.open(d / "docs" / "cart.png"))
        (apps if folder == "APPS" else games).append(item)
    system = [("COVER (DEFAULT)", Image.open(ASSETS / "cover-default.png")),
              ("ABOUT", Image.open(ASSETS / "about-default.png")),
              ("INSTALLED", Image.open(ASSETS / "system" / "installed.png")),
              ("NO PICTURE", Image.open(ASSETS / "system" / "game.png")),
              ("FOLDER (DEFAULT)", Image.open(ASSETS / "system" / "folder.png"))]
    system += [(f"ERROR {n}", Image.open(ASSETS / "system" / f"error-{n}.png")) for n in range(1, 6)]
    menu = [("DEFAULT (EVERY CART)", Image.open(ASSETS / "menu-default.png")),
            ("DEFAULT, WITH THE LIST", text_menu(ASSETS / "menu-default.png")),
            ("CASINO CARD", Image.open(SD / "menu.png")), ("CASINO, WITH THE LIST", text_menu(SD / "menu.png"))]
    icons = [(n.upper(), icon_screen(n)) for n in ("usb", "folder", "error", "game", "ok")]
    return [("THE CASINO CART: COVER AND FOLDERS", cart),
            ("THE GAMES", games),
            ("THE APPS", apps),
            ("THE MENU'S OWN SCREENS (spec/assets)", system),
            ("THE TEXT MENU'S PICTURES: THE DEFAULT AND THE CASINO CARD'S", menu),
            ("BUILT INTO THE BOOTLOADER (12x12 one-bit icons, drawn 8x)", icons)]


def build(secs, scale=2, cols=6, strip=True):
    s = 128 * scale
    gap, lab, head = 16, 22, 34
    width = gap + cols * (s + gap)
    H = gap
    for _, items in secs:
        rows = (len(items) + cols - 1) // cols
        H += head + rows * (s + lab + gap)
    allims = [im for _, items in secs for _, im in items if im.size == (128, 128)]
    per = (width - gap) // (128 + 4)
    if strip:
        H += head + ((len(allims) + per - 1) // per) * (128 + 4) + gap
    sheet = Image.new("RGB", (width, H), BG)
    d = ImageDraw.Draw(sheet)
    fh, fl = font(20), font(14)
    y = gap
    for title, items in secs:
        d.text((gap, y + 6), title, fill=GOLD, font=fh)
        y += head
        for k, (label, im) in enumerate(items):
            x = gap + (k % cols) * (s + gap)
            yy = y + (k // cols) * (s + lab + gap)
            sheet.paste(im.convert("RGB").resize((s, s), Image.NEAREST), (x, yy))
            d.text((x, yy + s + 4), label, fill=INK, font=fl)
        y += ((len(items) + cols - 1) // cols) * (s + lab + gap)
    if strip:
        d.text((gap, y + 6), "AT THEIR REAL SIZE", fill=GOLD, font=fh)
        y += head
        for k, im in enumerate(allims):
            sheet.paste(im.convert("RGB"), (gap + (k % per) * 132, y + (k // per) * 132))
    return sheet


def git_head(path):
    rel = path.resolve().relative_to(ROOT).as_posix()
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True)
    return Image.open(io.BytesIO(r.stdout)) if r.returncode == 0 else None


def compare(out, names):
    rows = []
    for n in names:
        p = path_of(n)
        old = git_head(p)
        new = Image.open(p)
        rows.append((n, old, new))
    s = 384
    gap = 16
    W = gap + 2 * (s + gap) + 128 + gap
    H = gap + len(rows) * (s + 30 + gap)
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    fl = font(16)
    for k, (n, old, new) in enumerate(rows):
        y = gap + k * (s + 30 + gap)
        d.text((gap, y), f"{n}: before", fill=DIM, font=fl)
        d.text((gap + s + gap, y), "after", fill=GOLD, font=fl)
        d.text((gap + 2 * (s + gap), y), "real size", fill=DIM, font=fl)
        if old is not None:
            sheet.paste(old.convert("RGB").resize((s, s), Image.NEAREST), (gap, y + 24))
        sheet.paste(new.convert("RGB").resize((s, s), Image.NEAREST), (gap + s + gap, y + 24))
        sheet.paste(new.convert("RGB"), (gap + 2 * (s + gap), y + 24))
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def gallery_casino():
    """The casino card as the visual menu shows it: the cover, the folders,
    then the games and the apps in the card's order."""
    ims = [Image.open(SD / "art" / "cover.png")]
    ims += [Image.open(SD / "art" / f"{f}.png") for f in ("cards", "casino", "dice", "board", "tiles", "words", "apps")]
    for sk, _ in card_order():
        d = sketch_dir(sk)
        if d and (d / "docs" / "cart.png").exists():
            ims.append(Image.open(d / "docs" / "cart.png"))
    return ims


def gallery_defaults():
    """The pictures every cart falls back on (spec/assets): the cover, the
    text menu's picture, about, installed, no picture, folder, the errors."""
    names = ["cover-default.png", "menu-default.png", "about-default.png", "system/installed.png", "system/game.png",
             "system/folder.png"] + [f"system/error-{n}.png" for n in range(1, 6)]
    return [Image.open(ASSETS / n) for n in names]


def gallery(ims, out, scale=2, cols=6, gap=8):
    """Pictures in a plain grid, no labels: for the docs."""
    s = 128 * scale
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (gap + cols * (s + gap), gap + rows * (s + gap)), BG)
    for k, im in enumerate(ims):
        sheet.paste(im.convert("RGB").resize((s, s), Image.NEAREST),
                    (gap + (k % cols) * (s + gap), gap + (k // cols) * (s + gap)))
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if sheet.getcolors(256) is not None:                       # 256 colours or fewer: indexed, exact and small
        sheet = sheet.convert("P", palette=Image.ADAPTIVE, colors=256)
    sheet.save(out, optimize=True)
    return out


def main(argv):
    if argv and argv[0] == "--gallery":
        print(gallery(gallery_casino(), ROOT / "docs" / "cover-art.png"))
        print(gallery(gallery_defaults(), ROOT / "docs" / "cover-art-defaults.png"))
        return 0
    if argv and argv[0] == "--compare":
        print(compare(argv[1], argv[2:]))
        return 0
    out = pathlib.Path(argv[0] if argv else ROOT / "out" / "art-review.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    build(sections()).save(out)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
