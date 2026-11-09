"""`chgame cart ...` and `chgame export`: .chgame files from the command line.

    chgame export [--no-build] [--out F]          in a sketch folder: build/<Name>.chgame
    chgame cart info PKG [--json]                 the games, their files, the warnings
    chgame cart verify PKG ...                    every rule of spec/chgame.md (exit 1 on an error)
    chgame cart extract PKG DIR                   the files, as laid out inside
    chgame cart new OUT ITEM ... [--title T ...]  a cart from .chgame/.bin/.hex/.elf/.chg files and sketches
    chgame cart build RECIPE.json [OUT]           a cart from a recipe (games named by sketch)
    chgame cart add PKG ITEM ... [--folder F] [--at N]
    chgame cart remove PKG ID ...
    chgame cart order PKG ID|FOLDER/ ...          these first, in this order; the rest after (FOLDER/:
                                                  that folder's games, which puts the folder there)
    chgame cart set PKG [--game ID] KEY=VALUE ... (KEY= clears; title, folder, author, ...)
    chgame cart launch PKG ID|none                the game started at power-on
    chgame cart background PKG IMAGE|none [--folder F] [--color KEY=#RRGGBB]
                                                  the list menu's picture (any image: converted, chcart/background.py)
    chgame cart picture PKG IMAGE|none [--game ID | --folder F | --about | --system SCREEN]
                                                  the visual menu's pictures: the cart's cover (the
                                                  splash), a game's, a folder's cover, the about page,
                                                  one of the menu's own screens (installed, game, folder,
                                                  error-1 .. error-5; the defaults stand in for the rest)
    chgame cart art PKG [--redo]                  a picture for every game and folder cover missing
                                                  one, drawn from its title (tools/boxart.py)
    chgame cart prepare PKG OUTDIR [--image IMG]  the card's files (spec/card.md), and a FAT32 image
    chgame cart flash PKG [--game ID] [--port P]  upload one game
    chgame cart deploy PKG [--card DIR] [--port P] [--clean] [--no-flash]
    chgame cart backup CARD OUT [--game PATH|ID ...] [--sd CHG=PATH ...] [--title T]
                                                  the card's games (CARD: a drive, a FAT image or a
                                                  ZIP of its files) back into a cart, with their SD
                                                  files (chcart/backup.py); all of them: the menu too

A recipe is a manifest whose games may be {"sketch": "CHFour", "folder": ...,
other game keys to override}: chgame cart build compiles each sketch (unless
--no-build) and takes its game from it (chcart/sources.py: chgame.json). Its
menu's pictures (background, cover, about, folders' background and cover)
are any images, converted, paths relative to the recipe; a folder without a
cover gets one drawn from its name.
Exit codes: 0 done, 1 an error in a cart or a failed step, 2 usage.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from . import background, backup, deploy, model, runtime, sources, zipio
from .model import CartError

GAME_SET = ("title", "folder", "version", "author", "description", "genre", "license", "url", "sourceUrl", "id")
CART_SET = ("title", "version", "author", "description", "date", "license", "url", "sourceUrl")


def _load(path):
    issues = []
    cart = zipio.load(path, issues)
    for i in issues:
        if not i.error:
            print(f"{path}: {i}", file=sys.stderr)
    return cart


def _save(cart, path):
    data = zipio.write(cart, path)
    print(f"{path}: {len(cart.games)} game{'s' * (len(cart.games) != 1)}, {len(data)} B")


def _game(cart, gid):
    g = cart.game(gid)
    if g is None:
        raise CartError([model.Issue("bad-id", gid, f"no game {gid!r} (games: {', '.join(x.id for x in cart.games)})")])
    return g


def cmd_info(a):
    cart = _load(a.pkg)
    if a.json:
        print(json.dumps(model.to_manifest(cart)[0], indent=2))
        return 0
    print(f"{cart.title}" + "".join(f"  {k} {getattr(cart, k)}" for k in ("version", "author") if getattr(cart, k)))
    if cart.launch:
        print(f"launch: {cart.launch}")
    for g in cart.games:
        where = f"[{g.folder}] " if g.folder else ""
        sizes = ", ".join(f"{d} {len(b)} B" for d, b in sorted(g.binaries.items()) if d != "rev0")
        img = g.binary("rev0")
        print(f"  {g.id:20s} {where}{g.title!r}  {len(img) if img else 0} B" + (f" ({sizes})" if sizes else "")
              + (f", {len(g.sd)} SD file{'s' * (len(g.sd) != 1)} ({sum(map(len, g.sd.values()))} B)" if g.sd else "")
              + (f"  {g.version}" if g.version else ""))
    return 0


def cmd_verify(a):
    bad = 0
    for p in a.pkgs:
        issues = zipio.check(p)
        errors = [i for i in issues if i.error]
        print(f"{p}: {'BAD' if errors else 'ok'}")
        for i in issues:
            print(f"  {i}")
        bad += bool(errors)
    return 1 if bad else 0


def cmd_extract(a):
    files, manifest = zipio.read(a.pkg)
    out = pathlib.Path(a.dir)
    for n, data in files.items():
        (out / n).parent.mkdir(parents=True, exist_ok=True)
        (out / n).write_bytes(data)
    print(f"{out}: {len(files)} files")
    return 0


def _apply_cart_args(cart, a):
    for k in CART_SET:
        v = getattr(a, k, None)
        if v is not None:
            setattr(cart, k, v)


def cmd_new(a):
    games = []
    for item in a.items:
        games = sources.merge(games, sources.load_item(item, build=not a.no_build))
    first = next((zipio.load(i) for i in a.items if str(i).lower().endswith(".chgame")), None)
    cart = model.Cart(title=a.title or (first.title if first else games[0].title if len(games) == 1 else "CART"),
                      games=games)
    if first:                               # the first cart's menu and details carry over
        for k in CART_SET[1:] + ("background", "colors", "folder_backgrounds", "cover", "about", "folder_covers",
                                 "system_images", "extensions"):
            setattr(cart, k, getattr(first, k))
    _apply_cart_args(cart, a)
    _save(cart, a.out)
    return 0


def recipe_sketches(recipe_path):
    """The sketch names a recipe takes its games from, in order."""
    r = json.loads(pathlib.Path(recipe_path).read_text(encoding="utf-8"))
    return [e["sketch"] for e in r.get("games", []) if "sketch" in e]


def build_recipe(recipe_path, build=True, platform_dir=None, binary=None, only=None):
    """A Cart from a recipe file. `binary(sketch_dir)` may supply each release
    .bin instead of building (tools/release/acceptance.py); `platform_dir`
    finds the sketches in an installed board package instead of here; `only`
    keeps the games of those sketches."""
    import paths
    r = json.loads(pathlib.Path(recipe_path).read_text(encoding="utf-8"))
    base = pathlib.Path(recipe_path).parent
    games = []
    for e in r.get("games", []):
        e = dict(e)
        name = e.pop("sketch")
        if only and name not in only:
            continue
        d = paths.sketch(name) if platform_dir is None else _in_platform(name, platform_dir)
        if binary is not None:
            g = sources.from_sketch(d, pathlib.Path(binary(d)).read_bytes())
        else:
            g = sources.load_item(d, build=build)[0]
        for k, v in e.items():
            if k not in GAME_SET:
                raise CartError([model.Issue("bad-field", f"{recipe_path}: {name}.{k}", "not a game key a recipe sets")])
            setattr(g, k, v)
        games = sources.merge(games, [g])
    menu = r.get("menu", {})
    cart = model.Cart(title=r.get("title", "CART"), games=games, launch=r.get("launch", ""),
                      colors=menu.get("colors", {}))
    for k in CART_SET[1:]:
        setattr(cart, k, r.get(k, ""))
    ui = cart.ui_colors()
    if menu.get("background"):
        cart.background = _picture(base / menu["background"], ui)
    for k in ("cover", "about"):
        if menu.get(k):
            setattr(cart, k, _picture(base / menu[k], model.UI_COLORS))
    for k, path in menu.get("systemImages", {}).items():
        if k not in model.SYSTEM_IMAGES:
            raise CartError([model.Issue("bad-field", f"{recipe_path}: menu.systemImages.{k}",
                                         f"not a screen of the menu (they are {', '.join(model.SYSTEM_IMAGES)})")])
        cart.system_images[k] = _picture(base / path, model.UI_COLORS)
    for f in menu.get("folders", []):
        if f.get("background"):
            cart.folder_backgrounds[f["name"]] = _picture(base / f["background"], ui)
        if f.get("cover"):
            cart.folder_covers[f["name"]] = _picture(base / f["cover"], model.UI_COLORS)
    fill_art(cart)
    return cart


def fill_art(cart, redo=False):
    """A picture for every game without one (its title) and a cover for every folder without one (its name):
    tools/boxart.py's placeholders. redo: every game's and folder's, even one
    it has. Returns how many were drawn."""
    n = 0
    for g in cart.games:
        if g.cart_image is None or redo:
            g.cart_image = sources.placeholder(g.title)
            n += 1
    for f in cart.folders():
        if f not in cart.folder_covers or redo:
            import boxart                   # (tools/ is on the path: runtime.py)
            cart.folder_covers[f] = boxart.folder_cover(f.rsplit("/", 1)[-1])
            n += 1
    return n


def _picture(path, ui, fit="cover", dither=False):
    """A menu picture from any image, converted if it needs to be (saying how)."""
    png, notes = background.convert(path, ui, fit, dither)
    for n in notes:
        print(f"{pathlib.Path(path).name}: {n}")
    return png


def _in_platform(name, platform_dir):
    for sub in ("Games", "Apps"):
        d = pathlib.Path(platform_dir) / "libraries" / "CHGame" / "examples" / sub / name
        if d.is_dir():
            return d
    raise SystemExit(f"{name}: not in {platform_dir}")


def cmd_build(a):
    cart = build_recipe(a.recipe, build=not a.no_build)
    out = a.out or str(pathlib.Path(a.recipe).with_suffix(".chgame").name)
    _save(cart, out)
    return 0


def cmd_add(a):
    cart = _load(a.pkg)
    new = []
    for item in a.items:
        new += sources.load_item(item, build=not a.no_build)
    for g in new:
        if a.folder is not None:
            g.folder = a.folder
    merged = sources.merge(cart.games, new)
    if a.at is not None:
        added = merged[len(cart.games):]
        merged = cart.games[:a.at] + added + cart.games[a.at:]
    cart.games = merged
    _save(cart, a.pkg)
    return 0


def cmd_remove(a):
    cart = _load(a.pkg)
    for gid in a.ids:
        _game(cart, gid)
    cart.games = [g for g in cart.games if g.id not in a.ids]
    if cart.launch in a.ids:
        cart.launch = ""
    _save(cart, a.pkg)
    return 0


def cmd_order(a):
    """Games, and folders (an item ending in '/'), first in the order given:
    a folder sits where its first game is, so moving its games moves it."""
    cart = _load(a.pkg)
    first = []
    for item in a.ids:
        if item.endswith("/"):
            path = item.rstrip("/")
            block = [g for g in cart.games if g.folder == path or g.folder.startswith(path + "/")]
            if not block:
                raise CartError([model.Issue("bad-folder", item, f"no game is in a folder {path!r} "
                                             f"(folders: {', '.join(cart.folders()) or 'none'})")])
        else:
            block = [_game(cart, item)]
        first += [g for g in block if g not in first]
    cart.games = first + [g for g in cart.games if g not in first]
    _save(cart, a.pkg)
    return 0


def cmd_set(a):
    cart = _load(a.pkg)
    target, keys = (_game(cart, a.game), GAME_SET) if a.game else (cart, CART_SET)
    for kv in a.pairs:
        k, eq, v = kv.partition("=")
        if not eq or k not in keys:
            raise SystemExit(f"{kv}: KEY=VALUE with KEY one of {', '.join(keys)}")
        if k == "id" and cart.launch == target.id:
            cart.launch = v
        setattr(target, k, v)
    _save(cart, a.pkg)
    return 0


def cmd_launch(a):
    cart = _load(a.pkg)
    cart.launch = "" if a.id == "none" else _game(cart, a.id).id
    _save(cart, a.pkg)
    return 0


def cmd_background(a):
    cart = _load(a.pkg)
    if a.color:
        cart.colors = {k: v for k, v in background.colors_arg(a.color).items() if v != model.UI_COLORS[k]}
    png = None if a.png == "none" else _picture(a.png, cart.ui_colors(), a.fit, a.dither)
    if a.folder:
        if png is None:
            cart.folder_backgrounds.pop(a.folder, None)
        else:
            cart.folder_backgrounds[a.folder] = png
    else:
        cart.background = png
    _save(cart, a.pkg)
    return 0


def cmd_picture(a):
    cart = _load(a.pkg)
    png = None if a.png == "none" else _picture(a.png, model.UI_COLORS, a.fit, a.dither)
    if a.game:
        _game(cart, a.game).cart_image = png
    elif a.folder:
        if a.folder not in cart.folders():
            raise CartError([model.Issue("bad-folder", a.folder, f"no game is in it (folders: {', '.join(cart.folders()) or 'none'})")])
        if png is None:
            cart.folder_covers.pop(a.folder, None)
        else:
            cart.folder_covers[a.folder] = png
    elif a.about:
        cart.about = png
    elif a.system:
        if png is None:
            cart.system_images.pop(a.system, None)
        else:
            cart.system_images[a.system] = png
    else:
        cart.cover = png
    _save(cart, a.pkg)
    return 0


def cmd_art(a):
    cart = _load(a.pkg)
    n = fill_art(cart, a.redo)
    print(f"{a.pkg}: {n} picture{'s' * (n != 1)} drawn")
    if n:
        _save(cart, a.pkg)
    return 0


def cmd_prepare(a):
    cart = _load(a.pkg)
    files = runtime.prepare(cart, a.device)
    runtime.write_folder(files, a.outdir)
    print(f"{a.outdir}: {len(files)} files, {sum(map(len, files.values()))} B; copy its contents to the card's root")
    if a.image:
        runtime.write_image(files, a.image)
        print(f"card image: {a.image}")
    return 0


def cmd_flash(a):
    cart = _load(a.pkg)
    g = _game(cart, a.game) if a.game else (cart.game(cart.launch) if cart.launch else cart.games[0])
    if not a.game and len(cart.games) > 1:
        print(f"note: flashing {g.id}; --game picks another", file=sys.stderr)
    deploy.flash(g, a.port, a.device)
    return 0


def cmd_deploy(a):
    deploy.deploy(_load(a.pkg), a.card, a.port, a.clean, a.device, do_flash=not a.no_flash)
    return 0


def cmd_backup(a):
    sd = {}
    for pair in a.sd or []:
        chg, sep, path = pair.partition("=")
        if not sep:
            raise CartError([model.Issue("bad-field", pair, "--sd takes GAMES/<NAME>.CHG=<path on the card>")])
        sd.setdefault(chg.replace("\\", "/"), []).append(path)
    cart, issues = backup.backup(a.card, a.game, a.title or "CARD BACKUP", sd)
    for i in issues:
        print(i, file=sys.stderr)
    _save(cart, a.out)
    for g in cart.games:
        print(f"  {(g.folder + '/' if g.folder else '') + g.title:32s} {g.id:20s} "
              f"{len(g.sd)} SD file{'s' * (len(g.sd) != 1)}" + ("  (launch)" if g.id == cart.launch else ""))
    return 0


def cmd_export(a, sketch):
    g = sources.load_item(sketch, build=not a.no_build)[0]
    cart = model.Cart(title=g.title, games=[g], version=g.version, author=g.author, license=g.license,
                      url=g.url, sourceUrl=g.sourceUrl)
    out = pathlib.Path(a.out) if a.out else sketch / "build" / f"{sketch.name}.chgame"
    out.parent.mkdir(parents=True, exist_ok=True)
    _save(cart, out)
    return 0


def parser():
    ap = argparse.ArgumentParser(prog="chgame cart", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="command")
    p = sub.add_parser("info", help="list a cart's games")
    p.add_argument("pkg")
    p.add_argument("--json", action="store_true", help="the normalized info.json")
    p = sub.add_parser("verify", help="check carts against the spec")
    p.add_argument("pkgs", nargs="+")
    p = sub.add_parser("extract", help="unpack a cart's files")
    p.add_argument("pkg")
    p.add_argument("dir")
    for name in ("new", "build"):
        p = sub.add_parser(name, help="a cart from items" if name == "new" else "a cart from a recipe")
        if name == "new":
            p.add_argument("out")
            p.add_argument("items", nargs="+")
        else:
            p.add_argument("recipe")
            p.add_argument("out", nargs="?")
        p.add_argument("--no-build", action="store_true", help="sketches: take build/release as it is")
        for k in CART_SET:
            p.add_argument(f"--{k}")
    p = sub.add_parser("add", help="add games")
    p.add_argument("pkg")
    p.add_argument("items", nargs="+")
    p.add_argument("--folder")
    p.add_argument("--at", type=int, help="position (0 = first)")
    p.add_argument("--no-build", action="store_true")
    p = sub.add_parser("remove", help="remove games")
    p.add_argument("pkg")
    p.add_argument("ids", nargs="+")
    p = sub.add_parser("order", help="reorder games and folders")
    p.add_argument("pkg")
    p.add_argument("ids", nargs="+", metavar="ID|FOLDER/")
    p = sub.add_parser("set", help="edit details")
    p.add_argument("pkg")
    p.add_argument("pairs", nargs="+", metavar="KEY=VALUE")
    p.add_argument("--game", help="a game's id (default: the cart's own details)")
    p = sub.add_parser("launch", help="the game started at power-on")
    p.add_argument("pkg")
    p.add_argument("id")
    p = sub.add_parser("background", help="the menu's picture (any image; converted to fit)")
    p.add_argument("pkg")
    p.add_argument("png", metavar="image")
    p.add_argument("--folder", help="a folder's own picture instead of the menu's")
    p.add_argument("--color", action="append", metavar="KEY=#RRGGBB",
                   help="the menu's text, disabled, selectedText or mark colour")
    p.add_argument("--fit", choices=["cover", "contain"], default="cover")
    p.add_argument("--dither", action="store_true")
    p = sub.add_parser("picture", help="the visual menu's pictures (any image; converted to fit)")
    p.add_argument("pkg")
    p.add_argument("png", metavar="image", help="the picture, or none to remove it")
    w = p.add_mutually_exclusive_group()
    w.add_argument("--game", help="a game's picture (its cartImage)")
    w.add_argument("--folder", help="a folder's cover")
    w.add_argument("--about", action="store_true", help="the about page (B at the top)")
    w.add_argument("--system", choices=model.SYSTEM_IMAGES, metavar="SCREEN",
                   help="one of the menu's own screens: " + ", ".join(model.SYSTEM_IMAGES)
                        + " (none: the default again)")
    p.add_argument("--fit", choices=["cover", "contain"], default="cover")
    p.add_argument("--dither", action="store_true")
    p = sub.add_parser("art", help="pictures drawn for the games and folders that have none")
    p.add_argument("pkg")
    p.add_argument("--redo", action="store_true", help="redraw every game's and folder's picture from its title")
    p = sub.add_parser("prepare", help="the card's files")
    p.add_argument("pkg")
    p.add_argument("outdir")
    p.add_argument("--image", help="also a FAT32 card image")
    device_help = "the board the card or upload is for (default rev0; spec/chgame.md, the device table)"
    p.add_argument("--device", choices=list(model.DEVICES), default="rev0", help=device_help)
    p = sub.add_parser("flash", help="upload one game")
    p.add_argument("pkg")
    p.add_argument("--game")
    p.add_argument("--port")
    p.add_argument("--device", choices=list(model.DEVICES), default="rev0", help=device_help)
    p = sub.add_parser("deploy", help="flash and/or write the card, by the deploy rules")
    p.add_argument("pkg")
    p.add_argument("--card", help="the mounted card's folder (drive)")
    p.add_argument("--port")
    p.add_argument("--clean", action="store_true", help="empty the card's GAMES/ first (several games)")
    p.add_argument("--no-flash", action="store_true")
    p.add_argument("--device", choices=list(model.DEVICES), default="rev0", help=device_help)
    p = sub.add_parser("backup", help="a card's games back into a cart, with their SD files")
    p.add_argument("card", help="the mounted card's folder (drive), a FAT image, or a ZIP of its files")
    p.add_argument("out", help="the .chgame to write")
    p.add_argument("--game", action="append", metavar="PATH|ID",
                   help="only this game (its CHG file's path on the card, its id or its title); again for more. "
                        "Without it: every game, with the card's folders, menu and launch game")
    p.add_argument("--sd", action="append", metavar="CHG=PATH",
                   help="an SD file of a game whose CHG file has no record, e.g. GAMES/WORDS.CHG=WORDS.DIC")
    p.add_argument("--title", help="the cart's title (the card does not hold one)")
    return ap


def main(argv=None):
    a = parser().parse_args(argv)
    try:
        return globals()[f"cmd_{a.cmd}"](a)
    except CartError as e:
        print(e, file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def background_main(argv):
    """`chgame background`: the menu's picture (docs/menu-image.md)."""
    ap = argparse.ArgumentParser(prog="chgame background", description=background.__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", nargs="?", help="any picture: PNG, JPEG, BMP, GIF ...")
    ap.add_argument("--template", metavar="OUT.png", help="write the default picture (the CHGAME logo), to edit")
    ap.add_argument("--out", metavar="OUT.png", help="write the picture as the menu will use it")
    ap.add_argument("--preview", metavar="FILE", help="the menu drawn on it: .png, or .gif with the rainbow turning")
    ap.add_argument("--card", metavar="DIR", help="write it to a mounted card (GAMES/MENU.BG)")
    ap.add_argument("--fit", choices=["cover", "contain"], default="cover",
                    help="not 128x128: crop to fill (cover) or add black bars (contain)")
    ap.add_argument("--dither", action="store_true", help="dither when reducing colours (photos)")
    ap.add_argument("--color", action="append", metavar="KEY=#RRGGBB",
                    help="the menu's text, disabled, selectedText or mark colour, for --preview and --card")
    ap.add_argument("--style", choices=["rainbow", "static"], default="rainbow",
                    help="--preview as the rainbow bootloader (default) or the static one draws it")
    a = ap.parse_args(argv)
    try:
        if a.template:
            pathlib.Path(a.template).write_bytes(background.template())
            print(f"{a.template}: the default picture, 128x128. Edit it, then: chgame background {a.template} --preview preview.gif")
            if not a.image:
                return 0
        if not a.image:
            ap.error("give an image (or --template OUT.png)")
        ui = background.colors_arg(a.color)
        png, notes = background.convert(a.image, ui, a.fit, a.dither)
        print(f"{a.image}: " + ("ready as it is" if not notes else "converted"))
        for n in notes:
            print(f"  {n}")
        if a.out:
            pathlib.Path(a.out).write_bytes(png)
            print(f"{a.out}: written")
        if a.preview:
            background.save_preview(png, a.preview, ui, style=a.style)
            print(f"{a.preview}: the menu on it")
        if a.card:
            print(f"{background.write_to_card(png, a.card, ui)}: written (eject the card before the CHGame reads it)")
        if not (a.out or a.preview or a.card):
            print("nothing written: add --preview FILE to see it, --out FILE to keep it, --card DRIVE to use it")
        return 0
    except CartError as e:
        print(e, file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def picture_main(argv):
    """`chgame picture`: the visual menu's pictures (docs/visual-menu.md)."""
    from . import picture
    ap = argparse.ArgumentParser(prog="chgame picture", description=picture.__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", nargs="?", help="any picture: PNG, JPEG, BMP, GIF ...")
    ap.add_argument("--template", metavar="OUT.png", help="write a blank picture with the menu's marks shown, to paint on")
    ap.add_argument("--out", metavar="OUT.png", help="write the picture as the menu will use it")
    ap.add_argument("--preview", metavar="FILE", help="as the menu shows it: .png, or .gif fading in, installing, out")
    ap.add_argument("--card", metavar="DIR", help="write it to a mounted card as its cover (GAMES/COVER.PIC)")
    ap.add_argument("--fit", choices=["cover", "contain"], default="cover",
                    help="not 128x128: crop to fill (cover) or add black bars (contain)")
    ap.add_argument("--dither", action="store_true", help="dither when reducing colours (photos)")
    ap.add_argument("--style", choices=["rainbow", "static"], default="rainbow",
                    help="--preview as the rainbow bootloader (default) or the static one shows it")
    a = ap.parse_args(argv)
    try:
        if a.template:
            pathlib.Path(a.template).write_bytes(picture.template())
            print(f"{a.template}: a blank picture, 128x128. Paint it, then: chgame picture {a.template} --preview p.gif")
            if not a.image:
                return 0
        if not a.image:
            ap.error("give an image (or --template OUT.png)")
        png, notes = picture.convert(a.image, a.fit, a.dither)
        print(f"{a.image}: " + ("ready as it is" if not notes else "converted"))
        for n in notes:
            print(f"  {n}")
        if a.out:
            pathlib.Path(a.out).write_bytes(png)
            print(f"{a.out}: written")
        if a.preview:
            picture.save_preview(png, a.preview, style=a.style)
            print(f"{a.preview}: as the menu shows it")
        if a.card:
            print(f"{picture.write_to_card(png, a.card)}: written (eject the card before the CHGame reads it)")
        if not (a.out or a.preview or a.card):
            print("nothing written: add --preview FILE to see it, --out FILE to keep it, --card DRIVE to use it")
        return 0
    except CartError as e:
        print(e, file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def export_main(argv, sketch):
    ap = argparse.ArgumentParser(prog="chgame export", description="the sketch as a .chgame (build/<Name>.chgame)")
    ap.add_argument("--no-build", action="store_true", help="take build/release as it is")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    try:
        return cmd_export(a, sketch)
    except CartError as e:
        print(e, file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
