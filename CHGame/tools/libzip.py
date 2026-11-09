"""Pack one of the bundled libraries as a ZIP the Arduino IDE installs.

    python tools/libzip.py CHGfx            -> out/CHGfx-1.3.0.zip
    python tools/libzip.py CHGfx CHSd CHGame [--out DIR]

The libraries live in the board package (platform/board/arduino/CHGame/
libraries) and arrive with it. CHGfx is also usable on its own, on any
CH32X035 board with the panel: this makes the archive for *Sketch > Include
Library > Add .ZIP Library*, or to attach to a release. The ZIP holds one
folder named after the library, as the IDE expects; the version is the one
in the library's library.properties.
"""
import argparse
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LIBRARIES = REPO / "platform" / "board" / "arduino" / "CHGame" / "libraries"
SKIP = {"__pycache__", "build", "out"}


def version(lib):
    for line in (lib / "library.properties").read_text(encoding="utf-8").splitlines():
        if line.startswith("version="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f"{lib.name}: no version in library.properties")


def pack(name, outdir):
    lib = LIBRARIES / name
    if not (lib / "library.properties").exists():
        raise SystemExit(f"{name}: no such library in {LIBRARIES}")
    out = outdir / f"{name}-{version(lib)}.zip"
    outdir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in lib.rglob("*") if p.is_file() and not (set(p.relative_to(lib).parts) & SKIP)
                   and p.suffix != ".pyc")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, f"{name}/{p.relative_to(lib).as_posix()}")
    print(f"{out.relative_to(REPO)}: {len(files)} files, {out.stat().st_size:,} B")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("libraries", nargs="+")
    ap.add_argument("--out", default=str(REPO / "out"))
    a = ap.parse_args()
    for name in a.libraries:
        pack(name, Path(a.out).resolve())


if __name__ == "__main__":
    sys.exit(main())
