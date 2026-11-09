"""Build the Go uploader, chgame-upload, for every host Arduino runs on.

    python tools/release/build_uploader.py [--host TRIPLET ...] [--out DIR] [--go PATH]

Cross-compiles platform/bootloader/host/go from one machine with cgo off
into out/chgame-upload/<host>/chgame-upload[.exe] (what
make_tool_archives.py packs). Go comes from --go, $CHGAME_GO, a toolchain
unpacked in .toolchains/go at the repository root, or the PATH (1.25 or
later). Prints the size of each binary.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import BIN_DIR, GO_DIR, HOSTS, REPO, fail, run, say  # noqa: E402


def find_go(explicit: str | None = None) -> str:
    for cand in (explicit, os.environ.get("CHGAME_GO"),
                 REPO / ".toolchains" / "go" / "bin" / ("go.exe" if os.name == "nt" else "go"),
                 shutil.which("go")):
        if cand and Path(cand).is_file():
            return str(cand)
    fail("Go not found: pass --go, set CHGAME_GO, put go on the PATH, or unpack a toolchain in .toolchains/go "
         "(needs Go 1.25 or later)")


def build(hosts=None, out: Path = BIN_DIR, go: str | None = None) -> dict[str, Path]:
    go = find_go(go)
    say(f"go: {run([go, 'version']).stdout.strip()}")
    built = {}
    for triplet, goos, goarch, suffix in HOSTS:
        if hosts and triplet not in hosts:
            continue
        dest = Path(out) / triplet / f"chgame-upload{suffix}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, GOOS=goos, GOARCH=goarch, CGO_ENABLED="0", GOTOOLCHAIN="local")
        run([go, "build", "-trimpath", "-buildvcs=false", "-ldflags", "-s -w", "-o", str(dest), "."],
            cwd=GO_DIR, env=env)
        built[triplet] = dest
        say(f"  {triplet:22s} {dest.stat().st_size:>9,} B")
    return built


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--host", action="append", choices=[h[0] for h in HOSTS], help="build this host only (repeatable)")
    ap.add_argument("--out", type=Path, default=BIN_DIR)
    ap.add_argument("--go", help="the go executable")
    a = ap.parse_args(argv)
    build(a.host, a.out, a.go)
    return 0


if __name__ == "__main__":
    sys.exit(main())
