"""Putting a cart on a CHGame: the deploy rules of spec/card.md.

    one game, no SD files    flash it (and, with a card, add its CHG file to
                             GAMES/ so the menu lists it)
    one game with SD files   its SD files and CHG file onto the card, then
                             flash it
    several games            the cart's whole GAMES/ tree and SD files onto
                             the card; flash the launch game if it names one

A single game joins whatever the card holds: GAMES/MENU.IDX and MENU.BG are
left alone, and a different game already using its file name keeps it (the
new one takes the next free name). A cart of several games brings its own
menu: its MENU.IDX and MENU.BG replace the card's, and --clean empties
GAMES/ first. The card is any mounted FAT16/FAT32 folder: a card reader, or
the CHGame itself after SD CARD READER in the menu (CHSDtoUSB).
"""
from __future__ import annotations

import os
import pathlib
import shutil
import tempfile

from . import model, runtime
from .model import CartError, Issue

NEED_CARD = ("needs the SD card mounted: pick SD CARD READER in the CHGame's menu (or put the card in a "
             "card reader) and pass --card with the drive (E:\\, /media/<you>/CHGAME ...)")


def flash(game, port=None, device="rev0", log=print):
    """Uploads the game's binary for `device` through the Python uploader and
    starts it; a board whose bootloader reports another board is refused."""
    import paths  # noqa: F401  (tools/paths.py: puts the uploader on sys.path)
    from chgame_upload.upload import flash_file
    with tempfile.TemporaryDirectory() as d:
        f = pathlib.Path(d) / f"{game.id}.bin"
        f.write_bytes(runtime.flash_image(game, device))
        log(f"flash   : {game.title} ({game.id})")
        return flash_file(f, port=port, run=True, log=log, device=device)


def _write(root, rel, data, log):
    f = root / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "wb") as h:
        h.write(data)
        h.flush()
        os.fsync(h.fileno())
    log(f"card    : {rel} ({len(data)} B)")


def _chg_title(data):
    import chgpack
    try:
        return chgpack.parse(data, check_payload=False)["title"]
    except chgpack.ChgError:
        return None


def add_game(game, card, device="rev0", log=print):
    """A single game's CHG file and SD files onto a mounted card, leaving the
    card's menu alone. Returns the CHG file's card path."""
    root = pathlib.Path(card)
    games = root / "GAMES"
    taken, same = set(), None
    if games.is_dir():
        for f in sorted(games.iterdir()):
            base, _, ext = f.name.upper().partition(".")
            if f.is_file() and ext == "CHG" and same is None and _chg_title(f.read_bytes()) == game.title:
                same = f.name                # the same game, older: replaced, under its own name
                continue
            taken.add((base, ext if f.is_file() else ""))
    path = f"GAMES/{same or runtime.name83(game.title, taken, 'CHG', 'GAME') + '.CHG'}"
    _write(root, path, runtime.chg_file(game, device), log)
    for p in sorted(game.sd):
        _write(root, p, game.sd[p], log)
    return path


def write_card(cart, card, clean=False, device="rev0", log=print):
    """A cart's whole runtime (runtime.prepare) onto a mounted card."""
    root = pathlib.Path(card)
    files = runtime.prepare(cart, device)
    if clean and (root / "GAMES").exists():
        log("card    : GAMES/ emptied (--clean)")
        shutil.rmtree(root / "GAMES")
    for p, data in files.items():
        _write(root, p, data, log)
    return files


def deploy(cart, card=None, port=None, clean=False, device="rev0", do_flash=True, log=print):
    """The deploy rules. Raises CartError when the cart needs a card and none
    is given."""
    errors = [i for i in model.validate(cart) if i.error]
    if errors:
        raise CartError(errors)
    if card is not None and not pathlib.Path(card).is_dir():
        raise CartError([Issue("missing-file", "--card", f"{card} is not a folder")])
    if len(cart.games) == 1:
        g = cart.games[0]
        if g.sd and card is None:
            raise CartError([Issue("missing-file", "--card", f"{g.id} has SD files: it {NEED_CARD}")])
        if card is not None:
            add_game(g, card, device, log)
        _sync()
        if do_flash:
            flash(g, port, device, log)
        return
    if card is None:
        raise CartError([Issue("missing-file", "--card", f"a cart of {len(cart.games)} games {NEED_CARD}")])
    write_card(cart, card, clean, device, log)
    _sync()
    if do_flash and cart.launch:
        flash(cart.game(cart.launch), port, device, log)
    log("done    : eject the card before the CHGame reads it (hold B, or START for 3 s, to leave the "
        "card reader)")


def _sync():
    if hasattr(os, "sync"):
        os.sync()
