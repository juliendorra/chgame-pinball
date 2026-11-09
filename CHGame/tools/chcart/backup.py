"""Backing a card up: the games on a CHGame's SD card back into a cart
(spec/card.md, "Backing up a card"), from the card alone.

Each CHG file that runtime preparation wrote carries the game's record
(spec/chg.md): its cart entry, its cart image and licence files as the cart
held them, the length of its binary and the SD files it put on the card with
their sizes and CRCs. So a game comes back with its SD files, and a card
prepared from a cart comes back as that cart: preparing the backup gives the
same card, byte for byte. A CHG file without a record (Export Compiled
Binary's, or one from before records) comes back from its header and
picture, and its SD files are the ones named by hand (`sd`).

    chgame cart backup E:\\ out.chgame                  the whole card: games, folders, menu
    chgame cart backup card.img words.chgame --game chwords
    chgame cart backup E:\\ mine.chgame --game GAMES/MINE.CHG --sd GAMES/MINE.CHG=MINE.DAT

A card is a mounted folder or drive, a FAT image, or a ZIP of the card's
files (what an "SD card zip" holds), or {path: bytes}.
"""
from __future__ import annotations

import base64
import binascii
import io
import json
import os
import pathlib
import re
import stat
import struct
import zipfile
import zlib

from . import model, runtime
from .model import Cart, Game, Issue

chgpack = runtime.chgpack
CRC_RE = re.compile(r"^[0-9a-f]{8}$")


# ---- cards ---------------------------------------------------------------------------

class FilesCard:
    """A card as {path: bytes} (paths with '/', any case)."""

    def __init__(self, files):
        self.files = {p.upper(): d for p, d in files.items()}

    def list(self, folder):
        pre = folder.upper().rstrip("/") + "/"
        out = set()
        for p in self.files:
            if p.startswith(pre):
                head, sep, _ = p[len(pre):].partition("/")
                out.add((head, bool(sep)))
        return sorted(out)

    def read(self, path):
        return self.files.get(path.upper())


class FolderCard:
    """A mounted card, or any folder laid out as one."""

    HIDDEN = getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 2) | getattr(stat, "FILE_ATTRIBUTE_SYSTEM", 4)

    def __init__(self, root):
        self.root = pathlib.Path(root)

    def list(self, folder):
        d = self.root / folder
        if not d.is_dir():
            return []
        out = []
        for e in os.scandir(d):
            if getattr(e.stat(follow_symlinks=False), "st_file_attributes", 0) & self.HIDDEN:
                continue
            out.append((e.name.upper(), e.is_dir()))
        return sorted(out)

    def read(self, path):
        f = self.root / path
        return f.read_bytes() if f.is_file() else None


class ImageCard:
    """A FAT16/FAT32 card image (CHSd's tools/fatimg.py reads it)."""

    def __init__(self, path):
        import sys
        sys.path.insert(0, str(runtime.REPO / "platform" / "board" / "arduino" / "CHGame" / "libraries" / "CHSd" / "tools"))
        import fatimg  # noqa: E402
        self.fat = fatimg
        self.vol = fatimg.FatVolume(str(path))

    def list(self, folder):
        try:
            cluster = self.vol.find(folder, is_dir=True)[0]
        except self.fat.FatError:
            return []
        out = []
        for raw, attr, _, _ in self.vol.listdir(cluster):
            if attr & (self.fat.ATTR_HIDDEN | self.fat.ATTR_SYS) or raw[0] in b"._":
                continue
            base, ext = raw[:8].decode("ascii", "replace").rstrip(), raw[8:].decode("ascii", "replace").rstrip()
            out.append((base + ("." + ext if ext else ""), bool(attr & self.fat.ATTR_DIR)))
        return sorted(out)

    def read(self, path):
        try:
            return self.vol.read_file(path)
        except self.fat.FatError:
            return None


def open_card(where):
    """A card from a folder or drive, a FAT image, a ZIP of its files, or {path: bytes}."""
    if isinstance(where, dict):
        return FilesCard(where)
    p = pathlib.Path(where)
    if p.is_dir():
        return FolderCard(p)
    if zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            return FilesCard({i.filename: z.read(i) for i in z.infolist() if not i.filename.endswith("/")})
    return ImageCard(p)


def card_zip(files):
    """A card's files as a ZIP (sorted, dated 1980-01-01, deflated): the form
    the backup fixtures keep cards in."""
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(files):
            z.writestr(zipfile.ZipInfo(p, (1980, 1, 1, 0, 0, 0)), files[p], zipfile.ZIP_DEFLATED, 9)
    return b.getvalue()


# ---- the record ----------------------------------------------------------------------

def parse_record(data):
    """The record's dict (spec/chg.md), checked, or None if it is not one this
    reader can trust (then the file is backed up as one without a record)."""
    try:
        r = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(r, dict) or r.get("chgRecord") != runtime.RECORD_VERSION:
        return None
    g = r.get("game")
    if not isinstance(g, dict) or not all(isinstance(g.get(k), str) for k in ("id", "title")):
        return None
    if not model.ID_RE.match(g["id"]) or not g["title"].strip() or not model.printable(g["title"])             or len(g["title"]) > model.TITLE_MAX:
        return None
    if any(not isinstance(g[k], str) for k in runtime.RECORD_TEXT if k in g):
        return None
    if not isinstance(g.get("buttons", []), list) or any(
            not isinstance(b, dict) or not isinstance(b.get("control"), str) or not isinstance(b.get("action"), str)
            for b in g.get("buttons", [])):
        return None
    n = r.get("binaryBytes")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        return None
    try:
        if "cartImage" in r:
            r["cartImage"] = base64.b64decode(r["cartImage"], validate=True)
        lic = r.get("licenseFiles", {})
        if not isinstance(lic, dict) or not all(isinstance(k, str) and model.FILE_NAME_RE.match(k) for k in lic):
            return None
        r["licenseFiles"] = {k: base64.b64decode(v, validate=True) for k, v in lic.items()}
    except (TypeError, ValueError, binascii.Error):
        return None
    sd = r.get("sdcard", [])
    if not isinstance(sd, list):
        return None
    for f in sd:
        if (not isinstance(f, dict) or not isinstance(f.get("path"), str) or not model.sd_path_ok(f["path"])
                or not isinstance(f.get("bytes"), int) or not isinstance(f.get("crc32"), str)
                or not CRC_RE.match(f["crc32"])):
            return None
    r["sdcard"] = sd
    return r


def game_from_chg(data, device=None, where="CHG"):
    """(Game, the record's SD files [{path, bytes, crc32}] or None, [Issue]) from
    a CHG file; Game is None if the file fails the bootloader's checks. The
    game's binary is filed under the board the file names (its target id);
    given `device`, a file for another board is left out."""
    issues = []
    try:
        info = chgpack.parse(data, target=None if device is None else model.DEVICES[device].chg_target)
    except chgpack.ChgError as e:
        return None, None, [Issue("bad-chg", where, f"{e}: left out", False)]
    device = info["device"]
    payload = data[chgpack.HEADER_BYTES:chgpack.HEADER_BYTES + info["payload_bytes"]]
    try:
        raw = chgpack.read_record(data)
    except chgpack.ChgError as e:
        raw = None
        issues.append(Issue("bad-record", where, f"{e}: backed up from its header", False))
    r = parse_record(raw) if raw else None
    if raw and r is None:
        issues.append(Issue("bad-record", where, "a record this reader cannot use: backed up from its header", False))
    if r:
        n = r["binaryBytes"]
        if n > len(payload) or len(chgpack.pad_image(payload[:n])) != len(payload) or payload[n:] != b"\xff" * (len(payload) - n):
            issues.append(Issue("bad-record", where, f"binaryBytes {n} does not fit the payload: backed up from its header", False))
            r = None
    if r:
        g = r["game"]
        game = Game(id=g["id"], title=g["title"], binaries={device: payload[:r["binaryBytes"]]},
                    buttons=[(b["control"], b["action"]) for b in g.get("buttons", [])],
                    license_files=r["licenseFiles"], cart_image=r.get("cartImage"),
                    **{k: g[k] for k in runtime.RECORD_TEXT if k in g})
        return game, r["sdcard"], issues
    issues.append(Issue("no-record", where, "no record: its SD files are not known (name them by hand)", False))
    try:
        pic = chgpack.read_picture(data)
    except chgpack.ChgError:
        pic = None
    title = info["title"] or "GAME"
    game = Game(id=model.slug(title), title=title, binaries={device: payload}, author=info["author"],
                version=info["version"], cart_image=runtime.picture_png(pic) if pic else None)
    return game, None, issues


# ---- reading the card ----------------------------------------------------------------

def _fold(title):
    """A title as the menu sorts it: capitals, '?' for what its font lacks, 19 columns."""
    t = "".join(c.upper() if "a" <= c <= "z" else (c if " " <= c <= "_" else "?") for c in title)
    return t[:model.TITLE_SHOWN].ljust(model.TITLE_SHOWN)


def _raw11(name):
    base, _, ext = name.partition(".")
    return base.ljust(8)[:8] + ext.ljust(3)[:3]


def _index(data):
    """{raw 8.3 name: (record number, launch flag, folder title)} from a MENU.IDX."""
    out = {}
    if not data or data[:4] != runtime.IDX_MAGIC:
        return out
    for k in range(1, len(data) // runtime.IDX_RECORD):
        e = data[k * runtime.IDX_RECORD:(k + 1) * runtime.IDX_RECORD]
        name = e[:11].decode("ascii", "replace")
        if name not in out:
            out[name] = (k, bool(e[11] & runtime.IDX_LAUNCH), e[12:].split(b"\0", 1)[0].decode("ascii", "replace"))
    return out


def _folder_name_ok(s):
    return 1 <= len(s) <= model.FOLDER_MAX and model.printable(s) and "/" not in s and s == s.strip()


def _picture(data):
    return data if data and len(data) == runtime.BG_BYTES and data[:4] == runtime.BG_MAGIC else None


def _same(png, data, ui=None):
    """Whether a PNG prepares into these bytes (a default left as it was)."""
    return (runtime.menu_background(png, ui) if ui else runtime.menu_picture(png)) == data


def read_card(card, device=None):
    """Every game on the card, in the menu's order, with what the menu shows of
    it: ([{"path", "folder", "launch", "game", "sd", "issues"}], [Issue]).
    Each game's binary is filed under the board its CHG file names; given
    `device`, only that board's games are read."""
    issues, out = [], []

    def level(folder, cart_folder, launch_ok, depth):
        names = card.list(folder)
        idx = _index(card.read(f"{folder}/MENU.IDX"))
        entries = []
        for name, is_dir in names:
            if name.startswith((".", "_")):
                continue
            if not is_dir and not name.endswith(".CHG"):
                continue
            raw = _raw11(name if not is_dir else name.partition(".")[0])
            k, flag, title = idx.get(raw, (None, False, ""))
            path = f"{folder}/{name}"
            if is_dir:
                label = title if _folder_name_ok(title) else name
                entries.append(((k is None, k or 0, _fold(name.ljust(11)), raw), "dir", path, label, flag))
            else:
                data = card.read(path) or b""
                game, sd, why = game_from_chg(data, device, path)
                sort = _fold(game.title if game else name)
                entries.append(((k is None, k or 0, sort, raw), "game", path, (game, sd, why), flag))
        for _, kind, path, e, flag in sorted(entries, key=lambda x: x[0]):
            if kind == "dir":
                if depth == model.FOLDER_DEPTH:
                    issues.append(Issue("bad-folder", path, f"deeper than {model.FOLDER_DEPTH} folders: left out", False))
                    continue
                level(path, f"{cart_folder}/{e}" if cart_folder else e, launch_ok and flag, depth + 1)
            else:
                game, sd, why = e
                issues.extend(why)
                if game:
                    game.folder = cart_folder
                    out.append({"path": path, "folder": cart_folder, "launch": launch_ok and flag,
                                "game": game, "sd": sd})

    level("GAMES", "", True, 0)
    return out, issues


def read_menu(card, cart, folders):
    """The cart's menu from the card's MENU.BG, COVER.PIC and SYSTEM.PIC, the
    defaults left out (so a cart without them prepares the same card again)."""
    bg = _picture(card.read("GAMES/MENU.BG"))
    if bg:
        pal = struct.unpack_from("<16H", bg, 8)
        for k, i in runtime.UI_INDEX.items():
            if pal[i] != runtime.rgb565(*model.hex_rgb(model.UI_COLORS[k])):
                cart.colors[k] = "#%02X%02X%02X" % runtime.rgb888(pal[i])
    ui = cart.ui_colors()
    if bg and not _same(runtime.DEFAULT_BACKGROUND.read_bytes(), bg, ui):
        cart.background = runtime.picture_png(bg, ui)
    cover = _picture(card.read("GAMES/COVER.PIC"))
    if cover and not _same(runtime.DEFAULT_COVER.read_bytes(), cover):
        cart.cover = runtime.picture_png(cover)
    sysp = card.read("GAMES/SYSTEM.PIC") or b""
    slots = [_picture(sysp[k * runtime.BG_BYTES:(k + 1) * runtime.BG_BYTES]) for k in range(1 + len(runtime.SYSTEM_SCREENS))]
    if slots[0] and not _same(runtime.DEFAULT_ABOUT.read_bytes(), slots[0]):
        cart.about = runtime.picture_png(slots[0])
    for n, pic in zip(runtime.SYSTEM_SCREENS, slots[1:]):
        if pic and not _same((runtime.SYSTEM_DIR / f"{n}.png").read_bytes(), pic):
            cart.system_images[n] = runtime.picture_png(pic)
    for name, path in folders.items():
        bg = _picture(card.read(f"{path}/MENU.BG"))
        if bg:
            cart.folder_backgrounds[name] = runtime.picture_png(bg, ui)
        cover = _picture(card.read(f"{path}/COVER.PIC"))
        if cover:
            cart.folder_covers[name] = runtime.picture_png(cover)


def backup(where, games=None, title="CARD BACKUP", sd=None, device=None):
    """(Cart, [Issue]): the games on the card as a cart (spec/card.md, "Backing
    up a card"). `games`: the ones to keep (card paths, ids or titles; None for
    all, with the card's menu and launch game). `sd`: {card path of a CHG: [SD
    paths]} for games without a record. Raises CartError when nothing is left
    or the result breaks a rule of the format."""
    card = open_card(where)
    found, issues = read_card(card, device)
    if games is not None:
        want = [str(w) for w in games]
        keep = [f for f in found if any(w.upper() in (f["path"].upper(), f["game"].id.upper(), f["game"].title.upper())
                                        for w in want)]
        for w in want:
            if not any(w.upper() in (f["path"].upper(), f["game"].id.upper(), f["game"].title.upper()) for f in keep):
                raise model.CartError([Issue("missing-file", w, "no game on the card by that path, id or title")])
        found = keep
        issues = [i for i in issues if any(i.where.startswith(f["path"]) for f in keep)]
    sd = {k.upper(): v for k, v in (sd or {}).items()}
    cart = Cart(title=title)
    used = set()
    folders = {}
    for f in found:
        g = f["game"]
        gid, n = g.id, 2
        while gid in used:
            s = f"-{n}"
            gid, n = g.id[:32 - len(s)].rstrip("-") + s, n + 1
        if gid != g.id:
            issues.append(Issue("renamed-id", f["path"], f"{g.id!r} is taken: {gid!r}", False))
            g.id = gid
        used.add(gid)
        for p in (f["sd"] or []):
            data = card.read(p["path"])
            if data is None:
                issues.append(Issue("sd-missing", f"{f['path']}: {p['path']}", "not on the card: left out", False))
                continue
            if len(data) != p["bytes"] or f"{zlib.crc32(data) & 0xFFFFFFFF:08x}" != p["crc32"]:
                issues.append(Issue("sd-changed", f"{f['path']}: {p['path']}",
                                    "not the file the game came with: backed up as the card has it", False))
            g.sd[p["path"]] = data
        for p in sd.pop(f["path"].upper(), []):
            p = p.replace("\\", "/").strip("/").upper()
            data = card.read(p)
            if data is None or not model.sd_path_ok(p):
                raise model.CartError([Issue("missing-file", p, "not a file on the card (8.3 names, outside GAMES/)")])
            g.sd[p] = data
        cart.games.append(g)
        if games is None:
            if f["launch"] and not cart.launch:
                cart.launch = g.id
            parts = f["folder"].split("/") if f["folder"] else []
            dirs = f["path"].split("/")[:-1]
            for k in range(1, len(parts) + 1):
                folders.setdefault("/".join(parts[:k]), "/".join(dirs[:k + 1]))
    if sd:
        raise model.CartError([Issue("missing-file", p, "no game on the card by that path") for p in sd])
    if not cart.games:
        raise model.CartError([Issue("missing-field", "games", "no game on the card")])
    if games is None:
        read_menu(card, cart, folders)
    errors = [i for i in model.validate(cart) if i.error]
    if errors:
        raise model.CartError(errors)
    return cart, issues
