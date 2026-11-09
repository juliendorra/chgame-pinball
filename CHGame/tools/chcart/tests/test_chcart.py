"""chcart's tests: the format's rules, the ZIP reader's refusals, the imports,
runtime preparation byte for byte, the editing commands.

    python -m unittest discover -s tools/chcart/tests
"""
import io
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

TOOLS = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TOOLS))

import chgpack  # noqa: E402
from chcart import cli, model, runtime, sources, zipio  # noqa: E402
from chcart.model import Cart, CartError, Game  # noqa: E402


def image(n, seed=1):
    return bytes((i * 31 + seed * 17) & 0xFF for i in range(n))


def png(size=(128, 128), colors=((0, 0, 0),), mode="RGB", fmt="PNG"):
    from PIL import Image
    im = Image.new(mode, size, colors[0])
    for k, c in enumerate(colors[1:], 1):
        im.putpixel((k % size[0], k // size[0]), c)
    b = io.BytesIO()
    im.save(b, fmt)
    return b.getvalue()


def game(gid="one", title="ONE", **kw):
    return Game(id=gid, title=title, binaries={"rev0": image(kw.pop("n", 1000), len(gid))}, **kw)


def codes(issues, errors=True):
    return sorted({i.code for i in issues if i.error == errors})


class Format(unittest.TestCase):
    def test_round_trip_and_same_bytes(self):
        c = Cart("CART", [game("one", "ONE", sd={"DATA/X.DAT": b"x"}, license_files={"LICENSE": b"L"},
                               cart_image=png(), buttons=[("A", "go")]),
                          game("two", "TWO", folder="F/G")],
                 version="1.0", author="me", launch="two", background=png(), colors={"text": "#FFFFFF"},
                 folder_backgrounds={"F": png()}, cover=png(colors=((1, 1, 1),)), about=png(colors=((2, 2, 2),)),
                 folder_covers={"F/G": png(colors=((3, 3, 3),))})
        a = zipio.to_bytes(c)
        self.assertEqual(a, zipio.to_bytes(c))
        back = zipio.load(a)
        self.assertEqual(zipio.to_bytes(back), a)
        self.assertEqual(back.game("one").sd, {"DATA/X.DAT": b"x"})
        self.assertEqual(back.folders(), ["F", "F/G"])
        self.assertEqual((back.cover, back.about, back.folder_covers), (c.cover, c.about, c.folder_covers))
        names = zipfile.ZipFile(io.BytesIO(a)).namelist()
        self.assertEqual(names[0], "info.json")
        self.assertIn("one/rev0.bin", names)
        self.assertIn("one/sdcard/DATA/X.DAT", names)

    def test_errors(self):
        bad = [
            ("duplicate-id", Cart("C", [game("a"), game("a", "B")])),
            ("bad-id", Cart("C", [game("A b")])),
            ("bad-title", Cart("C", [game("a", "")])),
            ("bad-title", Cart("C", [game("a", "X" * 32)])),
            ("bad-title", Cart("C", [game("a", "café")])),
            ("bad-folder", Cart("C", [game("a", folder="A/B/C/D/E")])),
            ("bad-folder", Cart("C", [game("a", folder=" A")])),
            ("bad-sd-path", Cart("C", [game("a", sd={"words.dic": b""})])),
            ("bad-sd-path", Cart("C", [game("a", sd={"GAMES/X.CHG": b""})])),
            ("bad-sd-path", Cart("C", [game("a", sd={"LONGFILENAME.DIC": b""})])),
            ("sd-conflict", Cart("C", [game("a", sd={"X.DAT": b"1"}), game("b", "B", sd={"X.DAT": b"2"})])),
            ("binary-size", Cart("C", [game("a", n=50945)])),
            ("bad-launch", Cart("C", [game("a")], launch="b")),
            ("bad-image", Cart("C", [game("a", cart_image=png((64, 64)))])),
            ("bad-image", Cart("C", [game("a")], background=png(mode="RGBA", colors=((0, 0, 0, 0),)))),
            ("bad-background", Cart("C", [game("a")], background=png(colors=[(i, i, i) for i in range(1, 14)]))),
            ("missing-field", Cart("C", [])),
            ("bad-device", Cart("C", [Game("a", "A", {"Rev 0": image(10)})])),
            ("full-folder", Cart("C", [game(f"g{i}", f"G{i}", n=8) for i in range(model.FOLDER_ENTRIES + 1)])),
            ("full-folder", Cart("C", [game(f"g{i}", f"G{i}", n=8, folder=f"F{i}") for i in range(model.FOLDER_ENTRIES + 1)])),
        ]
        for code, c in bad:
            with self.subTest(code=code):
                self.assertIn(code, codes(model.validate(c)))
                with self.assertRaises(CartError):
                    zipio.to_bytes(c)
        boot = bytearray(image(100))
        struct.pack_into("<I", boot, 8, model.BOOT_SIG)
        self.assertIn("bootloader-image", codes(model.validate(Cart("C", [Game("a", "A", {"rev0": bytes(boot)})]))))

    def test_shared_sd_and_warnings(self):
        c = Cart("C", [game("a", "A" * 20, sd={"X.DAT": b"1"}), game("b", "B{", sd={"X.DAT": b"1"}, n=50436)])
        issues = model.validate(c)
        self.assertEqual(codes(issues), [])
        self.assertEqual(codes(issues, False), ["long-title", "save-pages", "title-chars"])
        self.assertEqual(model.validate(Cart("C", [game("a", "abc")])), [])     # a-z fold to capitals

    def test_manifest_shape(self):
        good = zipio.to_bytes(Cart("C", [game()]))
        files, m = zipio.read(good)

        def issues(m2, extra=None):
            f = dict(files, **(extra or {}))
            return model.from_manifest(m2, f)[1]
        self.assertIn("schema-version", codes(issues(dict(m, schemaVersion=2))))
        self.assertIn("schema-version", codes(issues({k: v for k, v in m.items() if k != "schemaVersion"})))
        self.assertIn("missing-file", codes(issues({**m, "games": [{**m["games"][0], "binaries": [
            {"device": "rev0", "filename": "nope.bin"}]}]})))
        self.assertIn("missing-field", codes(issues({k: v for k, v in m.items() if k != "games"})))
        self.assertIn("bad-field", codes(issues(dict(m, title=3))))
        w = issues(dict(m, colour="red"), {"stray.txt": b"x"})
        self.assertEqual(codes(w), [])
        self.assertEqual(codes(w, False), ["unknown-key", "unused-file"])
        # A cart from before screenshots left the format: read, without them
        old = {**m, "games": [{**m["games"][0], "screenshots": [{"filename": "a/screenshot-1.gif"}]}]}
        cart, w = model.from_manifest(old, dict(files, **{"a/screenshot-1.gif": b"GIF89a"}))
        self.assertEqual(codes(w), [])
        self.assertEqual(codes(w, False), ["unknown-key", "unused-file"])
        self.assertEqual(zipio.to_bytes(cart), good)


class Zip(unittest.TestCase):
    def zipped(self, entries, method=zipfile.ZIP_DEFLATED):
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w", method) as z:
            for n, d in entries:
                zi = zipfile.ZipInfo("x")
                zi.filename = n                 # as given: ZipInfo() would turn '\' into '/' on Windows
                zi.compress_type = method
                z.writestr(zi, d)
        return b.getvalue()

    def code(self, data):
        with self.assertRaises(CartError) as e:
            zipio.read(data)
        return e.exception.code

    def test_refusals(self):
        info = json.dumps({"schemaVersion": 1}).encode()
        self.assertEqual(self.code(b"not a zip"), "not-a-zip")
        self.assertEqual(self.code(self.zipped([("x.txt", b"")])), "no-manifest")
        self.assertEqual(self.code(self.zipped([("info.json", b"{")])), "bad-json")
        self.assertEqual(self.code(self.zipped([("info.json", info), ("../evil", b"")])), "bad-zip")
        self.assertEqual(self.code(self.zipped([("info.json", info), ("/abs", b"")])), "bad-zip")
        self.assertEqual(self.code(self.zipped([("info.json", info), ("a\\b", b"")])), "bad-zip")
        self.assertEqual(self.code(self.zipped([("info.json", info), ("A.bin", b""), ("a.bin", b"")])), "bad-zip")
        self.assertEqual(self.code(self.zipped([("info.json", info)], zipfile.ZIP_BZIP2)), "bad-zip")
        self.assertEqual(zipio.read(self.zipped([("info.json", info), ("dir/", b"")]))[1], {"schemaVersion": 1})


class Sources(unittest.TestCase):
    def test_hex(self):
        def rec(addr, kind, data):
            b = bytes([len(data), addr >> 8, addr & 0xFF, kind]) + data
            return ":" + (b + bytes([-sum(b) & 0xFF])).hex().upper()
        text = "\n".join([rec(0, 4, b"\x00\x00"), rec(0x3000, 0, b"\x01\x02"), rec(0x3004, 0, b"\x05"),
                          rec(0, 1, b"")])
        self.assertEqual(sources.hex_to_bin(text), b"\x01\x02\xff\xff\x05")
        with self.assertRaises(ValueError):
            sources.hex_to_bin(rec(0x2FFF, 0, b"\x01"))
        with self.assertRaises(ValueError):
            sources.hex_to_bin(":0100000001FF")          # bad checksum

    @staticmethod
    def elf(segments, machine=243, kind=2):
        """A 32-bit little-endian ELF executable with these PT_LOAD segments:
        [(paddr, bytes, filesz or None for a .bss-like segment)]."""
        phoff, phsize = 52, 32
        data_at = phoff + phsize * len(segments)
        head = bytearray(b"\x7fELF\x01\x01\x01" + bytes(9))
        head += struct.pack("<HHIIIIIHHHHHH", kind, machine, 1, 0x3000, phoff, 0, 0, 52, phsize, len(segments), 0, 0, 0)
        ph, body = bytearray(), bytearray()
        for paddr, blob, filesz in segments:
            n = len(blob) if filesz is None else filesz
            ph += struct.pack("<IIIIIIII", 1, data_at + len(body), 0x20000000 if filesz is not None else paddr,
                              paddr, n, len(blob), 6, 4)
            body += blob[:n]
        return bytes(head + ph + body)

    def test_elf(self):
        text, data = b"\x6f\x00\x00\x01" + bytes(range(60)), b"\x11\x22\x33\x44"
        e = self.elf([(0x3000, text, None), (0x3000 + 72, data, 4), (0x20000100, bytes(40), 0)])   # text, .data (LMA in flash), .bss
        self.assertEqual(sources.elf_to_bin(e), text + b"\xff" * 8 + data)
        self.assertEqual(sources.elf_to_bin(self.elf([(0x08003000, text, None)])), text)         # the flash alias
        for bad, why in ((self.elf([(0x0, text, None)]), "a bootloader"), (self.elf([(0x3000, text, None)], machine=40), "another board"),
                         (self.elf([(0x3000, text, None)], kind=1), "not an executable"), (b"MZ" + bytes(60), "not an ELF"),
                         (self.elf([(0x3000, text, None), (0x3010, data, None)]), "overlap")):
            with self.subTest(why), self.assertRaises(ValueError):
                sources.elf_to_bin(bad)
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "My Game.ino.elf"
            p.write_bytes(e)
            g = sources.from_binary(p)
            self.assertEqual((g.title, g.binary()), ("MY GAME", text + b"\xff" * 8 + data))
            self.assertEqual(sources.load_item(p)[0].binary(), g.binary())
            self.assertEqual(chgpack.program_image(str(p)), g.binary())
        # the real thing: any example built here gives its .bin from its .elf
        built = sorted(TOOLS.parent.glob("platform/board/arduino/CHGame/libraries/CHGame/examples/*/*/build/release/*.ino.elf"))
        for elf in built[:3]:
            b = elf.with_suffix(".bin")
            if b.exists():
                self.assertEqual(sources.elf_to_bin(elf.read_bytes()), b.read_bytes(), elf.name)

    def test_chg_and_bin(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "FOUR.CHG"
            p.write_bytes(chgpack.pack(image(4096), "FOUR IN A ROW", "me", "1.2"))
            g = sources.from_binary(p)
            self.assertEqual((g.id, g.title, g.author, g.version), ("four-in-a-row", "FOUR IN A ROW", "me", "1.2"))
            self.assertEqual(g.binary(), image(4096))
            b = pathlib.Path(d) / "My Game.ino.bin"
            b.write_bytes(image(10))
            self.assertEqual(sources.from_binary(b).title, "MY GAME")
            self.assertTrue(model.picture_ok(g.cart_image))                  # a picture drawn from its title
            pic = runtime.menu_picture(png(colors=((10, 60, 200), (255, 0, 255))))
            p.write_bytes(chgpack.pack(image(4096), "FOUR IN A ROW", picture=pic))
            self.assertEqual(runtime.menu_picture(sources.from_binary(p).cart_image), pic)   # the CHG's own

    def test_merge(self):
        a, b = game("x"), game("x")
        c = game("x", n=999)
        log = []
        out = sources.merge([a], [b, c], log.append)
        self.assertEqual([g.id for g in out], ["x", "x-2"])
        self.assertEqual(len(log), 2)

    def test_sketch(self):
        with tempfile.TemporaryDirectory() as d:
            s = pathlib.Path(d) / "CHDemo"
            (s / "sdcard" / "SUB").mkdir(parents=True)
            (s / "sdcard" / "SUB" / "A.DAT").write_bytes(b"a")
            (s / "LICENSE").write_text("MIT License\n")
            (s / "README.md").write_text("# CHDemo\n\nA [demo](x) with *style*.\nMore.\n\n![gif](y)\n")
            (s / "config.h").write_text('#define DEMO_VERSION "2.5"\n')
            g = sources.from_sketch(s, image(64))
            self.assertEqual((g.id, g.title, g.version, g.license), ("chdemo", "CHDEMO", "2.5", "MIT"))
            self.assertEqual(g.description, "A demo with style. More.")
            self.assertEqual(g.sd, {"SUB/A.DAT": b"a"})
            self.assertEqual(list(g.license_files), ["LICENSE"])
            self.assertTrue(model.picture_ok(g.cart_image))                  # no docs/cart.png: one drawn
            (s / "docs").mkdir()
            (s / "docs" / "cart.png").write_bytes(png(colors=((1, 2, 3),)))
            self.assertEqual(sources.from_sketch(s, image(64)).cart_image, png(colors=((1, 2, 3),)))
            (s / "chgame.json").write_text(json.dumps({"title": "DEMO", "folder": "TOYS", "sdcard": ""}))
            g = sources.from_sketch(s, image(64))
            self.assertEqual((g.title, g.folder, g.sd), ("DEMO", "TOYS", {}))
            (s / "chgame.json").write_text(json.dumps({"titel": "X"}))
            with self.assertRaises(CartError):
                sources.from_sketch(s, image(64))


class Runtime(unittest.TestCase):
    def test_names(self):
        taken = set()
        got = [runtime.name83(t, taken, "CHG", "GAME") for t in ("WORDS", "WORDS", "Blackjack!", "BLACKJACK", "CON", "", "")]
        self.assertEqual(got, ["WORDS", "WORDS2", "BLACKJAC", "BLACKJA2", "CON2", "GAME", "GAME2"])
        self.assertEqual(runtime.name83("WORDS", taken, "", "FOLDER"), "WORDS")    # a folder: its own namespace

    def test_prepare(self):
        c = Cart("C", [game("z", "ZULU"), game("a", "ALPHA", folder="ONE"), game("b", "BRAVO", folder="ONE/TWO"),
                       game("m", "MIKE", sd={"M.DAT": b"m"})], launch="b")
        files = runtime.prepare(c)
        self.assertEqual(list(files), ["GAMES/MENU.IDX", "GAMES/MENU.BG", "GAMES/COVER.PIC", "GAMES/SYSTEM.PIC",
                                       "GAMES/ZULU.CHG", "GAMES/MIKE.CHG",
                                       "GAMES/ONE/MENU.IDX", "GAMES/ONE/ALPHA.CHG", "GAMES/ONE/TWO/MENU.IDX",
                                       "GAMES/ONE/TWO/BRAVO.CHG", "M.DAT"])
        idx = files["GAMES/MENU.IDX"]
        recs = [idx[i:i + 32] for i in range(0, len(idx), 32)]
        self.assertEqual(recs[0], b"CHX1" + bytes(28))
        self.assertEqual([r[:12] for r in recs[1:]], [b"ZULU    CHG\0", b"ONE        \1", b"MIKE    CHG\0"])
        self.assertEqual(recs[2][12:], b"ONE".ljust(20, b"\0"))
        two = files["GAMES/ONE/MENU.IDX"]
        self.assertEqual(two[32:44], b"ALPHA   CHG\0")
        self.assertEqual(two[64:76], b"TWO        \1")
        self.assertEqual(files["GAMES/ONE/TWO/MENU.IDX"][32:44], b"BRAVO   CHG\1")
        info = chgpack.parse(files["GAMES/ZULU.CHG"])
        self.assertEqual((info["title"], info["payload_bytes"]), ("ZULU", 1000))
        self.assertEqual(files["GAMES/MENU.BG"], runtime.menu_background(runtime.DEFAULT_BACKGROUND.read_bytes(),
                                                                         c.ui_colors()))
        self.assertEqual(runtime.prepare(c), files)

    def test_visual_files(self):
        """The visual menu's files: the covers, SYSTEM.PIC, a game's picture in its CHG."""
        cover, about, one, pic = png(colors=((0, 0, 90),)), png(colors=((90, 0, 0),)), png(colors=((0, 90, 0),)), \
            png(colors=((9, 9, 9), (255, 0, 255)))
        c = Cart("C", [game("z", "ZULU", cart_image=pic), game("a", "ALPHA", folder="ONE"),
                       game("b", "BRAVO", folder="ONE/TWO")], cover=cover, about=about, folder_covers={"ONE": one})
        files = runtime.prepare(c)
        self.assertEqual(files["GAMES/COVER.PIC"], runtime.menu_picture(cover))
        self.assertEqual(files["GAMES/ONE/COVER.PIC"], runtime.menu_picture(one))
        self.assertNotIn("GAMES/ONE/TWO/COVER.PIC", files)        # no cover of its own: none (no inheritance)
        self.assertNotIn("GAMES/ONE/SYSTEM.PIC", files)           # SYSTEM.PIC: GAMES/ only
        sysp = files["GAMES/SYSTEM.PIC"]
        self.assertEqual(len(sysp), 9 * runtime.BG_BYTES)
        self.assertEqual(sysp[:runtime.BG_BYTES], runtime.menu_picture(about))      # slot 0: the cart's about page
        self.assertEqual(sysp, runtime.system_pic(about))
        self.assertEqual(chgpack.read_picture(files["GAMES/ZULU.CHG"]), runtime.menu_picture(pic))
        self.assertIsNone(chgpack.read_picture(files["GAMES/ONE/ALPHA.CHG"]))
        bare = runtime.prepare(Cart("C", [game("z", "ZULU")]))
        self.assertEqual(bare["GAMES/COVER.PIC"], runtime.menu_picture(runtime.DEFAULT_COVER.read_bytes()))
        self.assertEqual(bare["GAMES/SYSTEM.PIC"][:runtime.BG_BYTES], runtime.menu_picture(runtime.DEFAULT_ABOUT.read_bytes()))

    def test_system_images(self):
        """menu.systemImages: a cart's own versions of the menu's screens go
        into SYSTEM.PIC's slots; the defaults fill the rest. The web tool's
        x-chgame-web (version 1) is read as an alias, the official field
        winning; other x- keys are kept as they are."""
        inst, err3 = png(colors=((9, 0, 9), (255, 0, 255))), png(colors=((0, 9, 9),))
        c = Cart("C", [game("z", "ZULU")], system_images={"installed": inst, "error-3": err3})
        self.assertEqual(codes(model.validate(c)), [])
        files = runtime.prepare(c)
        sysp, n = files["GAMES/SYSTEM.PIC"], runtime.BG_BYTES
        self.assertEqual(sysp[n:2 * n], runtime.menu_picture(inst))                    # slot 1
        self.assertEqual(sysp[6 * n:7 * n], runtime.menu_picture(err3))                # slot 6: error-3
        default = runtime.system_pic()
        self.assertEqual(sysp[2 * n:6 * n], default[2 * n:6 * n])                       # the rest: the defaults
        self.assertEqual(sysp[:n], default[:n])
        data = zipio.to_bytes(c)
        back = zipio.load(data)
        self.assertEqual(back.system_images, c.system_images)
        self.assertEqual(zipio.to_bytes(back), data)
        m = zipio.read(data)[1]
        self.assertEqual(m["menu"]["systemImages"], {"installed": "menu/system-installed.png", "error-3": "menu/system-error-3.png"})
        many = png(colors=[(k * 20, 0, 0) for k in range(13)])
        bad = Cart("C", [game("z", "ZULU")], system_images={"game": many})
        self.assertEqual(codes(model.validate(bad)), ["bad-picture"])                   # a supplied picture must follow the rule
        self.assertEqual(codes(model.validate(Cart("C", [game("z", "ZULU")], system_images={"game": png((64, 64))}))), ["bad-image"])
        unknown = Cart("C", [game("z", "ZULU")], system_images={"splash": inst})
        self.assertEqual(codes(model.validate(unknown), False), ["unknown-key"])
        # the extension: read where the official field says nothing
        files, m = zipio.read(zipio.to_bytes(Cart("C", [game("z", "ZULU")])))
        files = dict(files, **{"art/installed.png": inst, "art/folder.png": err3})
        ext = {"version": 1, "systemImages": {"installed": "art/installed.png", "folder": "art/folder.png"}, "builder": "web 1.2"}
        cart, issues = model.from_manifest({**m, "x-chgame-web": ext, "x-other": {"k": [1, 2]}}, files)
        self.assertEqual(codes(issues), [])
        self.assertEqual(codes(issues, False), [])                                      # no unknown-key for x- keys, nothing unused
        self.assertEqual(cart.system_images, {"installed": inst, "folder": err3})
        self.assertEqual(cart.extensions, {"x-chgame-web": {"version": 1, "builder": "web 1.2"}, "x-other": {"k": [1, 2]}})
        m2 = zipio.read(zipio.to_bytes(cart))[1]                                          # written back: the official field, the rest kept
        self.assertEqual(m2["menu"]["systemImages"], {"installed": "menu/system-installed.png", "folder": "menu/system-folder.png"})
        self.assertEqual((m2["x-chgame-web"], m2["x-other"]), ({"version": 1, "builder": "web 1.2"}, {"k": [1, 2]}))
        # both: the official field wins, a word where they differ; a bad alias picture is an error all the same
        both = {**m, "menu": {"systemImages": {"installed": "art/folder.png"}}, "x-chgame-web": ext}
        cart, issues = model.from_manifest(both, files)
        self.assertEqual(codes(issues, False), ["extension-conflict"])
        self.assertEqual(cart.system_images["installed"], err3)
        cart, issues = model.from_manifest({**m, "x-chgame-web": {"version": 1, "systemImages": {"game": "art/game.png"}}},
                                           dict(files, **{"art/game.png": many}))
        self.assertEqual(codes(issues), ["bad-picture"])
        # another version of the extension: not read as version 1 (its files are then unused), kept as it is
        cart, issues = model.from_manifest({**m, "x-chgame-web": {"version": 2, "systemImages": {"installed": "art/installed.png"}}}, files)
        self.assertEqual(cart.system_images, {})
        self.assertEqual(cart.extensions["x-chgame-web"]["version"], 2)
        self.assertIn("unused-file", codes(issues, False))

    def test_picture_rule(self):
        """Pictures keep the menu's colours at their defaults, whatever the cart's."""
        many = png(colors=[(k * 20, 0, 0) for k in range(13)])
        ok = png(colors=[(0, 0, 0), (255, 244, 214), (255, 0, 255)] + [(k * 20, 9, 9) for k in range(11)])
        self.assertEqual(codes(model.check_picture(ok, "x")), [])
        self.assertEqual(codes(model.check_picture(many, "x")), ["bad-picture"])
        self.assertEqual(codes(model.check_picture(png(size=(64, 64)), "x")), ["bad-image"])
        c = Cart("C", [game("z", "ZULU", cart_image=many)], cover=many, colors={"text": "#FFFFFF"})
        issues = model.validate(c)
        self.assertEqual(codes(issues), ["bad-picture"])                         # the cover: an error
        self.assertEqual(codes(issues, errors=False), ["bad-picture"])           # a cartImage: a warning
        c.cover = ok
        files = runtime.prepare(c)                                               # (the menu's text colour ignored)
        self.assertIsNone(chgpack.read_picture(files["GAMES/ZULU.CHG"]))         # no picture rather than a wrong one
        pal = struct.unpack_from("<16H", files["GAMES/COVER.PIC"], 8)
        self.assertEqual(pal[11], runtime.rgb565(255, 244, 214))

    def test_chg_picture(self):
        pic = runtime.menu_picture(png(colors=((1, 2, 3),)))
        for n in (4, 508, 1000, 1500):
            chg = chgpack.pack(image(n), "P", picture=pic)
            at, size, crc = struct.unpack_from("<III", chg, chgpack.IMAGE_OFF)
            self.assertEqual((at % 512, at >= 512 + n, size, len(chg)), (0, True, runtime.BG_BYTES, at + size))
            self.assertEqual(chgpack.read_picture(chg), pic)
            self.assertEqual(chgpack.parse(chg)["payload_bytes"], len(chgpack.pad_image(image(n))))
        bad = bytearray(chg)
        bad[-1] ^= 1
        with self.assertRaises(chgpack.ChgError) as e:
            chgpack.read_picture(bytes(bad))
        self.assertEqual(e.exception.code, 8)
        chgpack.parse(bytes(bad))                                                # (the game still installs)
        with self.assertRaises(ValueError):
            chgpack.pack(image(8), "P", picture=pic[:-1])

    def test_chg_fields(self):
        g = game("a", "A", author="A very long author name", version="1.2.3-beta")
        info = chgpack.parse(runtime.chg_file(g))
        self.assertEqual((info["author"], info["version"]), ("A very long aut", "1.2.3-b"))
        g = game("a", "A", author="José")
        self.assertEqual(chgpack.parse(runtime.chg_file(g))["author"], "")

    def test_background(self):
        colors = [(255, 0, 255), (10, 20, 30), (255, 244, 214), (40, 50, 60), (10, 20, 30)]
        from PIL import Image
        im = Image.new("RGB", (128, 128), (0, 0, 0))
        for x, c in enumerate(colors):
            im.putpixel((x, 0), c)
        b = io.BytesIO()
        im.save(b, "PNG")
        bg = runtime.menu_background(b.getvalue(), dict(model.UI_COLORS))
        self.assertEqual(len(bg), runtime.BG_BYTES)
        self.assertEqual(bg[:4], b"CHB1")
        pal = struct.unpack_from("<16H", bg, 8)
        self.assertEqual(pal[0], runtime.rgb565(10, 20, 30))
        self.assertEqual(pal[1], runtime.rgb565(40, 50, 60))
        self.assertEqual(pal[11], runtime.rgb565(255, 244, 214))
        self.assertEqual(pal[13], 0)                     # selectedText: black
        self.assertEqual(pal[15], 0xF81F)                # colour 15: #FF00FF (the static visual menu shows it)
        row = bg[512:512 + 3]
        # magenta 15, (10,20,30) 0, cream 11 (text), (40,50,60) 1, (10,20,30) 0, then black 13 (selectedText)
        self.assertEqual(row, bytes([0xF0, 0xB1, 0x0D]))


class Background(unittest.TestCase):
    def test_convert(self):
        from chcart import background
        from PIL import Image, ImageDraw
        default = background.template()
        self.assertEqual(background.convert(default), (default, []))      # ready: kept byte for byte
        im = Image.new("RGB", (300, 200))
        for x in range(300):
            for y in range(200):
                im.putpixel((x, y), (x * 255 // 299, y * 255 // 199, 90))
        ImageDraw.Draw(im).rectangle([140, 0, 160, 20], fill=(250, 12, 240))
        b = io.BytesIO()
        im.save(b, "PNG")
        png, notes = background.convert(b.getvalue())
        self.assertTrue(background.ready(png))
        self.assertEqual(len(notes), 3)                                   # scaled, magenta, colours
        px = model.rgb_pixels(png)
        self.assertIn(model.RAINBOW_RGB, px)
        self.assertLessEqual(len(model.background_colors(png, dict(model.UI_COLORS))), 11)
        big = Image.open(io.BytesIO(default)).resize((256, 256), Image.NEAREST)
        b = io.BytesIO()
        big.save(b, "PNG")
        self.assertEqual(model.rgb_pixels(background.convert(b.getvalue())[0]), model.rgb_pixels(default))
        rgba = Image.new("RGBA", (128, 128), (255, 255, 255, 0))
        b = io.BytesIO()
        rgba.save(b, "PNG")
        self.assertEqual(set(model.rgb_pixels(background.convert(b.getvalue())[0])), {(0, 0, 0)})

    def test_preview_and_card(self):
        from chcart import background
        im = background.preview(background.template())
        self.assertEqual(im.size, (384, 384))
        static = background.preview(background.template(), scale=1, style="static")
        self.assertEqual(static.getpixel((64, 25)), background.rgb(runtime.rgb565(255, 244, 214)))   # the bar: the text colour
        bars = {background.preview(background.template(), phase=p, scale=1).getpixel((64, 25)) for p in (0, 64, 128)}
        self.assertEqual(len(bars), 3)                                 # one colour, turning
        with tempfile.TemporaryDirectory() as d:
            f = background.write_to_card(background.template(), d)
            self.assertEqual(f.read_bytes(), runtime.menu_background(background.template(), dict(model.UI_COLORS)))
            background.save_preview(background.template(), pathlib.Path(d) / "p.gif")
            self.assertGreater((pathlib.Path(d) / "p.gif").stat().st_size, 0)
        self.assertEqual(background.colors_arg(["text=#ffffff"])["text"], "#FFFFFF")
        with self.assertRaises(ValueError):
            background.colors_arg(["txt=#FFFFFF"])

    def test_cart_command_converts(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "a.bin").write_bytes(image(100))
            pkg = str(d / "c.chgame")
            Image.new("RGB", (64, 32), (200, 30, 30)).save(d / "pic.jpg")
            self.assertEqual(cli.main(["new", pkg, str(d / "a.bin")]), 0)
            self.assertEqual(cli.main(["background", pkg, str(d / "pic.jpg"), "--color", "text=#FFFFFF"]), 0)
            c = zipio.load(pkg)
            self.assertEqual(model.image_info(c.background)[1:3], (128, 128))
            self.assertEqual(c.colors, {"text": "#FFFFFF"})
            self.assertEqual(cli.background_main([str(d / "pic.jpg"), "--card", str(d / "card")]), 0)
            self.assertEqual(len((d / "card" / "GAMES" / "MENU.BG").read_bytes()), runtime.BG_BYTES)

    def test_picture_commands(self):
        """chgame picture and chgame cart picture / art: any image converted to
        the picture rule; placeholders for what has none."""
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            im = Image.new("RGB", (300, 300))
            for x in range(300):
                for y in range(300):
                    im.putpixel((x, y), (x % 256, y % 256, 120))
            im.save(d / "photo.png")
            self.assertEqual(cli.picture_main([str(d / "photo.png"), "--out", str(d / "p.png"),
                                               "--preview", str(d / "p.gif"), "--card", str(d / "card")]), 0)
            self.assertTrue(model.picture_ok((d / "p.png").read_bytes()))
            self.assertEqual((d / "card" / "GAMES" / "COVER.PIC").read_bytes(), runtime.menu_picture((d / "p.png").read_bytes()))
            self.assertEqual(cli.picture_main(["--template", str(d / "t.png")]), 0)
            self.assertTrue(model.picture_ok((d / "t.png").read_bytes()))
            (d / "a.bin").write_bytes(image(100))
            pkg = str(d / "c.chgame")
            run = lambda *a: self.assertEqual(cli.main([str(x) for x in a]), 0)
            run("new", pkg, d / "a.bin")
            run("add", pkg, d / "a.bin", "--folder", "MORE")
            gid = zipio.load(pkg).games[0].id
            run("picture", pkg, d / "photo.png")
            run("picture", pkg, d / "photo.png", "--about")
            run("picture", pkg, d / "p.png", "--game", gid)
            self.assertEqual(cli.main(["picture", pkg, str(d / "p.png"), "--folder", "NOPE"]), 1)
            c = zipio.load(pkg)
            self.assertTrue(model.picture_ok(c.cover) and model.picture_ok(c.about))
            self.assertEqual(c.game(gid).cart_image, (d / "p.png").read_bytes())
            self.assertEqual(c.folder_covers, {})
            run("art", pkg)                                  # the folder's cover, drawn from its name
            c = zipio.load(pkg)
            self.assertEqual(list(c.folder_covers), ["MORE"])
            self.assertTrue(model.picture_ok(c.folder_covers["MORE"]))
            run("picture", pkg, "none", "--folder", "MORE")
            self.assertEqual(zipio.load(pkg).folder_covers, {})
            run("picture", pkg, d / "photo.png", "--system", "error-2")       # one of the menu's own screens
            c = zipio.load(pkg)
            self.assertEqual(list(c.system_images), ["error-2"])
            self.assertTrue(model.picture_ok(c.system_images["error-2"]))
            run("picture", pkg, "none", "--system", "error-2")
            self.assertEqual(zipio.load(pkg).system_images, {})
            with self.assertRaises(SystemExit):                       # not a screen of the menu: usage
                cli.main(["picture", pkg, str(d / "p.png"), "--system", "splash"])


class Deploy(unittest.TestCase):
    def test_rules(self):
        from chcart import deploy
        quiet = lambda s: None
        with tempfile.TemporaryDirectory() as d:
            card = pathlib.Path(d)
            # one game with SD files needs a card
            with self.assertRaises(CartError):
                deploy.deploy(Cart("C", [game("a", "WORDS", sd={"W.DIC": b"w"})]), None, do_flash=False, log=quiet)
            # a hand-copied older WORDS under another name is replaced in place; another game keeps WORDS.CHG
            (card / "GAMES").mkdir()
            (card / "GAMES" / "OLDWORDS.CHG").write_bytes(chgpack.pack(image(10), "WORDS"))
            (card / "GAMES" / "WORDS.CHG").write_bytes(chgpack.pack(image(20), "OTHER"))
            (card / "GAMES" / "MENU.IDX").write_bytes(b"theirs")
            deploy.deploy(Cart("C", [game("a", "WORDS", sd={"W.DIC": b"w"})]), card, do_flash=False, log=quiet)
            self.assertEqual(chgpack.parse((card / "GAMES" / "OLDWORDS.CHG").read_bytes())["payload_bytes"], 1000)
            self.assertEqual(chgpack.parse((card / "GAMES" / "WORDS.CHG").read_bytes())["title"], "OTHER")
            self.assertEqual((card / "W.DIC").read_bytes(), b"w")
            self.assertEqual((card / "GAMES" / "MENU.IDX").read_bytes(), b"theirs")   # its menu left alone
            deploy.deploy(Cart("C", [game("b", "NEW")]), card, do_flash=False, log=quiet)
            self.assertTrue((card / "GAMES" / "NEW.CHG").exists())
            # several games: the cart's menu replaces the card's; --clean empties GAMES/ first
            multi = Cart("C", [game("x", "XRAY"), game("y", "YANKEE", folder="F")])
            with self.assertRaises(CartError):
                deploy.deploy(multi, None, do_flash=False, log=quiet)
            deploy.deploy(multi, card, do_flash=False, log=quiet)
            self.assertEqual((card / "GAMES" / "MENU.IDX").read_bytes(), runtime.prepare(multi)["GAMES/MENU.IDX"])
            self.assertTrue((card / "GAMES" / "NEW.CHG").exists())
            deploy.deploy(multi, card, clean=True, do_flash=False, log=quiet)
            self.assertEqual(sorted(p.relative_to(card).as_posix() for p in (card / "GAMES").rglob("*") if p.is_file()),
                             sorted(p for p in runtime.prepare(multi) if p.startswith("GAMES/")))


class Backup(unittest.TestCase):
    """The record in each CHG file, and backing a card up from it (backup.py)."""

    def full_cart(self):
        pic = lambda c: png(colors=(c, (255, 0, 255)))
        return Cart("FULL", [
            game("words", "WORDS", version="1.2.3-beta", author="A very long author name", genre="Word",
                 description="Words. Café", license="MIT", url="https://example.org", buttons=[("A", "Lay a tile")],
                 license_files={"LICENSE": b"licence\n", "NOTICE": b"notice\n"}, cart_image=pic((9, 9, 90)),
                 sd={"WORDS.DIC": b"w" * 999, "DATA/X.DAT": b"x"}, n=1001),
            game("inner", "INNER", folder="TOYS/BOX", sd={"WORDS.DIC": b"w" * 999}),
            game("alpha", "Alpha", folder="TOYS", cart_image=png(colors=[(k, 0, 0) for k in range(13)])),  # 13 colours: no picture
            game("long", "A TITLE LONGER THAN THE MENU")],
            launch="inner", colors={"mark": "#FF8000", "text": "#FFFFFF"},
            background=png(colors=((10, 20, 60), (255, 0, 255), (255, 255, 255))),
            folder_backgrounds={"TOYS": png(colors=((60, 10, 10),))}, cover=pic((20, 20, 80)),
            about=pic((80, 20, 20)), folder_covers={"TOYS/BOX": pic((0, 80, 30))},
            system_images={"installed": pic((0, 40, 80)), "error-4": pic((100, 0, 0))})

    def test_record(self):
        c = self.full_cart()
        g = c.games[0]
        chg = runtime.chg_file(g)
        rec = chgpack.read_record(chg)
        self.assertEqual(rec, runtime.record(g))
        at, n, _ = struct.unpack_from("<III", chg, chgpack.RECORD_OFF)
        pic_at, pic_n, _ = struct.unpack_from("<III", chg, chgpack.IMAGE_OFF)
        self.assertEqual((at % 512, at >= pic_at + pic_n, len(chg)), (0, True, at + n))
        r = json.loads(rec)
        self.assertEqual(r["game"]["author"], "A very long author name")       # all of it: the header holds 15
        self.assertEqual(r["binaryBytes"], 1001)
        self.assertEqual(r["sdcard"], [{"bytes": 1, "crc32": "8cdc1683", "path": "DATA/X.DAT"},
                                       {"bytes": 999, "crc32": f"{__import__('zlib').crc32(b'w' * 999):08x}",
                                        "path": "WORDS.DIC"}])
        self.assertIn(b"Caf\\u00e9", rec)                                      # canonical: ASCII only, keys sorted
        self.assertEqual(rec, json.dumps(r, sort_keys=True, separators=(",", ":")).encode())
        self.assertIsNone(chgpack.read_record(chgpack.pack(image(8), "P")))      # none: the field is 0
        bad = bytearray(chg)
        bad[-1] ^= 1
        with self.assertRaises(chgpack.ChgError) as e:
            chgpack.read_record(bytes(bad))
        self.assertEqual(e.exception.code, 9)
        chgpack.parse(bytes(bad))                                                # (the game still installs)
        self.assertEqual(chgpack.read_picture(bytes(bad)), chgpack.read_picture(chg))
        with self.assertRaises(ValueError):
            chgpack.pack(image(8), "P", record=bytes(chgpack.RECORD_MAX + 1))

    def test_round_trip(self):
        """A card prepared from a cart backs up to that cart (less its own title) and prepares the same card again, from any form of card."""
        from chcart import backup
        c = self.full_cart()
        files = runtime.prepare(c)
        b, issues = backup.backup(files, title="FULL")
        self.assertEqual(issues, [])
        self.assertEqual(runtime.prepare(b), files)
        self.assertEqual(b.launch, "inner")
        self.assertEqual(b.colors, {"mark": "#FF8100", "text": "#FFFFFF"})        # (as RGB565 gives them back)
        self.assertEqual(sorted(b.system_images), ["error-4", "installed"])
        self.assertEqual((sorted(b.folder_backgrounds), sorted(b.folder_covers)), (["TOYS"], ["TOYS/BOX"]))
        for want in c.games:
            got = b.game(want.id)
            self.assertEqual((got.title, got.folder, got.binaries, got.sd, got.license_files, got.cart_image,
                              got.buttons, got.author, got.version, got.description, got.genre, got.license, got.url),
                             (want.title, want.folder, want.binaries, want.sd, want.license_files, want.cart_image,
                              want.buttons, want.author, want.version, want.description, want.genre, want.license,
                              want.url))
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            runtime.write_folder(files, d / "card")
            runtime.write_image(files, d / "card.img")
            (d / "card.zip").write_bytes(backup.card_zip(files))
            for where in (d / "card", d / "card.img", d / "card.zip"):
                with self.subTest(where.name):
                    self.assertEqual(runtime.prepare(backup.backup(where)[0]), files)

    def test_hand_changes(self):
        from chcart import backup
        c = Cart("C", [game("a", "ALPHA", sd={"A.DAT": b"a", "B.DAT": b"b"}), game("z", "ZULU", folder="F")])
        files = runtime.prepare(c)
        files["A.DAT"] = b"changed"
        del files["B.DAT"]
        files["GAMES/OWN.CHG"] = chgpack.pack(image(40), "OWN", "me")
        files["MINE.DAT"] = b"mine"
        b, issues = backup.backup(files, sd={"GAMES/OWN.CHG": ["mine.dat"]})
        self.assertEqual(sorted(i.code for i in issues), ["no-record", "sd-changed", "sd-missing"])
        self.assertEqual(b.game("a").sd, {"A.DAT": b"changed"})
        self.assertEqual((b.game("own").sd, b.game("own").author), ({"MINE.DAT": b"mine"}, "me"))
        # some games only: no menu, no launch, and only their warnings
        one, issues = backup.backup(files, games=["zulu"])
        self.assertEqual(([g.id for g in one.games], one.games[0].folder, issues), (["z"], "F", []))
        self.assertEqual(backup.backup(files, games=["GAMES/ALPHA.CHG"])[0].games[0].id, "a")
        for kw in ({"games": ["nobody"]}, {"sd": {"GAMES/OWN.CHG": ["NONE.DAT"]}}, {"sd": {"GAMES/NO.CHG": ["A.DAT"]}}):
            with self.subTest(kw), self.assertRaises(CartError):
                backup.backup(files, **kw)

    def test_chg_import(self):
        """A .chg with a record gives its game as the cart had it."""
        g = self.full_cart().games[0]
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "WORDS.CHG"
            f.write_bytes(runtime.chg_file(g))
            got = sources.from_binary(f)
            self.assertEqual((got.id, got.author, got.binaries, got.license_files, got.cart_image, got.sd),
                             (g.id, g.author, g.binaries, g.license_files, g.cart_image, {}))
            f.write_bytes(chgpack.pack(g.binaries["rev0"], "WORDS", "me"))
            self.assertEqual(sources.from_binary(f).author, "me")                 # without one: the header

    def test_command(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            runtime.write_folder(runtime.prepare(self.full_cart()), d / "card")
            out = d / "b.chgame"
            self.assertEqual(cli.main(["backup", str(d / "card"), str(out), "--title", "MINE"]), 0)
            c = zipio.load(out)
            self.assertEqual((c.title, len(c.games), c.launch), ("MINE", 4, "inner"))
            self.assertEqual(cli.main(["backup", str(d / "card"), str(out), "--game", "nobody"]), 1)


class Boards(unittest.TestCase):
    """Which board a binary is for (spec/chgame.md, "Devices and revisions")."""
    CGR1 = 0x31524743

    def test_tables_agree(self):
        self.assertEqual({d.chg_target: (d.id, d.chg_layout, d.max_image) for d in model.DEVICES.values()},
                         chgpack.BOARDS)
        self.assertEqual({t: n for n, t in model.RESERVED_DEVICES.items()}, chgpack.RESERVED)
        self.assertEqual(chgpack.TARGET_REV1, self.CGR1)
        self.assertEqual(chgpack.fourcc(chgpack.TARGET_REV0), "CX35")
        self.assertEqual(chgpack.fourcc(chgpack.TARGET_REV1), "CGR1")
        spec = (TOOLS.parent / "spec" / "chgame.md").read_text(encoding="utf-8")
        for name, target in [(d.id, d.chg_target) for d in model.DEVICES.values()] + list(model.RESERVED_DEVICES.items()):
            self.assertIn(f"`{name}`", spec, "every device and reserved name is in the spec's table")
            self.assertIn(f"`{chgpack.fourcc(target)}`", spec)

    def test_unknown_and_reserved_devices(self):
        """A binary for a board this reader does not know, or a reserved one,
        is a warning: not used, kept, and the rest of the cart works."""
        for dev, says in (("rev1", "reserved"), ("rev7", "does not know")):
            c = Cart("C", [Game("a", "A", {"rev0": image(100), dev: image(100, 2)})])
            issues = model.validate(c)
            self.assertEqual(codes(issues), [])
            warned = [i for i in issues if i.code == "unknown-device"]
            self.assertTrue(warned and says in warned[0].message and not warned[0].error, warned)
            back = zipio.load(zipio.to_bytes(c))
            self.assertEqual(back.game("a").binaries[dev], image(100, 2), "kept when the cart is rewritten")
            self.assertEqual(runtime.prepare(back), runtime.prepare(Cart("C", [Game("a", "A", {"rev0": image(100)})])))
        bad = Cart("C", [Game("a", "A", {"REV0": image(100)})])
        self.assertEqual(codes(model.validate(bad)), ["bad-device"])
        with self.assertRaises(ValueError):
            chgpack.pack(image(100), "A", target=self.CGR1)
        with self.assertRaises(ValueError):
            chgpack.target_of("rev1")
        # a package that names rev1, as a rev1 tool would write it
        chg = bytearray(chgpack.pack(image(100), "A"))
        struct.pack_into("<I", chg, 8, self.CGR1)
        struct.pack_into("<I", chg, 0x1FC, __import__("zlib").crc32(bytes(chg[:0x1FC])))
        with self.assertRaises(chgpack.ChgError) as e:
            chgpack.parse(bytes(chg))
        self.assertEqual(e.exception.code, 4)
        self.assertIn("rev1 (CGR1)", str(e.exception))

    def test_a_second_board(self):
        """With a second board defined (as rev1 will be), a cart carries a
        binary for each, a card is prepared for one, its CHG files name it,
        and a backup files each game under the board its CHG names."""
        from unittest import mock
        from chcart import backup
        rev1 = model.Device("rev1", "CHGame Rev1", "CH32X035G8U6", 0x3000, 50944, 50432, self.CGR1, 0x003000F7,
                            "CHGame:ch32v:rev1")
        with mock.patch.dict(model.DEVICES, {"rev1": rev1}), \
                mock.patch.dict(chgpack.BOARDS, {self.CGR1: ("rev1", 0x003000F7, 50944)}):
            g = Game("a", "A", {"rev0": image(100, 1), "rev1": image(120, 2)})
            c = Cart("C", [g, Game("b", "B", {"rev0": image(90, 3)})])
            self.assertEqual(codes(model.validate(c)), [])
            back = zipio.load(zipio.to_bytes(c))
            self.assertEqual(set(back.game("a").binaries), {"rev0", "rev1"})
            with self.assertRaises(CartError) as e:
                runtime.prepare(c, "rev1")                  # b has no rev1 binary
            self.assertEqual(e.exception.code, "bad-device")
            one = Cart("C", [g])
            files0, files1 = runtime.prepare(one, "rev0"), runtime.prepare(one, "rev1")
            chg0, chg1 = files0["GAMES/A.CHG"], files1["GAMES/A.CHG"]
            self.assertEqual(chgpack.parse(chg0)["device"], "rev0")
            self.assertEqual(struct.unpack_from("<I", chg1, 8)[0], self.CGR1)
            self.assertEqual(chgpack.parse(chg1)["device"], "rev1")
            with self.assertRaises(chgpack.ChgError):        # a rev0 bootloader refuses it
                chgpack.parse(chg1, target=chgpack.TARGET_REV0)
            game1, _, _ = backup.game_from_chg(chg1)
            self.assertEqual(game1.binaries, {"rev1": image(120, 2)})
            refused, _, why = backup.game_from_chg(chg1, "rev0")
            self.assertIsNone(refused)
            self.assertEqual([i.code for i in why], ["bad-chg"])
            b, _ = backup.backup(files1)
            self.assertEqual(b.game("a").binaries, {"rev1": image(120, 2)})


class Fixtures(unittest.TestCase):
    def test_expected(self):
        from chcart import fixtures
        self.assertEqual(fixtures.check(log=lambda s: None), [])

    def test_schema_agrees(self):
        """spec/info.schema.json accepts every good fixture's manifest and
        refuses the bad ones whose fault is the manifest's shape."""
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed")
        from chcart import fixtures
        schema = json.loads((fixtures.FIX.parent / "info.schema.json").read_text(encoding="utf-8"))
        v = jsonschema.Draft202012Validator(schema)
        for f in sorted((fixtures.FIX / "good").glob("*.chgame")):
            with self.subTest(f.name):
                self.assertEqual([e.message for e in v.iter_errors(zipio.read(f)[1])], [])
        for code in ("schema-version", "missing-field", "bad-field", "bad-id", "bad-title", "bad-folder", "bad-device"):
            with self.subTest(code):
                self.assertTrue(list(v.iter_errors(zipio.read(fixtures.FIX / "bad" / f"{code}.chgame")[1])))


class Commands(unittest.TestCase):
    def test_edit_and_prepare(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            for n in ("ALPHA", "BRAVO", "CHARLIE"):
                (d / f"{n}.bin").write_bytes(image(500, len(n)))
            pkg = str(d / "c.chgame")
            run = lambda *a: self.assertEqual(cli.main([str(x) for x in a]), 0)
            run("new", pkg, d / "ALPHA.bin", d / "BRAVO.bin", "--title", "MINE")
            run("add", pkg, d / "CHARLIE.bin", "--folder", "MORE", "--at", 0)
            self.assertEqual([g.id for g in zipio.load(pkg).games], ["charlie", "alpha", "bravo"])
            run("order", pkg, "alpha", "MORE/")                       # a folder: its games
            self.assertEqual([g.id for g in zipio.load(pkg).games], ["alpha", "charlie", "bravo"])
            self.assertEqual(cli.main(["order", pkg, "NOPE/"]), 1)
            run("order", pkg, "bravo")
            run("set", pkg, "--game", "alpha", "title=ALPHA ONE", "folder=MORE")
            run("set", pkg, "author=me")
            run("launch", pkg, "alpha")
            run("remove", pkg, "charlie")
            c = zipio.load(pkg)
            self.assertEqual([(g.id, g.title, g.folder) for g in c.games],
                             [("bravo", "BRAVO", ""), ("alpha", "ALPHA ONE", "MORE")])
            self.assertEqual((c.title, c.author, c.launch), ("MINE", "me", "alpha"))
            run("verify", pkg)
            run("prepare", pkg, d / "card", "--image", d / "card.img")
            self.assertTrue((d / "card" / "GAMES" / "MORE" / "ALPHAONE.CHG").exists())
            self.assertTrue((d / "card.img").stat().st_size > 0)
            self.assertEqual(cli.main(["launch", pkg, "nobody"]), 1)


if __name__ == "__main__":
    unittest.main()
