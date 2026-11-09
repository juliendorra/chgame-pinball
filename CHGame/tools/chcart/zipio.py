""".chgame files on disk: a ZIP with info.json at its root (spec/chgame.md,
"The container").

read() refuses what a reader must refuse (encryption, methods other than
stored and deflate, unsafe or clashing paths, too much data) and returns the
manifest and the files; load() turns them into a Cart. write() makes the
same bytes from the same cart: info.json first, the rest sorted, every date
1980-01-01, deflate level 9, no OS-specific attributes.
"""
from __future__ import annotations

import io
import json
import zipfile

from . import model
from .model import CartError, Issue

MAX_FILES = 4096
MAX_BYTES = 512 << 20              # all files, uncompressed
EPOCH = (1980, 1, 1, 0, 0, 0)


def read(src):
    """({zip path: bytes}, manifest) of a .chgame (a path, bytes or a file),
    or CartError."""
    if isinstance(src, (bytes, bytearray)):
        src = io.BytesIO(src)
    try:
        z = zipfile.ZipFile(src)
    except (zipfile.BadZipFile, OSError) as e:
        raise CartError([Issue("not-a-zip", "file", str(e))])
    infos = [i for i in z.infolist() if not i.filename.endswith("/")]
    bad = lambda msg: CartError([Issue("bad-zip", "file", msg)])
    if len(infos) > MAX_FILES:
        raise bad(f"{len(infos)} files; {MAX_FILES} at most")
    if sum(i.file_size for i in infos) > MAX_BYTES:
        raise bad(f"more than {MAX_BYTES >> 20} MiB of files")
    seen = {}
    for i in infos:
        n = i.orig_filename                 # (on Windows, i.filename has '\' turned into '/')
        if i.flag_bits & 1:
            raise bad(f"{n}: encrypted")
        if i.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise bad(f"{n}: compression method {i.compress_type}; only stored (0) and deflate (8)")
        if not all(32 <= ord(c) < 127 for c in n) or "\\" in n or n.startswith("/") or \
                any(p in ("", ".", "..") for p in n.split("/")) or ":" in n:
            raise bad(f"{n!r}: paths are ASCII, relative, with '/' and no '.' or '..' parts")
        if n.lower() in seen:
            raise bad(f"{n} and {seen[n.lower()]}: the same path, or the same but for case")
        seen[n.lower()] = n
    files = {}
    try:
        for i in infos:
            files[i.filename] = z.read(i)
    except (zipfile.BadZipFile, OSError, RuntimeError) as e:
        raise bad(str(e))
    if "info.json" not in files:
        raise CartError([Issue("no-manifest", "info.json", "no info.json at the root")])
    try:
        manifest = json.loads(files["info.json"].decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        raise CartError([Issue("bad-json", "info.json", str(e))])
    return files, manifest


def load(src, issues=None):
    """The Cart in a .chgame, or CartError. `issues`, a list, collects the
    warnings too."""
    files, manifest = read(src)
    cart, found = model.from_manifest(manifest, files)
    if issues is not None:
        issues.extend(found)
    if cart is None:
        raise CartError(found)
    return cart


def check(src):
    """Every Issue of a .chgame, errors and warnings, without raising."""
    try:
        files, manifest = read(src)
    except CartError as e:
        return e.issues
    return model.from_manifest(manifest, files)[1]


def manifest_bytes(manifest):
    return (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def to_bytes(cart):
    """The .chgame's bytes. Raises CartError if the cart breaks a rule."""
    errors = [i for i in model.validate(cart) if i.error]
    if errors:
        raise CartError(errors)
    manifest, files = model.to_manifest(cart)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for name in ["info.json"] + sorted(files):
            zi = zipfile.ZipInfo(name, EPOCH)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.create_system = 0
            zi.external_attr = 0
            z.writestr(zi, manifest_bytes(manifest) if name == "info.json" else files[name], compresslevel=9)
    return out.getvalue()


def write(cart, path):
    data = to_bytes(cart)
    with open(path, "wb") as f:
        f.write(data)
    return data
