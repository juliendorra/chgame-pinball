"""Archive the chgame-upload binaries per host and write their Arduino tool definition.

    python tools/release/make_tool_archives.py --base-url URL [--bin-dir out/chgame-upload] [--out out/dist]

For every host in out/chgame-upload/ (build_uploader.py): a
chgame-upload-<version>-<host>.tar.bz2 with one root folder,
chgame-upload-<version>/, holding the binary (Arduino strips one level on
extraction, so the binary lands in the tool folder). The version is the Go
tool's (main.go). The definition goes to tools/release/chgame_upload_tool.json,
which make_package.py puts in the index; it is committed, so the index can be
rebuilt without the binaries.

--base-url is required: the index pins an absolute URL and a SHA-256 for
every archive, and a default is how an index gets published still pointing
at a local test server. The archives are reproducible (sorted members, no
owner, one timestamp: the HEAD commit's), so the same tree gives the same
checksums.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (BIN_DIR, DIST, HOSTS, UPLOADER_TOOL_JSON, deterministic_tar,  # noqa: E402
                     fail, head_commit_time, say, sha256, uploader_version)


def package_tool(base_url: str, bin_dir: Path = BIN_DIR, out: Path = DIST, version: str | None = None,
                 tool_json: Path = UPLOADER_TOOL_JSON) -> dict:
    """version: the Go tool's unless given (stage.py gives a -local one, so a
    staged install is never mistaken for the release); tool_json: where the
    definition goes (the committed file unless given)."""
    version = version or uploader_version()
    mtime = head_commit_time()
    systems = []
    for triplet, _goos, _goarch, suffix in HOSTS:
        exe = Path(bin_dir) / triplet / f"chgame-upload{suffix}"
        if not exe.is_file():
            fail(f"missing {exe}: run python tools/release/build_uploader.py first")
        name = f"chgame-upload-{version}-{triplet}.tar.bz2"
        archive = Path(out) / name
        deterministic_tar(archive, [(f"chgame-upload-{version}/{exe.name}", exe)], mtime)
        size = archive.stat().st_size
        systems.append({
            "host": triplet,
            # GitHub release assets are flat: the URL is the base plus the file name.
            "url": f"{base_url.rstrip('/')}/{name}",
            "archiveFileName": name,
            "checksum": "SHA-256:" + sha256(archive),
            "size": str(size),
        })
        say(f"  {triplet:22s} {size:>9,} B  {name}")
    tool = {"name": "chgame-upload", "version": version, "systems": systems}
    Path(tool_json).write_text(json.dumps(tool, indent=2) + "\n", encoding="utf-8", newline="\n")
    say(f"wrote {tool_json} (chgame-upload {version}, {base_url})")
    return tool


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base-url", required=True,
                    help="where the release assets will live, e.g. https://github.com/bateske/CHGame/releases/download/v0.3.0")
    ap.add_argument("--bin-dir", type=Path, default=BIN_DIR)
    ap.add_argument("--out", type=Path, default=DIST)
    a = ap.parse_args(argv)
    package_tool(a.base_url, a.bin_dir, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
