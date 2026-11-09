"""Serve a built release on this machine, so Boards Manager can install it
before anything is published.

    python tools/release/serve.py [--dist out/stage] [--port 8765]

Then add http://localhost:8765/package_chgame_index.json to the Arduino IDE's
*File > Preferences > Additional boards manager URLs* (or pass it to
arduino-cli with --additional-urls) and install CHGame from Boards Manager.
Stop it with Ctrl+C when the install is done: nothing is fetched afterwards.

The index is served as it is, except that every URL whose file is in the
folder is pointed here. So a dry run of the real release (out/dist, whose
index points at GitHub) installs from here too, with the same checksums:
the archives do not depend on where they are hosted. The toolchain and
wchisp still come from their upstream URLs, as they do for every user.
"""
from __future__ import annotations

import argparse
import functools
import json
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import OUT, say  # noqa: E402

INDEX = "package_chgame_index.json"
DEFAULT_PORT = 8765


def local_index(dist: Path, base: str) -> bytes:
    index = json.loads((dist / INDEX).read_text(encoding="utf-8"))
    for pkg in index["packages"]:
        for entry in pkg.get("platforms", []) + [s for t in pkg.get("tools", []) for s in t["systems"]]:
            name = entry.get("archiveFileName", "")
            if name and (dist / name).is_file():
                entry["url"] = f"{base}/{name}"
    return (json.dumps(index, indent=2) + "\n").encode("utf-8")


class _Handler(SimpleHTTPRequestHandler):
    base = ""

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/" + INDEX:
            body = local_index(Path(self.directory), self.base)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, fmt, *args):         # one line per download, not per request header
        if self.command == "GET":
            say(f"  served {self.path}")


def start(dist: Path, port: int = DEFAULT_PORT) -> tuple[ThreadingHTTPServer, str]:
    """Serve dist/ on 127.0.0.1:port in a background thread; returns the server
    and the index URL. server.shutdown() stops it."""
    dist = Path(dist).resolve()
    if not (dist / INDEX).is_file():
        raise SystemExit(f"{dist / INDEX} not found: build the release first (stage.py, or release.py --dry-run)")
    base = f"http://localhost:{port}"
    handler = type("Handler", (_Handler,), {"base": base})
    server = ThreadingHTTPServer(("127.0.0.1", port), functools.partial(handler, directory=str(dist)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"{base}/{INDEX}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dist", type=Path, default=OUT / "stage", help="the folder with the index and the archives")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    a = ap.parse_args(argv)
    server, url = start(a.dist, a.port)
    say(f"serving {a.dist.resolve()}\n\nBoards Manager URL (Arduino IDE: File > Preferences > Additional boards manager URLs):\n"
        f"  {url}\n\nCtrl+C to stop.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
