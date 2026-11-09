"""The conformance fixtures in spec/fixtures: carts, good and bad, and what
reading and preparing each must give.

    python tools/chcart/fixtures.py           write them (spec/fixtures/good, bad, expected)
    python tools/chcart/fixtures.py --check   compare chcart's results with expected/ (exit 1 on a difference)

Every game's program is spec/fixtures/src/hello.bin, the CHGame library's
Hello example (a real program: an emulator can run any of these). Pictures
are drawn here. expected/<name>.json holds, for a good cart, the games as
read (ids, titles, folders, sizes and SHA-256 of their binaries and SD
files), the warning codes, and every file of the prepared card (size and
SHA-256); for a bad one, the error codes. Nothing in it depends on where a
writer put files inside the ZIP, so another implementation can be held to
it. backup/<name>.zip are cards (their files in a ZIP), and
expected/backup/<name>.json what backing each up must give (backup.py). The
test (tools/chcart/tests) runs --check.
"""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import struct
import sys
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from chcart import backup, model, runtime, zipio  # noqa: E402
from chcart.model import Cart, Game  # noqa: E402

FIX = HERE.parents[1] / "spec" / "fixtures"
HELLO = FIX / "src" / "hello.bin"


def png(draw, size=128, fmt="PNG", frames=1):
    from PIL import Image, ImageDraw
    ims = []
    for f in range(frames):
        im = Image.new("RGB", (size, size), (0, 0, 0))
        draw(ImageDraw.Draw(im), f)
        ims.append(im)
    b = io.BytesIO()
    if frames > 1:
        ims[0].save(b, fmt, save_all=True, append_images=ims[1:], duration=200, loop=0)
    else:
        ims[0].save(b, fmt)
    return b.getvalue()


def background(d, f):
    d.rectangle([0, 0, 127, 127], fill=(10, 20, 60))
    d.rectangle([0, 0, 127, 16], fill=(255, 0, 255))           # the rainbow band
    d.rectangle([96, 24, 127, 127], fill=(0, 90, 40))
    d.rectangle([0, 118, 127, 127], fill=(128, 128, 128))       # = disabled: index 12
    d.line([(0, 17), (127, 17)], fill=(255, 244, 214))          # = text: index 11


def folder_background(d, f):
    d.rectangle([0, 0, 127, 127], fill=(60, 10, 10))
    d.ellipse([20, 20, 108, 108], fill=(255, 0, 255))


def shot(d, f):
    d.rectangle([8 + 8 * f, 8, 40 + 8 * f, 40], fill=(255, 200, 0))


def picture(rgb, square):
    """A picture for the visual menu: `rgb` behind, a #FF00FF bar, a square of `square`."""
    def draw(d, f):
        d.rectangle([0, 0, 127, 127], fill=rgb)
        d.rectangle([0, 100, 127, 107], fill=(255, 0, 255))
        d.rectangle([40, 30, 87, 77], fill=square)
        d.rectangle([2, 2, 5, 5], fill=(214, 32, 32))               # = mark: index 14
    return draw


def good():
    hello = HELLO.read_bytes()
    lic = {"LICENSE": b"Fixture licence text.\n"}
    single = Cart("HELLO", [Game("hello", "HELLO", {"rev0": hello}, version="1.0", author="fixtures",
                                 license="MIT", license_files=lic)])
    single_sd = Cart("HELLO WITH DATA", [Game(
        "hello-sd", "HELLO WITH DATA", {"rev0": hello}, description="Hello, with files for the SD card.",
        sd={"HELLO.TXT": b"hello, card\n", "DATA/INFO.DAT": bytes(range(256)) * 4},
        cart_image=png(shot),
        buttons=[("A", "say hello")])])
    shared = b"shared by two games\n"
    multi = Cart("FIXTURE CART", version="2.0", author="fixtures", date="2026-10-03", launch="inner",
                 background=png(background), colors={"text": "#FFF4D6", "mark": "#FF8000"},
                 folder_backgrounds={"TOYS": png(folder_background)}, games=[
                     Game("zulu", "ZULU", {"rev0": hello}, sd={"SHARED.DAT": shared}),
                     Game("alpha", "Alpha game", {"rev0": hello}, folder="TOYS"),
                     Game("inner", "INNER GAME", {"rev0": hello}, folder="TOYS/BOX", sd={"SHARED.DAT": shared}),
                     Game("words", "WORDS", {"rev0": hello}),
                     Game("words-2", "WORDS", {"rev0": hello}, folder="TOYS"),
                     Game("con", "CON", {"rev0": hello}),
                     Game("long", "A TITLE LONGER THAN THE MENU", {"rev0": hello}, author="an author with a long name")])
    pictures = Cart("PICTURES", cover=png(picture((20, 20, 80), (255, 200, 0))),
                    about=png(picture((80, 20, 20), (255, 255, 255))),
                    folder_covers={"CARDS": png(picture((0, 80, 30), (255, 244, 214))),
                                   "CARDS/CLASSIC": png(picture((60, 40, 0), (0, 200, 255)))},
                    folder_backgrounds={"CARDS": png(folder_background)}, games=[
                        Game("one", "ONE", {"rev0": hello}, cart_image=png(picture((90, 0, 90), (0, 255, 0)))),
                        Game("two", "TWO", {"rev0": hello}, folder="CARDS",
                             cart_image=png(picture((0, 60, 90), (255, 120, 0)))),
                        Game("three", "THREE", {"rev0": hello}, folder="CARDS/CLASSIC"),
                        Game("four", "FOUR", {"rev0": hello}, folder="DICE")])
    system = Cart("SYSTEM SCREENS", about=png(picture((30, 30, 30), (255, 244, 214))),
                  system_images={"installed": png(picture((0, 40, 80), (255, 255, 255))),
                                 "folder": png(picture((80, 60, 0), (255, 0, 255))),
                                 "error-4": png(picture((100, 0, 0), (255, 200, 0)))},
                  games=[Game("one", "ONE", {"rev0": hello}), Game("two", "TWO", {"rev0": hello}, folder="MORE")])
    return {"single": single, "single-sd": single_sd, "multi": multi, "pictures": pictures, "system": system}


def extension_cart():
    """A cart written by the web tool before menu.systemImages existed: its
    x-chgame-web (version 1) names two system screens, the official field
    names one of them differently (it wins: extension-conflict), and another
    x- key rides along. Written raw: chcart itself writes the official field."""
    hello = HELLO.read_bytes()
    inst, folder, other = (png(picture((0, 40, 80), (255, 255, 255))), png(picture((80, 60, 0), (255, 0, 255))),
                           png(picture((10, 10, 60), (0, 255, 0))))
    m = {"schemaVersion": 1, "title": "WEB CART",
         "menu": {"systemImages": {"installed": "menu/official-installed.png"}},
         "games": [{"id": "one", "title": "ONE", "binaries": [{"device": "rev0", "filename": "one.bin"}]}],
         "x-chgame-web": {"version": 1, "builder": "fixture", "systemImages": {"installed": "art/installed.png",
                                                                               "folder": "art/missing-folder.png"}},
         "x-other-tool": {"note": "kept as it is"}}
    return raw([("info.json", json.dumps(m, indent=2).encode()), ("one.bin", hello),
                ("menu/official-installed.png", other), ("art/installed.png", inst), ("art/missing-folder.png", folder)])


def devices_cart():
    """A cart from a writer that knows boards this reader does not: each game
    has its rev0 binary and one for another board, rev1 (reserved, not yet
    defined) or other-board (unknown). Those are unknown-device warnings, not
    used and kept, and the card is the rev0 binaries' (spec/chgame.md,
    "Devices and revisions"). Written raw: chcart writes what it is given."""
    hello = HELLO.read_bytes()
    m = {"schemaVersion": 1, "title": "TWO BOARDS", "games": [
        {"id": "one", "title": "ONE", "binaries": [{"device": "rev0", "filename": "one/rev0.bin"},
                                                   {"device": "rev1", "filename": "one/rev1.bin"}]},
        {"id": "two", "title": "TWO", "binaries": [{"device": "other-board", "filename": "two/other.bin"},
                                                   {"device": "rev0", "filename": "two/rev0.bin"}]}]}
    return raw([("info.json", json.dumps(m, indent=2).encode()), ("one/rev0.bin", hello),
                ("one/rev1.bin", bytes(range(64))), ("two/other.bin", bytes(range(64, 128))),
                ("two/rev0.bin", hello)])


def raw(entries):
    """A ZIP of exactly these (name, bytes), stored: bad carts are written
    around chcart's checks."""
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        for n, d in entries:
            zi = zipfile.ZipInfo("x", (1980, 1, 1, 0, 0, 0))
            zi.filename = n
            z.writestr(zi, d)
    return b.getvalue()


def bad():
    """{error code: bytes of a cart that breaks exactly that rule}."""
    img = bytes(range(64))
    boot = bytearray(img)
    struct.pack_into("<I", boot, 8, model.BOOT_SIG)

    def cart(games, **top):
        m = {"schemaVersion": 1, "title": "BAD", **top, "games": games}
        return m

    def g(gid="a", title="A", **kw):
        return {"id": gid, "title": title, "binaries": [{"device": "rev0", "filename": "a.bin"}], **kw}

    def z(m, extra=()):
        return raw([("info.json", json.dumps(m).encode()), ("a.bin", img), *extra])

    from PIL import Image
    many = Image.new("RGB", (128, 128))
    for i in range(12):
        many.putpixel((i, 0), (i + 1, 0, 0))
    b = io.BytesIO()
    many.save(b, "PNG")
    return {
        "not-a-zip": b"this is not a ZIP file\n",
        "bad-zip": raw([("info.json", b"{}"), ("../escape.bin", img)]),
        "no-manifest": raw([("a.bin", img)]),
        "bad-json": raw([("info.json", b"{\"schemaVersion\": 1,")]),
        "schema-version": z(dict(cart([g()]), schemaVersion=2)),
        "missing-field": z({"schemaVersion": 1, "title": "BAD"}),
        "bad-field": z(cart([g(author=7)])),
        "missing-file": z(cart([g(cartImage="nope.png")])),
        "bad-id": z(cart([g("Not An Id")])),
        "duplicate-id": z(cart([g(), g(title="B")])),
        "bad-title": z(cart([g(title="T" * 32)])),
        "bad-folder": z(cart([g(folder="A/B/C/D/E")])),
        "bad-device": z(cart([{"id": "a", "title": "A", "binaries": [{"device": "REV0", "filename": "a.bin"}]}])),
        "binary-size": raw([("info.json", json.dumps(cart([g()])).encode()), ("a.bin", bytes(50948))]),
        "bootloader-image": raw([("info.json", json.dumps(cart([g()])).encode()), ("a.bin", bytes(boot))]),
        "bad-sd-path": z(cart([g(sdcard="sd/")]), [("sd/words.dic", b"x")]),
        "sd-conflict": z(cart([g(sdcard="a/"), g("b", "B", sdcard="b/")]), [("a/X.DAT", b"1"), ("b/X.DAT", b"2")]),
        "bad-image": z(cart([g(cartImage="c.png")]), [("c.png", png(shot, 64))]),
        "bad-background": z(cart([g()], menu={"background": "bg.png"}), [("bg.png", b.getvalue())]),
        "bad-picture": z(cart([g()], menu={"cover": "c.png"}), [("c.png", b.getvalue())]),
        "bad-launch": z(cart([g()], launch="nobody")),
        "full-folder": z(cart([g(f"g{i}", f"G{i}") for i in range(model.FOLDER_ENTRIES + 1)])),
    }


def warnings_cart():
    m = {"schemaVersion": 1, "title": "WARNINGS", "colour": "red", "games": [
        {"id": "a", "title": "A TITLE OF TWENTY ONE", "binaries": [{"device": "rev0", "filename": "a.bin"}]},
        {"id": "b", "title": "B{}", "binaries": [{"device": "rev0", "filename": "b.bin"}]}]}
    return raw([("info.json", json.dumps(m).encode()), ("a.bin", HELLO.read_bytes()),
                ("b.bin", HELLO.read_bytes() + bytes(50440 - len(HELLO.read_bytes()))), ("README.txt", b"stray\n")])


def sha(b):
    return hashlib.sha256(b).hexdigest()


def result(data):
    """What expected/ records for a cart's bytes."""
    issues = zipio.check(data)
    errors = sorted({i.code for i in issues if i.error})
    if errors:
        return {"errors": errors}
    cart = zipio.load(data)
    return {
        "warnings": sorted({i.code for i in issues if not i.error}),
        "games": [{"id": g.id, "title": g.title, "folder": g.folder,
                   "binaries": {d: {"size": len(b), "sha256": sha(b)} for d, b in g.binaries.items()},
                   "sdcard": {p: sha(b) for p, b in sorted(g.sd.items())}} for g in cart.games],
        "launch": cart.launch,
        "card": {p: {"size": len(b), "sha256": sha(b)} for p, b in runtime.prepare(cart).items()},
    }


def backup_cards():
    """{name: the card's files}: cards to back up (spec/card.md, "Backing up
    a card"). Three as preparation wrote them, one changed by hand, one from
    before records."""
    carts = good()
    out = {n: runtime.prepare(carts[n]) for n in ("multi", "pictures", "system")}
    hello = HELLO.read_bytes()
    shared = b"shared by two games\n"
    cart = Cart("EDITED", games=[
        Game("words", "WORDS", {"rev0": hello}, version="1.0", author="fixtures", license="MIT",
             license_files={"LICENSE": b"Fixture licence text.\n"}, sd={"WORDS.DIC": b"words\n" * 50}),
        Game("cross", "CROSS", {"rev0": hello}, folder="PUZZLES",
             sd={"CHCW/A.CWD": b"puzzle a\n", "CHCW/B.CWD": b"puzzle b\n"}),
        Game("twin-a", "TWIN A", {"rev0": hello}, sd={"SHARED.DAT": shared}),
        Game("twin-b", "TWIN B", {"rev0": hello}, folder="PUZZLES", sd={"SHARED.DAT": shared}),
        Game("solo", "SOLO", {"rev0": hello}, cart_image=png(picture((90, 0, 90), (0, 255, 0)))),
        Game("dented", "DENTED", {"rev0": hello})])
    f = runtime.prepare(cart)
    del f["CHCW/B.CWD"]                                         # gone: sd-missing
    f["SHARED.DAT"] = b"changed by hand\n"                      # changed: sd-changed, for both twins
    f["GAMES/PUZZLES/SOLO.CHG"] = f.pop("GAMES/SOLO.CHG")       # moved by hand: in no MENU.IDX
    f["GAMES/PUZZLES/WORDS.CHG"] = f["GAMES/WORDS.CHG"]         # copied: renamed-id
    f["GAMES/HANDMADE.CHG"] = runtime.chgpack.pack(hello, "HANDMADE", "me", "0.1")      # no-record
    broken = bytearray(f["GAMES/WORDS.CHG"])
    broken[600] ^= 0xFF
    f["GAMES/BROKEN.CHG"] = bytes(broken)                       # payload damaged: bad-chg
    dented = bytearray(f["GAMES/DENTED.CHG"])
    dented[-2] ^= 0xFF
    f["GAMES/DENTED.CHG"] = bytes(dented)                       # record damaged: bad-record
    f["README.TXT"] = b"not any game's\n"
    out["edited"] = f
    old = runtime.prepare(carts["single-sd"])                   # CHG files from before records
    for p in [p for p in old if p.endswith(".CHG")]:
        data = old[p]
        info = runtime.chgpack.parse(data)
        old[p] = runtime.chgpack.pack(data[512:512 + info["payload_bytes"]], info["title"], info["author"],
                                      info["version"], picture=runtime.chgpack.read_picture(data))
    out["old"] = old
    return out


def backup_result(files):
    """What expected/backup/ records for backing a card up."""
    cart, issues = backup.backup(files)
    ui = cart.ui_colors()
    pic = lambda png: sha(runtime.menu_picture(png)) if png is not None and model.picture_ok(png) else None
    return {
        "warnings": sorted({i.code for i in issues}),
        "games": [{"id": g.id, "title": g.title, "folder": g.folder,
                   **{k: getattr(g, k) for k in runtime.RECORD_TEXT if getattr(g, k)},
                   "binaries": {d: {"size": len(b), "sha256": sha(b)} for d, b in g.binaries.items()},
                   "sdcard": {p: sha(b) for p, b in sorted(g.sd.items())},
                   "licenseFiles": {n: sha(b) for n, b in sorted(g.license_files.items())},
                   "picture": pic(g.cart_image)} for g in cart.games],
        "launch": cart.launch,
        "menu": {"colors": dict(sorted(cart.colors.items())),
                 "background": sha(runtime.menu_background(cart.background, ui)) if cart.background else None,
                 "cover": pic(cart.cover), "about": pic(cart.about),
                 "systemImages": {k: pic(v) for k, v in sorted(cart.system_images.items())},
                 "folders": {n: {"background": sha(runtime.menu_background(cart.folder_backgrounds[n], ui))
                                 if n in cart.folder_backgrounds else None,
                                 "cover": pic(cart.folder_covers.get(n))}
                             for n in sorted(set(cart.folder_backgrounds) | set(cart.folder_covers))}},
        "sameCard": runtime.prepare(cart) == files,
    }


def everything():
    out = {f"good/{n}.chgame": zipio.to_bytes(c) for n, c in good().items()}
    out["good/warnings.chgame"] = warnings_cart()
    out["good/extension.chgame"] = extension_cart()
    out["good/devices.chgame"] = devices_cart()
    out.update({f"bad/{code}.chgame": data for code, data in bad().items()})
    return out


def write():
    for rel, data in everything().items():
        f = FIX / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        e = FIX / "expected" / (f.stem + ".json")
        e.parent.mkdir(parents=True, exist_ok=True)
        e.write_text(json.dumps(result(data), indent=1) + "\n", newline="\n", encoding="utf-8")
        print(rel)
    for name, files in backup_cards().items():
        f = FIX / "backup" / f"{name}.zip"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(backup.card_zip(files))
        e = FIX / "expected" / "backup" / f"{name}.json"
        e.parent.mkdir(parents=True, exist_ok=True)
        e.write_text(json.dumps(backup_result(files), indent=1) + "\n", newline="\n", encoding="utf-8")
        print(f"backup/{name}.zip")


def check(log=print):
    """[(fixture, problem)] between chcart's results and expected/."""
    bad_ = []
    for f in sorted((FIX / "good").glob("*.chgame")) + sorted((FIX / "bad").glob("*.chgame")):
        want = json.loads((FIX / "expected" / (f.stem + ".json")).read_text(encoding="utf-8"))
        got = result(f.read_bytes())
        if f.parent.name == "bad" and want.get("errors") != [f.stem]:
            bad_.append((f.name, f"expected/{f.stem}.json should name exactly the error {f.stem}"))
        if got != want:
            bad_.append((f.name, "differs from expected/" + f.stem + ".json"))
    for f in sorted((FIX / "backup").glob("*.zip")):
        want = json.loads((FIX / "expected" / "backup" / (f.stem + ".json")).read_text(encoding="utf-8"))
        if backup_result(backup.open_card(f).files) != want:
            bad_.append((f"backup/{f.name}", "differs from expected/backup/" + f.stem + ".json"))
    for name, why in bad_:
        log(f"{name}: {why}")
    return bad_


if __name__ == "__main__":
    if "--check" in sys.argv:
        problems = check()
        print("fixtures: " + ("ok" if not problems else f"{len(problems)} differ"))
        sys.exit(1 if problems else 0)
    write()
