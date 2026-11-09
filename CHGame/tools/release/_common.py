"""What the release scripts share: where things are, the hosts, the archive
rules, and a few helpers. Nothing here runs on its own."""
from __future__ import annotations

import hashlib
import io
import re
import subprocess
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent                      # tools/release
REPO = HERE.parents[1]
PLATFORM = REPO / "platform" / "board" / "arduino" / "CHGame"
PLATFORM_TXT = PLATFORM / "platform.txt"
CHANGELOG = REPO / "platform" / "board" / "CHANGELOG.md"
BOOTLOADER = REPO / "platform" / "bootloader"
GO_DIR = BOOTLOADER / "host" / "go"
PY_DIR = BOOTLOADER / "host" / "py"
OUT = REPO / "out"
DIST = OUT / "dist"
BIN_DIR = OUT / "chgame-upload"
TOOL_DEFS = HERE / "tool_defs"
UPLOADER_TOOL_JSON = HERE / "chgame_upload_tool.json"

# (Arduino host triplet, GOOS, GOARCH, executable suffix)
HOSTS = [
    ("x86_64-mingw32", "windows", "amd64", ".exe"),
    ("x86_64-pc-linux-gnu", "linux", "amd64", ""),
    ("aarch64-linux-gnu", "linux", "arm64", ""),
    ("x86_64-apple-darwin", "darwin", "amd64", ""),
    ("arm64-apple-darwin", "darwin", "arm64", ""),
]

# The platform archive is every file git tracks under platform/board/arduino/CHGame,
# except these. (Build output is never tracked, so a walk of the working tree is
# not used: the games' build/ and out/ folders alone would add hundreds of MB.)
PACKAGE_EXCLUDE_NAMES = {".gitignore", "platform.local.txt"}
# "probes": hardware probe sketches kept in a game's tools/ (CHBlackjack's
# FlashProbe). In the package they would show in File > Examples nested inside
# the game; they are for developers and stay in the repository.
PACKAGE_EXCLUDE_DIRS = {"build", "out", "__pycache__", "probes"}
PACKAGE_EXCLUDE_SUFFIXES = {".pyc"}


def run(cmd, cwd=None, env=None, check=True, capture=True):
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace",
                       capture_output=capture)
    if check and r.returncode:
        raise SystemExit(f"{' '.join(str(c) for c in cmd)} failed ({r.returncode})\n{(r.stdout or '') + (r.stderr or '')}")
    return r


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def platform_version() -> str:
    """The version= line of platform.txt: the number Boards Manager compares
    with an installed package to decide whether to offer an update."""
    for line in PLATFORM_TXT.read_text(encoding="utf-8").splitlines():
        if line.startswith("version="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f"no version= line in {PLATFORM_TXT}")


def uploader_version() -> str:
    """The Go tool's version (main.go), which the index names."""
    m = re.search(r'^\s*(?:const|var)?\s*version\s*=\s*"([^"]+)"', (GO_DIR / "main.go").read_text(encoding="utf-8"), re.M)
    if not m:
        raise SystemExit(f"no `version = \"...\"` in {GO_DIR / 'main.go'}")
    return m.group(1)


def python_uploader_version() -> str:
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', (PY_DIR / "chgame_upload" / "__init__.py").read_text(encoding="utf-8"), re.M)
    if not m:
        raise SystemExit(f"no __version__ in {PY_DIR / 'chgame_upload' / '__init__.py'}")
    return m.group(1)


def changelog_section(version: str) -> str:
    """The `## <version>` (or `## <version> (<date>)`) section of CHANGELOG.md."""
    lines = CHANGELOG.read_text(encoding="utf-8").splitlines()
    out, on = [], False
    for ln in lines:
        if re.match(r"^## " + re.escape(version) + r"( |$)", ln):
            on = True
            continue
        if ln.startswith("## "):
            on = False
        if on:
            out.append(ln)
    return "\n".join(out).strip()


def head_commit_time() -> int:
    r = run(["git", "log", "-1", "--format=%ct"], cwd=REPO)
    return int(r.stdout.strip() or "0")


def deterministic_tar(out_path: Path, members: list[tuple[str, Path | bytes]], mtime: int) -> None:
    """A .tar.bz2 whose bytes depend only on the files' contents and names:
    sorted members, uid/gid 0, no owner names, one mtime, modes 0644/0755.
    A member's source is a file, or its contents as bytes (mode 0644)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    dirs_done = set()
    with tarfile.open(out_path, "w:bz2") as tf:
        for arcname, src in sorted(members, key=lambda m: m[0]):
            parts = arcname.split("/")
            for i in range(1, len(parts)):
                d = "/".join(parts[:i])
                if d not in dirs_done:
                    dirs_done.add(d)
                    ti = tarfile.TarInfo(d)
                    ti.type = tarfile.DIRTYPE
                    ti.mode = 0o755
                    ti.mtime = mtime
                    tf.addfile(ti)
            data = src if isinstance(src, bytes) else Path(src).read_bytes()
            ti = tarfile.TarInfo(arcname)
            ti.size = len(data)
            ti.mtime = mtime
            ti.mode = 0o755 if (not isinstance(src, bytes) and Path(src).suffix in ("", ".exe", ".sh")
                                and _looks_executable(src)) else 0o644
            tf.addfile(ti, io.BytesIO(data))


def _looks_executable(src: Path) -> bool:
    src = Path(src)
    if src.suffix in (".exe", ".sh"):
        return True
    try:
        head = src.read_bytes()[:4]
    except OSError:
        return False
    return head[:2] in (b"MZ", b"#!") or head == b"\x7fELF" or head in (b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe")


def say(msg: str) -> None:
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:           # a cp1252 console and a changelog with arrows in it
        print(msg.encode(sys.stdout.encoding or "ascii", "replace").decode(sys.stdout.encoding or "ascii"), flush=True)


def fail(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(1)
