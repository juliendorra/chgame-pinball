"""The new-user test: install a built release into an empty Arduino setup and
use it the way someone who only has the board package would.

    python tools/release/acceptance.py [--dist out/stage] [--all] [--card out/stage/CHGame-sdcard-<v>.zip]

It serves --dist on localhost (serve.py), points a fresh arduino-cli at it
(its own data folder, sketchbook and config under out/newuser/; your own
Arduino setup is not touched), and checks:

  - Boards Manager installs CHGame from the one URL, with its three tools;
  - CHGame, CHGfx and CHSd come with it (platform libraries, nothing to add);
  - File > Examples has CHGame's Hello, the twenty games, CHStlView and CHSDtoUSB;
  - Tools > Bootloader offers the three bootloaders, and their files are there;
  - Tools > Programmer offers CHGame USB and the WCH factory ISP;
  - examples copied to the sketchbook (what the IDE does when one is saved)
    compile with plain `arduino-cli compile`, no --library, and Export
    Compiled Binary leaves a .bin and a .chg for the SD menu beside them.

--all compiles every game and app from the installed package (release
options, or a sketch's own FQBN in its tools/game.py), and --card then makes
the casino cart from them (tools/sdcard/casino.json) beside the zip, as
CHGame-Casino-<version>.chgame, and packs its card's contents (chcart's
runtime preparation) as the zip: the cart and the card that go with the
release, built from exactly what it delivers.

Nothing here touches a board. The bootloader and upload paths are for a
person with a board in hand (platform/board/docs/building.md).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "sdcard"))
from _common import OUT, fail, say  # noqa: E402
import serve  # noqa: E402
import chgpack  # noqa: E402
import device  # noqa: E402
import gamecfg  # noqa: E402
import mkcard  # noqa: E402
from chcart import runtime, zipio  # noqa: E402

FQBN = "CHGame:ch32v:rev0"
RELEASE_FQBN = device.FQBN_RELEASE
NEWUSER = OUT / "newuser"
DOWNLOADS = OUT / "arduino-downloads"     # kept between runs: the toolchain is ~100 MB; our archives are deleted
DEFAULT_JOBS = max(1, min(4, (os.cpu_count() or 2) // 2))
# What the sketchbook test compiles, and what it expects: None is a build, a
# string is a compile error containing it. The smallest sketch and a large game
# with the IDE's default options (Smallest + LTO), a game with the release
# options, and an SD game, which needs USB > Upload only and says so.
SKETCHES = [("Hello", FQBN, None), ("Games/CHChess", FQBN, None), ("Games/CHFour", RELEASE_FQBN, None),
            ("Games/CHWords", FQBN, "needs Tools > USB > Upload only"), ("Games/CHWords", RELEASE_FQBN, None)]


class Cli:
    def __init__(self, root: Path, index_url: str):
        self.root = root
        self.config = root / "arduino-cli.yaml"
        self.data, self.user = root / "arduino15", root / "sketchbook"
        root.mkdir(parents=True, exist_ok=True)
        self.config.write_text(
            "board_manager:\n  additional_urls:\n    - " + index_url + "\n"
            "directories:\n"
            f"  data: {self.data.as_posix()}\n  user: {self.user.as_posix()}\n  downloads: {DOWNLOADS.as_posix()}\n"
            "network:\n  connection_timeout: 600s\n",
            encoding="utf-8", newline="\n")

    def __call__(self, *args, check=True, json_out=False):
        cmd = ["arduino-cli", "--config-file", str(self.config), *args] + (["--json"] if json_out else [])
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if check and r.returncode:
            fail(f"FAILED: arduino-cli {' '.join(args)}\n{r.stdout[-4000:]}{r.stderr[-4000:]}")
        return json.loads(r.stdout) if json_out and r.returncode == 0 else r


class Checks:
    def __init__(self):
        self.rows = []

    def __call__(self, ok: bool, what: str, detail: str = ""):
        self.rows.append((ok, what, detail))
        say(f"  {'ok  ' if ok else 'FAIL'} {what}" + (f": {detail}" if detail else ""))
        return ok

    @property
    def failed(self):
        return [r for r in self.rows if not r[0]]


def compile_sketch(cli: Cli, sketch: Path, fqbn: str, build: Path, export: bool = False, flags: str = ""):
    args = ["compile", "-b", fqbn, "--build-path", str(build), "--warnings", "none"]
    if flags:
        args += ["--build-property", "build.extra_flags=" + flags]
    if export:
        args.append("--export-binaries")
    r = cli(*args, str(sketch), check=False)
    return r.returncode == 0, (r.stdout + r.stderr)


def run(dist: Path, port: int, build_all: bool, card: Path | None, jobs: int) -> int:
    check = Checks()
    server, index_url = serve.start(dist, port)
    expected = json.loads((dist / serve.INDEX).read_text(encoding="utf-8"))["packages"][0]["platforms"][0]["version"]
    say(f"=== a new user installs CHGame {expected} from {index_url} ===")
    if NEWUSER.exists():
        shutil.rmtree(NEWUSER)
    pkgdir = DOWNLOADS / "packages"
    if pkgdir.is_dir():                  # our archives change between builds of the same version
        for f in list(pkgdir.glob("CHGame-ch32v-*")) + list(pkgdir.glob("chgame-upload-*")):
            f.unlink()
    cli = Cli(NEWUSER, index_url)
    try:
        cli("core", "update-index")
        r = cli("core", "install", "CHGame:ch32v")
        say("  " + "\n  ".join(ln for ln in (r.stdout + r.stderr).splitlines()
                                if ln.strip() and not ("%" in ln and " / " in ln)))     # not the progress bars
    finally:
        server.shutdown()                # everything after this works offline, as an installed package must

    plat = cli.data / "packages" / "CHGame" / "hardware" / "ch32v" / expected
    check(plat.is_dir(), "the platform is installed", str(plat.relative_to(OUT)))
    tools = cli.data / "packages" / "CHGame" / "tools"
    for t in ("riscv-none-embed-gcc", "wchisp", "chgame-upload"):
        check(any((tools / t).glob("*")), f"tool {t}", ", ".join(p.name for p in (tools / t).glob("*")))

    say("=== libraries ===")
    libs = cli("lib", "list", "--all", "-b", FQBN, json_out=True).get("installed_libraries", [])
    found = {l["library"]["name"]: l["library"] for l in libs}
    for name in ("CHGame", "CHGfx", "CHSd"):
        lib = found.get(name)
        check(bool(lib) and lib.get("location") == "platform", f"library {name}",
              f"{lib.get('version')}, {lib.get('location')}" if lib else "missing")
    user_libs = list((cli.user / "libraries").glob("*")) if (cli.user / "libraries").is_dir() else []
    check(not user_libs, "nothing installed in the sketchbook's libraries")

    say("=== File > Examples ===")
    ex = cli("lib", "examples", "CHGame", "-b", FQBN, json_out=True).get("examples", [])
    paths = [Path(p) for e in ex for p in e.get("examples", [])]
    rel = sorted(p.relative_to(plat / "libraries" / "CHGame" / "examples").as_posix() for p in paths
                 if (plat / "libraries" / "CHGame" / "examples") in p.parents)
    games = [r for r in rel if r.startswith("Games/")]
    apps = [r for r in rel if r.startswith("Apps/")]
    check("Hello" in rel, "CHGame > Hello")
    check(len(games) == 20, "CHGame > Games", f"{len(games)}: " + " ".join(g.split("/")[1] for g in games))
    check({"Apps/CHSDtoUSB", "Apps/CHSDtoSerial", "Apps/CHStlView"} <= set(apps), "CHGame > Apps", " ".join(apps))
    gfx = cli("lib", "examples", "CHGfx", "-b", FQBN, json_out=True).get("examples", [])
    check(sum(len(e.get("examples", [])) for e in gfx) > 0, "CHGfx's examples",
          str(sum(len(e.get("examples", [])) for e in gfx)))

    say("=== Tools menus ===")
    det = cli("board", "details", "-b", FQBN, json_out=True)
    opts = {o["option"]: [v["value"] for v in o["values"]] for o in det.get("config_options", [])}
    check(opts.get("boot", []) == ["sdmenu", "sdstatic", "sdvisual", "sdvisualstatic", "nomenu"], "Tools > Bootloader",
          ", ".join(opts.get("boot", [])))
    progs = {p["id"]: p["name"] for p in det.get("programmers", [])}
    check({"chgameusb", "wchisp"} <= set(progs), "Tools > Programmer", "; ".join(progs.values()))
    boards_txt = (plat / "boards.txt").read_text(encoding="utf-8", errors="replace")
    for ln in boards_txt.splitlines():
        if ".bootloader.file=" in ln and not ln.lstrip().startswith("#"):
            f = plat / "bootloaders" / ln.split("=", 1)[1].strip()
            check(f.is_file(), f"bootloader {ln.split('.menu.boot.')[-1].split('.')[0]}",
                  f"{f.name}, {f.stat().st_size:,} B" if f.is_file() else f"{f} missing")
    ptxt = (plat / "platform.txt").read_text(encoding="utf-8")
    check(f"version={expected}" in ptxt, "platform.txt's version", expected)

    say("=== sketches saved to the sketchbook, compiled with no --library ===")
    examples = plat / "libraries" / "CHGame" / "examples"
    for rel_sketch, fqbn, error in SKETCHES:
        src = examples / rel_sketch
        dst = cli.user / src.name
        if not dst.exists():
            shutil.copytree(src, dst)
        options = "release options" if fqbn != FQBN else "the IDE's default options"
        ok, log = compile_sketch(cli, dst, fqbn, NEWUSER / "build" / f"{src.name}-{'default' if fqbn == FQBN else 'release'}", export=True)
        if error:
            check(not ok and error in log, f"{src.name} with {options} stops with a message", error)
            continue
        if not check(ok, f"{src.name} compiles with {options}"):
            say(log[-3000:])
            continue
        exported = list((dst / "build").rglob(f"{src.name}.ino.*"))
        names = sorted(p.suffix for p in exported)
        chg = next((p for p in exported if p.suffix == ".chg"), None)
        info = ""
        if chg:
            try:
                i = chgpack.parse(chg.read_bytes())
                info = f"{i['title']}, {i['payload_bytes']:,} B"
            except chgpack.ChgError as e:
                chg, info = None, str(e)
        check(".bin" in names and chg is not None, f"{src.name}: Export Compiled Binary gives .bin and .chg",
              info or " ".join(names))

    if build_all:
        say(f"=== every game and app, from the installed package ({jobs} at a time) ===")
        progs_ = mkcard.programs()

        def build_one(name):
            d = mkcard.folder(name, plat)
            out = NEWUSER / "build" / "all" / d.name
            ok, log = compile_sketch(cli, d, gamecfg.load(d).FQBN or RELEASE_FQBN, out, flags=device.defines(d))
            return name, d, out / f"{d.name}.ino.bin", ok, log

        results = [build_one(progs_[0])]          # one first: it fills the core cache the rest share
        with cf.ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
            results += list(pool.map(build_one, progs_[1:]))
        bins = {}
        for p, d, binf, ok, log in results:
            size = binf.stat().st_size if ok and binf.is_file() else 0
            if not check(ok and size > 0, f"{d.name}", f"{size:,} B (room under 50,432: {50432 - size:,})" if size else "failed"):
                say(log[-2000:])
            bins[d.name] = binf
        if card and not check.failed:
            say("=== the casino cart and its SD card ===")
            cart = mkcard.make_cart(binary=lambda d: bins[d.name], platform_dir=plat, version=expected)
            cart_file = card.with_name(f"CHGame-Casino-{expected}.chgame")
            card.parent.mkdir(parents=True, exist_ok=True)
            data = zipio.write(cart, cart_file)
            check(not [i for i in zipio.check(cart_file) if i.error], "the cart",
                  f"{cart_file.name}, {len(cart.games)} games, {len(data):,} B")
            files = runtime.prepare(cart)
            with zipfile.ZipFile(card, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("README.txt", CARD_README.format(version=expected))
                for name in sorted(files):
                    zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    z.writestr(zi, files[name])
            check(True, "SD card contents", f"{card.name}, {len(files)} files, {card.stat().st_size:,} B")

    say("")
    if check.failed:
        say(f"{len(check.failed)} of {len(check.rows)} checks FAILED")
        return 1
    say(f"all {len(check.rows)} checks passed: a new user gets everything from the one URL.")
    return 0


CARD_README = """CHGame {version}: the SD card for the game menu
==========================================

Copy everything in this zip (the GAMES folder and the files beside it) to the
root of a FAT32 (or FAT16) microSD card. Put the card in the CHGame and
switch it on: the game menu lists every game. A starts one; holding START
for 3 seconds in a game goes back to the menu.

The menu is part of the CHGame bootloader. A board that does not show it
needs the menu bootloader once: in the Arduino IDE, choose Tools > Board >
CHGame Boards > CHGame Rev0, Tools > Bootloader > SD Text Menu (Rainbow or Static),
Tools > Programmer > CHGame USB,
then Tools > Burn Bootloader.

The same games come as one file, CHGame-Casino-{version}.chgame, beside this
zip: the format games are shared in (the repository's spec/chgame.md).
`chgame cart deploy CHGame-Casino-{version}.chgame --card E:\\` writes this
card from it.

Your own sketches: Sketch > Export Compiled Binary leaves a .chg file in the
sketch's build folder. Copy it into GAMES (a short name, like MYGAME.CHG).
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dist", type=Path, default=OUT / "stage")
    ap.add_argument("--port", type=int, default=serve.DEFAULT_PORT)
    ap.add_argument("--all", action="store_true", help="also compile every game and app from the installed package")
    ap.add_argument("--card", type=Path, help="with --all: write the SD card's contents to this zip")
    ap.add_argument("--jobs", type=int, default=DEFAULT_JOBS)
    a = ap.parse_args(argv)
    if a.card and not a.all:
        ap.error("--card needs --all")
    if not shutil.which("arduino-cli"):
        fail("arduino-cli is not on the PATH")
    return run(a.dist, a.port, a.all, a.card, a.jobs)


if __name__ == "__main__":
    sys.exit(main())
