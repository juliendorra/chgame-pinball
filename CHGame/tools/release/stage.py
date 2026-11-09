"""Stage a release on this machine: build it, test it as a new user, and serve
it to the Arduino IDE, with nothing published.

    python tools/release/stage.py [--serve] [--quick] [--skip-go] [--port 8765] [--suffix local]

Builds what release.py would (the uploader for the five hosts, its tool
archives, the platform archive, the index) into out/stage/, versioned
<platform version>-<suffix> (0.3.0-local) and the uploader likewise, with
every URL at http://localhost:<port>. A pre-release version sorts before the
release, so a staged install is offered the real 0.3.0 as an update when it
is published, and the uploader is fetched again rather than kept from here.

Then it runs acceptance.py against it: a fresh arduino-cli in out/newuser/
installs from the URL, and the checks there run, including every game and
app compiled from the installed package, the casino cart made from those
builds (out/stage/CHGame-Casino-<version>.chgame) and its SD card's contents
(out/stage/CHGame-sdcard-<version>.zip). --quick skips the twenty games, the
cart and the card.

--serve then keeps serving out/stage/ for the Arduino IDE: add
http://localhost:<port>/package_chgame_index.json under File > Preferences >
Additional boards manager URLs and install CHGame from Boards Manager
(platform/board/docs/trying-a-release.md walks through it).
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import OUT, platform_version, say, uploader_version  # noqa: E402
import acceptance  # noqa: E402
import build_uploader  # noqa: E402
import make_package  # noqa: E402
import make_tool_archives  # noqa: E402
import serve  # noqa: E402

STAGE = OUT / "stage"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", type=int, default=serve.DEFAULT_PORT)
    ap.add_argument("--suffix", default="local", help="pre-release label: <version>-<suffix>")
    ap.add_argument("--skip-go", action="store_true", help="use the uploader binaries already in out/chgame-upload/")
    ap.add_argument("--quick", action="store_true", help="skip compiling every game and the SD card")
    ap.add_argument("--serve", action="store_true", help="afterwards, serve out/stage/ for the Arduino IDE")
    ap.add_argument("--jobs", type=int, default=None, help="parallel game builds (acceptance.py's default)")
    a = ap.parse_args(argv)

    version = f"{platform_version()}-{a.suffix}"
    tool_version = f"{uploader_version()}-{a.suffix}"
    base = f"http://localhost:{a.port}"
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    say(f"=== staging CHGame {version} (chgame-upload {tool_version}) in {STAGE} ===")
    if not a.skip_go:
        build_uploader.build()
    tool_json = STAGE / "chgame_upload_tool.json"
    make_tool_archives.package_tool(base, out=STAGE, version=tool_version, tool_json=tool_json)
    archive = make_package.build_archive(version, STAGE)
    make_package.build_index(version, archive, base, STAGE, tool_json=tool_json)

    card = None if a.quick else STAGE / f"CHGame-sdcard-{version}.zip"
    rc = acceptance.run(STAGE, a.port, not a.quick, card, a.jobs or acceptance.DEFAULT_JOBS)
    if rc:
        return rc
    say("\n=== staged ===")
    for f in sorted(STAGE.iterdir()):
        if f.is_file():
            say(f"  {f.name:55s} {f.stat().st_size:>12,} B")
    if a.serve:
        say("")
        return serve.main(["--dist", str(STAGE), "--port", str(a.port)])
    say(f"\nTo install it in the Arduino IDE: python tools/release/serve.py, then add\n  {base}/{serve.INDEX}\n"
        "under File > Preferences > Additional boards manager URLs (platform/board/docs/trying-a-release.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
