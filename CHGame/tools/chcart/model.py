"""The .chgame format, version 1 (spec/chgame.md): the model, info.json in and
out, and validation.

A Cart holds everything by value (images, binaries, SD files as bytes), so it
does not depend on where a file sat inside the ZIP it came from. Reading
accepts any layout the manifest names; writing (to_manifest) always lays the
files out the same way:

    info.json
    menu/background.png, menu/folder-<k>.png
    <id>/<device>.bin
    <id>/<LICENSE, NOTICE, ...>
    <id>/cart.png
    <id>/sdcard/<card path>

Problems are Issues with a stable code (spec/chgame.md lists them all); the
error ones make a cart unusable, the warnings do not.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Device:
    id: str
    board: str
    mcu: str
    load_address: int
    max_image: int          # bytes, after padding to a multiple of 4
    save_safe: int          # images up to this keep both save pages
    chg_target: int
    chg_layout: int
    fqbn: str


# The boards a binary can be for: spec/chgame.md's device table, "Devices and
# revisions" (its naming rule, and docs/hardware-revisions.md for adding one).
# chg_target is the board's id in CHG files, HELLO and the bootloader image:
# rev0's, "CX35", is named after its MCU and stays so; later boards' are
# "CGR<n>". chgpack.BOARDS lists the same boards (the tests check).
DEVICES = {
    "rev0": Device("rev0", "CHGame Rev0", "CH32X035G8U6", 0x3000, 50944, 50432,
                   0x35335843, 0x003000F7, "CHGame:ch32v:rev0"),
}
# Names and ids assigned to boards not defined yet: a binary for one is not
# used (warning unknown-device, as for any board this reader does not know)
# until it joins DEVICES.
RESERVED_DEVICES = {"rev1": 0x31524743}        # "CGR1"
# What any device name looks like, known or not; one that breaks it is bad-device.
DEVICE_RE = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
BOOT_SIG, BOOT_SIG_OFFSET = 0x4C424843, 8      # "CHBL": a bootloader image, not a program

TITLE_MAX, TITLE_SHOWN, FOLDER_MAX, FOLDER_DEPTH = 31, 19, 19, 4
FOLDER_ENTRIES = 240                           # rows a folder of the menu holds (menu.h MENU_MAX_GAMES)
CHG_AUTHOR_MAX, CHG_VERSION_MAX = 15, 7
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
SD_CHARS = "A-Z0-9!#$%&'()\\-@^_`{}~"
SD_NAME_RE = re.compile(rf"^[{SD_CHARS}]{{1,8}}(\.[{SD_CHARS}]{{1,3}})?$")
FILE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ][0-9:.+\-Z]+)?$")
RESERVED_SD = "GAMES"                          # the menu's own folder on the card
UI_COLORS = {"text": "#FFF4D6", "disabled": "#808080", "selectedText": "#000000", "mark": "#D62020"}
RAINBOW_RGB = (255, 0, 255)

CART_KEYS = ("schemaVersion", "title", "version", "author", "description", "date", "license", "url",
             "sourceUrl", "launch", "menu", "games")
MENU_KEYS = ("background", "colors", "folders", "cover", "about", "systemImages")
# The visual menu's own screens a cart may replace (menu.systemImages; the
# card's SYSTEM.PIC slots 1-8 in this order, after the about page: card.md step 7)
SYSTEM_IMAGES = ("installed", "game", "folder", "error-1", "error-2", "error-3", "error-4", "error-5")
EXTENSION_PREFIX = "x-"                        # top-level keys of other tools: kept, never warned about
WEB_EXTENSION = "x-chgame-web"                 # the web tool's; its version 1 systemImages are read as menu's
GAME_KEYS = ("id", "title", "folder", "version", "author", "description", "genre", "license",
             "licenseFiles", "url", "sourceUrl", "buttons", "binaries", "sdcard", "cartImage")
TEXT_FIELDS = ("version", "author", "description", "license", "url", "sourceUrl")


@dataclass
class Issue:
    code: str
    where: str
    message: str
    error: bool = True

    def __str__(self):
        return f"{'error' if self.error else 'warning'} {self.code}: {self.where}: {self.message}"


class CartError(Exception):
    def __init__(self, issues):
        self.issues = [i for i in issues if i.error]
        super().__init__("\n".join(str(i) for i in self.issues))

    @property
    def code(self):
        return self.issues[0].code if self.issues else ""


@dataclass
class Game:
    id: str
    title: str
    binaries: dict = field(default_factory=dict)        # device id -> image bytes (.bin)
    folder: str = ""                                    # "" (top level) or "A" or "A/B"
    version: str = ""
    author: str = ""
    description: str = ""
    genre: str = ""
    license: str = ""
    url: str = ""
    sourceUrl: str = ""
    license_files: dict = field(default_factory=dict)   # file name -> bytes
    buttons: list = field(default_factory=list)         # [(control, action)]
    sd: dict = field(default_factory=dict)              # card path -> bytes
    cart_image: bytes | None = None

    def binary(self, device="rev0"):
        return self.binaries.get(device)


@dataclass
class Cart:
    title: str
    games: list = field(default_factory=list)
    version: str = ""
    author: str = ""
    description: str = ""
    date: str = ""
    license: str = ""
    url: str = ""
    sourceUrl: str = ""
    launch: str = ""                                    # a game id, or ""
    background: bytes | None = None                     # PNG for the top of the menu
    colors: dict = field(default_factory=dict)          # UI_COLORS keys -> "#RRGGBB"
    folder_backgrounds: dict = field(default_factory=dict)   # folder path -> PNG
    cover: bytes | None = None                          # PNG: the cart's cover, the visual menu's splash
    about: bytes | None = None                          # PNG: the visual menu's about page
    folder_covers: dict = field(default_factory=dict)   # folder path -> PNG: the folder's cover
    system_images: dict = field(default_factory=dict)   # SYSTEM_IMAGES key -> PNG: the menu's own screens
    extensions: dict = field(default_factory=dict)      # "x-..." top-level keys, as read (JSON values)

    def game(self, gid):
        for g in self.games:
            if g.id == gid:
                return g
        return None

    def folders(self):
        """Every folder path, parents before children, in menu order (the
        order of first appearance in games)."""
        seen = []
        for g in self.games:
            parts = g.folder.split("/") if g.folder else []
            for k in range(1, len(parts) + 1):
                p = "/".join(parts[:k])
                if p not in seen:
                    seen.append(p)
        return seen

    def ui_colors(self):
        return {k: self.colors.get(k, v).upper() for k, v in UI_COLORS.items()}


# ---- images ---------------------------------------------------------------------

def image_info(data):
    """(format, width, height, frames, has transparency) of a PNG or GIF, or None."""
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception:
        return None
    alpha = im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info)
    if alpha and im.mode in ("RGBA", "LA"):
        alpha = im.getchannel("A").getextrema()[0] < 255
    return im.format, im.size[0], im.size[1], getattr(im, "n_frames", 1), alpha


def rgb_pixels(data):
    """A 128x128 opaque PNG's pixels as (r, g, b) tuples, row by row."""
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    return list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())


def background_colors(data, ui):
    """The colours of a menu background other than the rainbow and the UI's
    own, in order of first appearance (spec/card.md: indices 0-10)."""
    special = {RAINBOW_RGB} | {hex_rgb(c) for c in ui.values()}
    out = []
    for p in rgb_pixels(data):
        if p not in special and p not in out:
            out.append(p)
    return out


def hex_rgb(c):
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


# ---- text rules -------------------------------------------------------------------

def printable(s):
    return all(32 <= ord(ch) < 127 for ch in s)


def menu_shows(s):
    """Every character is one the menu's font has (a-z are shown as capitals)."""
    return all(32 <= ord(ch) <= 0x5F or "a" <= ch <= "z" for ch in s)


def chg_text(s, n):
    """What goes in a CHG header's author or version field: the text if it is
    printable ASCII, cut to n characters; otherwise nothing."""
    return s[:n] if printable(s) else ""


def slug(s, fallback="game"):
    """An id from a title or file name: lower case, a-z 0-9 and single hyphens."""
    t = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:32].strip("-")
    return t or fallback


def sd_path_ok(p):
    parts = p.split("/")
    return all(SD_NAME_RE.match(x) for x in parts) and parts[0].upper() != RESERVED_SD


# ---- validation -------------------------------------------------------------------

def validate(cart):
    """Every rule of spec/chgame.md that is about content, not the manifest's
    shape: [Issue]."""
    out = []

    def err(code, where, msg):
        out.append(Issue(code, where, msg))

    def warn(code, where, msg):
        out.append(Issue(code, where, msg, False))

    if not isinstance(cart.title, str) or not cart.title.strip():
        err("missing-field", "title", "the cart needs a title")
    for k in TEXT_FIELDS:
        if not isinstance(getattr(cart, k), str):
            err("bad-field", k, "must be text")
    if cart.date and not DATE_RE.match(cart.date):
        err("bad-field", "date", f"{cart.date!r} is not an ISO 8601 date")
    if not cart.games:
        err("missing-field", "games", "a cart holds at least one game")
    ids = set()
    for i, g in enumerate(cart.games):
        out += validate_game(g, f"games[{i}]")
        if g.id in ids:
            err("duplicate-id", f"games[{i}].id", f"{g.id!r} is used twice")
        ids.add(g.id)
    if cart.launch and cart.launch not in ids:
        err("bad-launch", "launch", f"no game has the id {cart.launch!r}")
    for k, v in cart.colors.items():
        if k not in UI_COLORS:
            warn("unknown-key", f"menu.colors.{k}", "not a colour the menu uses")
        elif not isinstance(v, str) or not COLOR_RE.match(v):
            err("bad-field", f"menu.colors.{k}", f"{v!r} is not #RRGGBB")
    ui = cart.ui_colors() if all(isinstance(v, str) and COLOR_RE.match(v) for v in cart.colors.values()) else UI_COLORS
    folders = cart.folders()
    if cart.background is not None:
        out += _check_background(cart.background, ui, "menu.background")
    for name, png in cart.folder_backgrounds.items():
        if name not in folders:
            warn("unused-file", f"menu.folders[{name!r}]", "no game is in this folder")
        out += _check_background(png, ui, f"menu.folders[{name!r}].background")
    for k in ("cover", "about"):
        if getattr(cart, k) is not None:
            out += check_picture(getattr(cart, k), f"menu.{k}")
    for k, png in cart.system_images.items():
        if k not in SYSTEM_IMAGES:
            warn("unknown-key", f"menu.systemImages.{k}", f"not a screen of the menu (they are {', '.join(SYSTEM_IMAGES)})")
        else:
            out += check_picture(png, f"menu.systemImages.{k}")
    for name, png in cart.folder_covers.items():
        if name not in folders and name not in cart.folder_backgrounds:
            warn("unused-file", f"menu.folders[{name!r}]", "no game is in this folder")
        out += check_picture(png, f"menu.folders[{name!r}].cover")
    # a folder of the menu lists FOLDER_ENTRIES entries, games and folders
    count = {}
    for g in cart.games:
        count[g.folder] = count.get(g.folder, 0) + 1
    for f in folders:
        parent = f.rsplit("/", 1)[0] if "/" in f else ""
        count[parent] = count.get(parent, 0) + 1
    for f, n in count.items():
        if n > FOLDER_ENTRIES:
            err("full-folder", f"folder {f!r}" if f else "top level",
                f"{n} entries; a folder of the menu lists {FOLDER_ENTRIES}: put some in folders")
    # the card holds one file per path
    owner = {}
    for g in cart.games:
        for p, data in g.sd.items():
            if p in owner and owner[p][1] != data:
                err("sd-conflict", f"games[{g.id}].sdcard", f"{p} differs from {owner[p][0]}'s")
            owner.setdefault(p, (g.id, data))
    return out


def validate_game(g, where):
    out = []

    def err(code, w, msg):
        out.append(Issue(code, f"{where}.{w}", msg))

    def warn(code, w, msg):
        out.append(Issue(code, f"{where}.{w}", msg, False))

    if not isinstance(g.id, str) or not ID_RE.match(g.id):
        err("bad-id", "id", f"{g.id!r}: a-z, 0-9 and '-', 1 to 32 characters, not starting with '-'")
    t = g.title
    if not isinstance(t, str) or not t.strip() or not printable(t) or len(t) > TITLE_MAX:
        err("bad-title", "title", f"{t!r}: printable ASCII, 1 to {TITLE_MAX} characters")
    else:
        if len(t) > TITLE_SHOWN:
            warn("long-title", "title", f"the menu shows the first {TITLE_SHOWN} characters: {t[:TITLE_SHOWN]!r}")
        if not menu_shows(t):
            warn("title-chars", "title", "the menu shows characters after '_' (except a-z) as '?'")
    for k in TEXT_FIELDS + ("genre",):
        if not isinstance(getattr(g, k), str):
            err("bad-field", k, "must be text")
    if g.folder:
        parts = g.folder.split("/")
        if len(parts) > FOLDER_DEPTH:
            err("bad-folder", "folder", f"folders nest {FOLDER_DEPTH} deep at most")
        for p in parts:
            if not p.strip() or p != p.strip() or not printable(p) or len(p) > FOLDER_MAX:
                err("bad-folder", "folder", f"{p!r}: printable ASCII, 1 to {FOLDER_MAX} characters, "
                                            "no spaces at either end, '/' between folders")
    if not g.binaries:
        err("missing-field", "binaries", "a game needs a binary")
    for dev, img in g.binaries.items():
        if not isinstance(dev, str) or not DEVICE_RE.match(dev):
            err("bad-device", f"binaries[{dev}]", f"{dev!r} is not a device name (spec/chgame.md: rev0, rev1 ...)")
            continue
        d = DEVICES.get(dev)
        if d is None:
            # A board added after this reader, or one not defined yet: its
            # binary is kept but not used, and the rest of the cart still is.
            warn("unknown-device", f"binaries[{dev}]",
                 f"{dev} is reserved for a board that is not defined yet: its binary is not used"
                 if dev in RESERVED_DEVICES else
                 f"a device this reader does not know (known: {', '.join(DEVICES)}): its binary is not used")
            continue
        n = len(img) + (-len(img) % 4)
        if not img or n > d.max_image:
            err("binary-size", f"binaries[{dev}]", f"{len(img)} B; {dev} takes 4 to {d.max_image} B")
        elif len(img) >= BOOT_SIG_OFFSET + 4 and int.from_bytes(img[BOOT_SIG_OFFSET:BOOT_SIG_OFFSET + 4], "little") == BOOT_SIG:
            err("bootloader-image", f"binaries[{dev}]", "a bootloader image, not a program")
        elif n > d.save_safe:
            warn("save-pages", f"binaries[{dev}]", f"{n} B covers a save page: saving switches itself off "
                                                   f"above {d.save_safe} B")
    for name in g.license_files:
        if not FILE_NAME_RE.match(name):
            err("bad-field", "licenseFiles", f"{name!r} is not a plain file name")
    for p in g.sd:
        if not sd_path_ok(p):
            err("bad-sd-path", "sdcard", f"{p}: every part an 8.3 name in capitals, not under {RESERVED_SD}/")
    if g.cart_image is not None:
        i = image_info(g.cart_image)
        if not i or i[0] != "PNG" or i[1:3] != (128, 128) or i[3] != 1:
            err("bad-image", "cartImage", "a 128x128 PNG")
        else:                               # (an older cart may break the picture rule: then no picture on the card)
            for issue in check_picture(g.cart_image, "cartImage"):
                warn("bad-picture", "cartImage", f"{issue.message}: the card gets no picture of it")
    for k, b in enumerate(g.buttons):
        if not (isinstance(b, (tuple, list)) and len(b) == 2 and all(isinstance(x, str) and x for x in b)):
            err("bad-field", f"buttons[{k}]", "control and action, both text")
    return out


def check_picture(png, where):
    """The picture rule (spec/card.md): what _check_background() asks, with
    the menu's colours at their defaults, whatever the cart's."""
    return [Issue("bad-picture" if i.code == "bad-background" else i.code, i.where, i.message)
            for i in _check_background(png, UI_COLORS, where)]


def picture_ok(png):
    return png is not None and not check_picture(png, "")


def _check_background(png, ui, where):
    i = image_info(png)
    if not i or i[0] != "PNG" or i[1:3] != (128, 128) or i[3] != 1:
        return [Issue("bad-image", where, "a 128x128 PNG")]
    if i[4]:
        return [Issue("bad-image", where, "must be opaque: no transparent pixels")]
    n = len(background_colors(png, ui))
    if n > 11:
        return [Issue("bad-background", where, f"{n} colours besides #FF00FF and the menu's own; 11 at most")]
    return []


# ---- info.json --------------------------------------------------------------------

def to_manifest(cart):
    """(manifest dict, {zip path: bytes}) in the canonical layout."""
    files = {}
    m = {"schemaVersion": SCHEMA_VERSION, "title": cart.title}
    for k in ("version", "author", "description", "date", "license", "url", "sourceUrl", "launch"):
        if getattr(cart, k):
            m[k] = getattr(cart, k)
    menu = {}
    if cart.background is not None:
        files["menu/background.png"] = cart.background
        menu["background"] = "menu/background.png"
    if cart.colors:
        menu["colors"] = {k: cart.colors[k] for k in UI_COLORS if k in cart.colors}
    for k in ("cover", "about"):
        if getattr(cart, k) is not None:
            files[f"menu/{k}.png"] = getattr(cart, k)
            menu[k] = f"menu/{k}.png"
    if cart.system_images:
        menu["systemImages"] = {}
        for k in SYSTEM_IMAGES:
            if k in cart.system_images:
                files[f"menu/system-{k}.png"] = cart.system_images[k]
                menu["systemImages"][k] = f"menu/system-{k}.png"
    if cart.folder_backgrounds or cart.folder_covers:
        menu["folders"] = []
        order = cart.folders()
        names = sorted(set(cart.folder_backgrounds) | set(cart.folder_covers),
                       key=lambda n: (order.index(n) if n in order else len(order), n))
        for k, name in enumerate(names, 1):
            f = {"name": name}
            if name in cart.folder_backgrounds:
                files[f"menu/folder-{k}.png"] = cart.folder_backgrounds[name]
                f["background"] = f"menu/folder-{k}.png"
            if name in cart.folder_covers:
                files[f"menu/folder-{k}-cover.png"] = cart.folder_covers[name]
                f["cover"] = f"menu/folder-{k}-cover.png"
            menu["folders"].append(f)
    if menu:
        m["menu"] = menu
    m["games"] = []
    for g in cart.games:
        e = {"id": g.id, "title": g.title}
        for k in ("folder", "version", "author", "description", "genre", "license"):
            if getattr(g, k):
                e[k] = getattr(g, k)
        if g.license_files:
            e["licenseFiles"] = []
            for name, data in g.license_files.items():
                files[f"{g.id}/{name}"] = data
                e["licenseFiles"].append(f"{g.id}/{name}")
        for k in ("url", "sourceUrl"):
            if getattr(g, k):
                e[k] = getattr(g, k)
        if g.buttons:
            e["buttons"] = [{"control": c, "action": a} for c, a in g.buttons]
        e["binaries"] = []
        for dev, img in g.binaries.items():
            files[f"{g.id}/{dev}.bin"] = img
            e["binaries"].append({"device": dev, "filename": f"{g.id}/{dev}.bin"})
        if g.sd:
            for p, data in g.sd.items():
                files[f"{g.id}/sdcard/{p}"] = data
            e["sdcard"] = f"{g.id}/sdcard/"
        if g.cart_image is not None:
            files[f"{g.id}/cart.png"] = g.cart_image
            e["cartImage"] = f"{g.id}/cart.png"
        m["games"].append(e)
    for k, v in cart.extensions.items():               # other tools' keys, as they were read
        if k.startswith(EXTENSION_PREFIX) and k not in m:
            m[k] = v
    return m, files


def from_manifest(m, files):
    """(Cart or None, [Issue]) from a parsed info.json and the ZIP's files.
    Shape problems are found here; content rules by validate(), which this
    runs too when the shape is sound."""
    issues = []
    used = {"info.json"}

    def err(code, where, msg):
        issues.append(Issue(code, where, msg))

    def warn(code, where, msg):
        issues.append(Issue(code, where, msg, False))

    def text(d, k, where, required=False):
        v = d.get(k, "")
        if k not in d and required:
            err("missing-field", where + k, "required")
        if not isinstance(v, str):
            err("bad-field", where + k, "must be text")
            return ""
        return v

    def blob(path, where):
        if not isinstance(path, str):
            err("bad-field", where, "must be a path in the file")
            return None
        if path not in files:
            err("missing-file", where, f"{path} is not in the file")
            return None
        used.add(path)
        return files[path]

    def unknown(d, keys, where):
        for k in d:
            if k not in keys and not k.startswith(EXTENSION_PREFIX):
                warn("unknown-key", where + k, "not part of schema version 1: ignored")

    if not isinstance(m, dict):
        return None, [Issue("bad-json", "info.json", "must be a JSON object")]
    v = m.get("schemaVersion")
    if not isinstance(v, int) or isinstance(v, bool) or v < 1:
        return None, [Issue("schema-version", "schemaVersion", "missing, or not a whole number >= 1")]
    if v > SCHEMA_VERSION:
        return None, [Issue("schema-version", "schemaVersion",
                            f"version {v}; this reader knows {SCHEMA_VERSION}: a newer tool is needed")]
    unknown(m, CART_KEYS, "")
    cart = Cart(title=text(m, "title", "", True))
    for k in ("version", "author", "description", "date", "license", "url", "sourceUrl", "launch"):
        setattr(cart, k, text(m, k, ""))
    menu = m.get("menu", {})
    if not isinstance(menu, dict):
        err("bad-field", "menu", "must be an object")
        menu = {}
    unknown(menu, MENU_KEYS, "menu.")
    if "background" in menu:
        cart.background = blob(menu["background"], "menu.background")
    for k in ("cover", "about"):
        if k in menu:
            setattr(cart, k, blob(menu[k], f"menu.{k}"))
    system = menu.get("systemImages", {})
    if not isinstance(system, dict):
        err("bad-field", "menu.systemImages", "must be an object: screen name -> path")
        system = {}
    for k, path in system.items():
        if k not in SYSTEM_IMAGES:
            warn("unknown-key", f"menu.systemImages.{k}", f"not a screen of the menu (they are {', '.join(SYSTEM_IMAGES)})")
            continue
        data = blob(path, f"menu.systemImages.{k}")
        if data is not None:
            cart.system_images[k] = data
    # Extensions: "x-" keys are other tools', kept as they are. The web
    # tool's version 1 names the same screens under x-chgame-web.systemImages:
    # read as menu.systemImages where that says nothing; the official field
    # wins where both speak, with a word when they differ.
    cart.extensions = {k: v for k, v in m.items() if k.startswith(EXTENSION_PREFIX)}
    ext = m.get(WEB_EXTENSION)
    if isinstance(ext, dict) and ext.get("version") == 1 and isinstance(ext.get("systemImages"), dict):
        for k, path in ext["systemImages"].items():
            w = f"{WEB_EXTENSION}.systemImages.{k}"
            if k not in SYSTEM_IMAGES:
                warn("unknown-key", w, f"not a screen of the menu (they are {', '.join(SYSTEM_IMAGES)})")
                continue
            data = blob(path, w)
            if data is None:
                continue
            if k in cart.system_images:
                if cart.system_images[k] != data:
                    warn("extension-conflict", w, f"differs from menu.systemImages.{k}, which is used")
            else:
                cart.system_images[k] = data
        kept = {k: v for k, v in ext.items() if k != "systemImages"}       # (moved to menu.systemImages)
        cart.extensions[WEB_EXTENSION] = kept
    colors = menu.get("colors", {})
    if isinstance(colors, dict):
        cart.colors = dict(colors)
    else:
        err("bad-field", "menu.colors", "must be an object")
    folders = menu.get("folders", [])
    if not isinstance(folders, list):
        err("bad-field", "menu.folders", "must be a list")
        folders = []
    for k, f in enumerate(folders):
        w = f"menu.folders[{k}]"
        if not isinstance(f, dict) or not isinstance(f.get("name"), str):
            err("bad-field", w, "needs a name")
            continue
        unknown(f, ("name", "background", "cover"), w + ".")
        if "background" in f:
            data = blob(f["background"], w + ".background")
            if data is not None:
                cart.folder_backgrounds[f["name"]] = data
        if "cover" in f:
            data = blob(f["cover"], w + ".cover")
            if data is not None:
                cart.folder_covers[f["name"]] = data
    games = m.get("games")
    if not isinstance(games, list):
        err("missing-field" if games is None else "bad-field", "games", "a list of games")
        games = []
    for i, e in enumerate(games):
        w = f"games[{i}]."
        if not isinstance(e, dict):
            err("bad-field", w[:-1], "must be an object")
            continue
        unknown(e, GAME_KEYS, w)
        g = Game(id=text(e, "id", w, True), title=text(e, "title", w, True))
        for k in ("folder", "version", "author", "description", "genre", "license", "url", "sourceUrl"):
            setattr(g, k, text(e, k, w))
        for k, path in enumerate(_list(e, "licenseFiles", w, err)):
            data = blob(path, f"{w}licenseFiles[{k}]")
            if data is not None:
                g.license_files[path.rsplit("/", 1)[-1]] = data
        for k, b in enumerate(_list(e, "buttons", w, err)):
            if isinstance(b, dict) and isinstance(b.get("control"), str) and isinstance(b.get("action"), str):
                g.buttons.append((b["control"], b["action"]))
            else:
                err("bad-field", f"{w}buttons[{k}]", "needs control and action")
        bins = _list(e, "binaries", w, err)
        if "binaries" not in e:
            err("missing-field", w + "binaries", "required")
        for k, b in enumerate(bins):
            if not isinstance(b, dict) or not isinstance(b.get("device"), str):
                err("bad-field", f"{w}binaries[{k}]", "needs device and filename")
                continue
            unknown(b, ("device", "filename"), f"{w}binaries[{k}].")
            if b["device"] in g.binaries:
                err("bad-device", f"{w}binaries[{k}]", f"a second binary for {b['device']}")
            data = blob(b.get("filename"), f"{w}binaries[{k}].filename")
            if data is not None:
                g.binaries[b["device"]] = data
        if "sdcard" in e:
            pre = e["sdcard"]
            if not isinstance(pre, str) or not pre.endswith("/"):
                err("bad-field", w + "sdcard", "a folder in the file, ending in '/'")
            else:
                for path in sorted(files):
                    if path.startswith(pre) and path != pre:
                        g.sd[path[len(pre):]] = files[path]
                        used.add(path)
                if not g.sd:
                    warn("unused-file", w + "sdcard", f"nothing in {pre}")
        if "cartImage" in e:
            g.cart_image = blob(e["cartImage"], w + "cartImage")
        cart.games.append(g)
    for path in sorted(files):
        if path not in used:
            warn("unused-file", path, "not named by info.json: ignored")
    if any(i.error for i in issues):
        return None, issues
    issues += validate(cart)
    return (None if any(i.error for i in issues) else cart), issues


def _list(d, k, where, err):
    v = d.get(k, [])
    if not isinstance(v, list):
        err("bad-field", where + k, "must be a list")
        return []
    return v
