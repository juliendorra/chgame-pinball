#!/usr/bin/env python3
"""The repository's cart and its SD card.

    chgame card                          build every program; write the cart and the card
    chgame card --no-build               use the release builds already there
    chgame card --image out/sdcard.img   also a FAT32 card image
    chgame card --only CHFour CHChess    just these programs

The programs, their order and their genre folders are tools/sdcard/casino.json,
a cart recipe (`chgame cart build`, tools/chcart/cli.py); each sketch's
chgame.json gives its title, details, SD files and picture. The cart is
written to out/CHGame-Casino.chgame, and the card made from it
(tools/chcart/runtime.py, spec/card.md: GAMES/ with the CHG files, MENU.IDX,
MENU.BG, COVER.PIC and SYSTEM.PIC, and the data files the games read) to
out/sdcard/. Copy the CONTENTS of out/sdcard/ to the
root of a FAT16/FAT32 card (for example through the CHGame's SD CARD READER,
in the menu's APPS folder), or `chgame cart deploy out/CHGame-Casino.chgame
--card E:\\`.

The same inputs give the same bytes, so a card can be rebuilt and compared.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import chgpack  # noqa: E402
from chcart import cli, runtime, zipio  # noqa: E402

RECIPE = pathlib.Path(__file__).with_name("casino.json")
PLATFORM = REPO / "platform" / "board" / "arduino" / "CHGame"
CART = REPO / "out" / "CHGame-Casino.chgame"


def programs(only=None) -> list[str]:
    """The recipe's sketch names, in menu order."""
    names = cli.recipe_sketches(RECIPE)
    return [n for n in names if n in only] if only else names


def folder(name: str, platform_dir: pathlib.Path = PLATFORM) -> pathlib.Path:
    """A program's sketch folder: in this repository, or in an installed board
    package (tools/release/acceptance.py builds the release's card from that)."""
    return cli._in_platform(name, platform_dir)


def make_cart(only=None, binary=None, platform_dir: pathlib.Path = PLATFORM, version: str = ""):
    """The casino cart. binary(sketch folder) gives each release .bin; None
    builds them (tools/device.py)."""
    cart = cli.build_recipe(RECIPE, build=binary is None, binary=binary, only=only,
                            platform_dir=None if platform_dir == PLATFORM else platform_dir)
    cart.version = version or cart.version
    return cart


def make_card(cart, out: pathlib.Path, image: str | None = None) -> dict:
    """The cart's card into out/ (replacing it), a table of what is on it, and
    a FAT32 image if asked. Returns {card path: bytes}."""
    files = runtime.prepare(cart)
    runtime.write_folder(files, out)
    print(f"{'game':16s} {'file':24s} {'image':>7s}  crc32     title")
    for g, path in zip_games(cart, files):
        i = chgpack.parse(files[path])
        print(f"{g.id:16s} {path:24s} {i['payload_bytes']:7d}  {i['payload_crc32']:08x}  {g.title}")
    print(f"\n{len(cart.games)} games, {len(files)} files in {out}")
    if image:
        runtime.write_image(files, image)
        print(f"card image: {image}")
    return files


def zip_games(cart, files):
    """(game, its CHG file's card path), matched by the CHG's payload."""
    by_payload = {}
    for p, data in files.items():
        if p.endswith(".CHG"):
            by_payload.setdefault(data[512:512 + chgpack.parse(data)["payload_bytes"]], p)   # (a picture may follow)
    return [(g, by_payload[chgpack.pad_image(g.binaries["rev0"])]) for g in cart.games]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(REPO / "out" / "sdcard"))
    ap.add_argument("--cart", default=str(CART), help="where the .chgame goes")
    ap.add_argument("--image", help="also write a FAT32 card image here")
    ap.add_argument("--no-build", action="store_true", help="use the existing build/release/*.ino.bin")
    ap.add_argument("--only", nargs="*", help="sketch names to include (default: all)")
    a = ap.parse_args(argv)
    binary = (lambda d: d / "build" / "release" / f"{d.name}.ino.bin") if a.no_build else None
    cart = make_cart(a.only, binary)
    pathlib.Path(a.cart).parent.mkdir(parents=True, exist_ok=True)
    data = zipio.write(cart, a.cart)
    print(f"{a.cart}: {len(cart.games)} games, {len(data)} B")
    make_card(cart, pathlib.Path(a.out), a.image)
    return 0


if __name__ == "__main__":
    sys.exit(main())
