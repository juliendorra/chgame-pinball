"""Build the CHGame Boards Manager package: the platform archive and the index.

    python tools/release/make_package.py --base-url URL [--version V] [--out out/dist]
    python tools/release/make_package.py --import-tool-defs      (once: see below)

Produces, in out/dist/:

    CHGame-ch32v-<version>.tar.bz2    the platform archive (one root folder, as
                                      Arduino requires): every file git tracks
                                      under platform/board/arduino/CHGame, so the
                                      core, the bootloaders, and the libraries
                                      with the games as their examples (their
                                      tools, art, data files and README GIFs
                                      included), minus _common.PACKAGE_EXCLUDE_*
    package_chgame_index.json         the Boards Manager index: one packager,
                                      CHGame, whose platform depends on three
                                      tools so that one URL installs everything:
                                      the RISC-V toolchain and wchisp (their
                                      definitions vendored in tool_defs/, URLs
                                      and checksums as upstream publishes them)
                                      and chgame-upload (chgame_upload_tool.json,
                                      written by make_tool_archives.py)

The version is platform.txt's version= line; --version must match it when
given (that number is what Boards Manager compares to offer an update, so it
is the one place a release is versioned). The index refuses uploader
archives built for another base URL.

--import-tool-defs reads the installed package_chgame_index.json (Arduino15)
and writes tool_defs/*.json from its riscv-none-embed-gcc and wchisp entries.
It was run once; the files are committed, and a release does not need an
installed core.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (DIST, PACKAGE_EXCLUDE_DIRS, PACKAGE_EXCLUDE_NAMES, PACKAGE_EXCLUDE_SUFFIXES,  # noqa: E402
                     PLATFORM, REPO, TOOL_DEFS, UPLOADER_TOOL_JSON, deterministic_tar, fail,
                     head_commit_time, platform_version, say, sha256)

PACKAGER = {
    "name": "CHGame",
    "maintainer": "bateske",
    "websiteURL": "https://github.com/bateske/CHGame",
    "email": "",
    "help": {"online": "https://github.com/bateske/CHGame/issues"},
}


def tracked_files() -> list[Path]:
    rel = PLATFORM.relative_to(REPO).as_posix()
    r = subprocess.run(["git", "ls-files", "-z", "--", rel], cwd=REPO, capture_output=True)
    if r.returncode:
        fail("git ls-files failed: " + r.stderr.decode(errors="replace"))
    return [REPO / p for p in r.stdout.decode("utf-8").split("\0") if p]


def keep(path: Path) -> bool:
    rel = path.relative_to(PLATFORM)
    if path.name in PACKAGE_EXCLUDE_NAMES or path.suffix in PACKAGE_EXCLUDE_SUFFIXES:
        return False
    return not any(part in PACKAGE_EXCLUDE_DIRS for part in rel.parts[:-1])


def nested_sketches(files: list[Path]) -> list[str]:
    """Sketches (X/X.ino) inside another sketch's folder, below a library's examples/."""
    sketches = {p.parent for p in files if p.suffix == ".ino" and p.stem == p.parent.name}
    return sorted(s.relative_to(PLATFORM).as_posix() for s in sketches
                  if "examples" in s.relative_to(PLATFORM).parts and any(a in sketches for a in s.parents))


def build_archive(version: str, out: Path = DIST) -> Path:
    """version is platform.txt's for a release. stage.py passes another (0.3.0-local):
    the archive's platform.txt then says that, as the folder it installs to does."""
    root = f"CHGame-ch32v-{version}"
    files = [p for p in tracked_files() if keep(p)]
    for p in files:
        if any(part in PACKAGE_EXCLUDE_DIRS for part in p.relative_to(PLATFORM).parts[:-1]):
            fail(f"refusing to package {p.relative_to(REPO)}: a build directory")
        if not p.is_file():
            fail(f"{p.relative_to(REPO)} is tracked but missing from the working tree")
    nested = nested_sketches(files)
    if nested:
        fail("these sketches sit inside another example's folder, so File > Examples would show them nested in it:\n  "
             + "\n  ".join(nested) + "\nmove them, or exclude their folder (_common.PACKAGE_EXCLUDE_DIRS)")
    members = [(f"{root}/{p.relative_to(PLATFORM).as_posix()}", p) for p in files]
    if version != platform_version():
        txt = PLATFORM.joinpath("platform.txt").read_bytes()
        txt = re.sub(rb"(?m)^version=.*$", b"version=" + version.encode(), txt, count=1)
        members = [(a, txt if a == f"{root}/platform.txt" else p) for a, p in members]
    archive = Path(out) / f"{root}.tar.bz2"
    deterministic_tar(archive, members, head_commit_time())
    total = sum(p.stat().st_size for p in files)
    say(f"platform archive: {len(files)} files, {total:,} B of content, {archive.stat().st_size:,} B compressed")
    for p in sorted(files, key=lambda q: q.stat().st_size, reverse=True)[:10]:
        say(f"  {p.stat().st_size:>10,}  {p.relative_to(PLATFORM).as_posix()}")
    return archive


def tool_def(name: str) -> dict:
    f = TOOL_DEFS / f"{name}.json"
    if not f.exists():
        fail(f"missing {f}: run make_package.py --import-tool-defs with the CHGame core installed")
    return json.loads(f.read_text(encoding="utf-8"))


def uploader_def(base_url: str, tool_json: Path = UPLOADER_TOOL_JSON) -> dict:
    if not Path(tool_json).exists():
        fail(f"missing {tool_json}: run build_uploader.py, then make_tool_archives.py --base-url ...")
    tool = json.loads(Path(tool_json).read_text(encoding="utf-8"))
    prefix = base_url.rstrip("/")
    bad = [s["url"] for s in tool["systems"] if not s["url"].startswith(prefix + "/")]
    if bad:
        fail("the uploader archives were built for a different base URL:\n  " + "\n  ".join(bad[:2])
             + f"\nexpected them under {prefix}\nre-run: python tools/release/make_tool_archives.py --base-url {prefix}")
    return tool


def build_index(version: str, archive: Path, base_url: str, out: Path = DIST,
                tool_json: Path = UPLOADER_TOOL_JSON) -> Path:
    gcc, wchisp, uploader = tool_def("riscv-none-embed-gcc"), tool_def("wchisp"), uploader_def(base_url, tool_json)
    platform = {
        "name": "CHGame Boards",
        "architecture": "ch32v",
        "version": version,
        "category": "Contributed",
        "help": PACKAGER["help"],
        "url": f"{base_url.rstrip('/')}/{archive.name}",
        "archiveFileName": archive.name,
        "checksum": "SHA-256:" + sha256(archive),
        "size": str(archive.stat().st_size),
        "boards": [{"name": "CHGame Rev0"}],
        "toolsDependencies": [{"packager": "CHGame", "name": t["name"], "version": t["version"]}
                              for t in (gcc, wchisp, uploader)],
    }
    index = {"packages": [dict(PACKAGER, platforms=[platform], tools=[gcc, wchisp, uploader])]}
    path = Path(out) / "package_chgame_index.json"
    path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def import_tool_defs() -> None:
    home = Path(os.environ.get("LOCALAPPDATA", "")) / "Arduino15" if os.name == "nt" else Path.home() / ".arduino15"
    src = home / "package_chgame_index.json"
    if not src.exists():
        fail(f"{src} not found: install the CHGame core once, or write tool_defs/*.json by hand")
    pkg = json.loads(src.read_text(encoding="utf-8"))["packages"][0]
    TOOL_DEFS.mkdir(exist_ok=True)
    for tool in pkg["tools"]:
        if tool["name"] in ("riscv-none-embed-gcc", "wchisp"):
            (TOOL_DEFS / f"{tool['name']}.json").write_text(json.dumps(tool, indent=2) + "\n", encoding="utf-8", newline="\n")
            say(f"tool_defs/{tool['name']}.json: {tool['version']}, {len(tool['systems'])} hosts")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", help="must match platform.txt (the default)")
    ap.add_argument("--base-url", help="where the archives will be hosted (required unless --import-tool-defs)")
    ap.add_argument("--out", type=Path, default=DIST)
    ap.add_argument("--import-tool-defs", action="store_true")
    a = ap.parse_args(argv)
    if a.import_tool_defs:
        import_tool_defs()
        return 0
    if not a.base_url:
        ap.error("--base-url is required")
    version = platform_version()
    if a.version and a.version != version:
        fail(f"--version {a.version} does not match platform.txt ({version}). Bump platform.txt: that is the "
             "number Boards Manager compares to offer updates.")
    a.out.mkdir(parents=True, exist_ok=True)
    archive = build_archive(version, a.out)
    index = build_index(version, archive, a.base_url, a.out)
    say(f"index   : {index}")
    say(f"Boards Manager URL once published: {a.base_url.rstrip('/')}/{index.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
