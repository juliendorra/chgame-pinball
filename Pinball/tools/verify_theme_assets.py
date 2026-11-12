#!/usr/bin/env python3
"""Compare the SD theme loader with embedded art on the real renderer."""
from contextlib import contextmanager
import os
from pathlib import Path
import struct
import sys
from tempfile import TemporaryDirectory

GAME = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(GAME.parent / "CHGame/tools/chsim"), str(GAME / "editor")]
from boards import image
from chdrivelib import Driver, SimTransport
from protocol import LiveClient
from sim_build import build

PACK = "PINBALL/THEMES.PBA"


@contextmanager
def console(exe, card=None):
    if card:
        os.environ["CHSD_CARD"] = str(card)
    else:
        os.environ.pop("CHSD_CARD", None)
    transport = SimTransport(exe)
    try:
        driver = Driver(transport, "MPIN")
        driver.handshake()
        driver.frames(1)
        yield driver, LiveClient(transport)
    finally:
        assert transport.close() == 0, transport.bugs


def tap(driver, key):
    driver.buttons(key)
    driver.frames(1)
    driver.buttons(0)
    driver.frames(1)


def play(driver, live, board):
    live.upload(board)
    driver.frames(1)
    driver.cmd("O 123456")
    driver.cmd("M -24")
    driver.cmd("W 256")
    roof = driver.shot()
    driver.cmd("M 128")
    driver.cmd("W 256")
    return roof, driver.shot()


def capture(exe, card, boards):
    with console(exe, card) as (driver, live):
        menu = [driver.shot()]
        for _ in boards:
            tap(driver, 32)  # Right
            menu.append(driver.shot())
        return menu, [play(driver, live, board) for board in boards.values()]


def verify_sd_library(exe, card, neon, pack):
    with console(exe, card) as (driver, live):
        assert live.boards() == [], "an absent card should leave the console picker empty"
        tap(driver, 1)  # A cannot start without a board.
        assert live.state()["id"] == 0
        try:
            live.request("R")
        except RuntimeError:
            pass
        else:
            raise AssertionError("USB restart must refuse an empty board")
        image(card, {"PINBALL/NEON.PBT": neon, PACK: pack}, fs="fat16", spc=1)
        tap(driver, 128)  # SELECT rescans after inserting the card.
        assert live.boards() == [{"index": 0, "file": "NEON"}]
        assert live.board(0) == neon
        tap(driver, 1)
        assert live.board() == neon and live.state()["lives"] == 3

    files = {f"PINBALL/B{i:03}.PBT": neon for i in range(97)}
    image(card, files, fs="fat16", spc=1)
    with console(exe, card) as (_, live):
        entries = live.boards()
        assert len(entries) == 96 and entries[0]["file"] == "B000"
        assert live.board() == live.board(0) == neon
        assert live.board(95) == neon


def main():
    out = GAME / "out/verify"
    out.mkdir(parents=True, exist_ok=True)
    embedded = build(GAME, out=out / "themes-embedded")
    loader = build(GAME, defines=("PINBALL_SD_THEMES=1",), out=out / "themes-sd")
    sd_only = build(GAME, defines=("PINBALL_SD_THEMES=1", "PINBALL_SD_BOARDS=1"), out=out / "boards-sd")
    boards = {f"PINBALL/{p.name}": p.read_bytes() for p in sorted((GAME / "sd/PINBALL").glob("*.PBT"))}
    pack = (GAME / "sd" / PACK).read_bytes()
    with TemporaryDirectory(dir=out) as tmp:
        verify_sd_library(sd_only, Path(tmp) / "boards.img", boards["PINBALL/NEON.PBT"], pack)
        card = Path(tmp) / "themes.img"
        image(card, boards, fs="fat16", spc=1)
        reference = capture(embedded, card, boards)
        fallback = capture(loader, card, boards)
        assert fallback != reference, "without the pack the loader should use Neon art"
        with console(embedded) as (driver, _):
            neon = driver.shot()
        with console(loader) as (driver, _):
            assert driver.shot() == neon, "built-in menu still works with no card"
        for fs in ("fat16", "fat32"):
            image(card, {**boards, PACK: pack}, fs=fs, spc=1, fragment={PACK: 8})
            assert capture(loader, card, boards) == reference, f"{fs}: themed menu and game pixels differ"

        # CARNIVAL uses theme 6. A corrupt sector must leave the other seven
        # themes usable. Test the integrity check and independently the sprite
        # bounds check by giving the malformed sprite a correct checksum.
        sector = 5 * 512
        invalid = bytearray(pack)
        invalid[sector + 7] = 255  # impossible run count in the first side row
        for rehash in (False, True):
            if rehash:
                checksum = 2166136261
                for byte in invalid[sector:sector + 508]:
                    checksum = ((checksum ^ byte) * 16777619) & 0xFFFFFFFF
                struct.pack_into("<I", invalid, sector + 508, checksum)
            image(card, {**boards, PACK: invalid}, fs="fat16", spc=1)
            menu, game = capture(loader, card, boards)
            assert menu[1] == fallback[0][1] and menu[2:] == reference[0][2:]
            assert game[0] == fallback[1][0] and game[1:] == reference[1][1:]
        image(card, {**boards, PACK: pack[:-512]}, fs="fat16", spc=1)
        assert capture(loader, card, boards) == fallback, "truncated pack should use the fallback"

        image(card, {**boards, PACK: pack}, fs="fat16", spc=1)
        with console(loader, card) as (driver, live):
            board = boards["PINBALL/PIRATES.PBT"]
            roof, _ = play(driver, live, board)
            driver.cmd("E 1")
            driver.cmd("M -24")
            driver.cmd("W 256")
            assert driver.shot() == roof, "play should keep using cached art after card removal"
            driver.cmd("D")
            driver.cmd("W 256")
            assert driver.shot() != roof, "rescan should discard cached art"
            driver.cmd("E 0")
            driver.cmd("D")
            driver.cmd("W 256")
            assert driver.shot() == roof, "rescan should reload art after reinsertion"
    print("PASS: all nine themes match pixel-for-pixel, fragmented FAT16/FAT32, fallback and rescan")
    print("PASS: console SD-only library starts empty, rescans, plays Neon, and accepts 96 SD entries")


if __name__ == "__main__":
    main()
