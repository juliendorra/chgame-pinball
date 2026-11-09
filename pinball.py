#!/usr/bin/env python3
"""Use the workspace's CHGame tools and native RISC-V compiler for Pinball."""
from pathlib import Path
import os
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
(ROOT / ".cache/tmp").mkdir(parents=True, exist_ok=True)
env = dict(os.environ)
env.update({
    "ARDUINO_CONFIG_FILE": str(ROOT / "arduino-cli.yaml"),
    "ARDUINO_DIRECTORIES_DATA": str(ROOT / ".arduino15"),
    "ARDUINO_DIRECTORIES_DOWNLOADS": str(ROOT / ".arduino15/staging"),
    "ARDUINO_DIRECTORIES_USER": str(ROOT / "sketchbook"),
    "ARDUINO_BUILD_CACHE_PATH": str(ROOT / ".arduino15/cache"),
    "UV_CACHE_DIR": str(ROOT / ".cache/uv"),
    "TMPDIR": str(ROOT / ".cache/tmp"),
})
args = sys.argv[1:] or ["build"]
python = ROOT / ".venv/bin/python"
if not python.exists():
    python = Path(sys.executable)
if args[0] in ("web", "web-check"):
    raise SystemExit(subprocess.call([str(python), str(ROOT / "Pinball/tools/build_studio.py"),
                                    *(["--check"] if args[0] == "web-check" else []), *args[1:]], env=env, cwd=ROOT))
if args[0] in ("setup", "native-toolchain"):
    raise SystemExit(subprocess.call([sys.executable, str(ROOT / "tools/setup_pinball.py"), *args], env=env, cwd=ROOT))
if args[0] == "boards":
    raise SystemExit(subprocess.call([str(python), str(ROOT / "Pinball/tools/boards.py"), *args[1:]], env=env, cwd=ROOT))
if args[0] == "editor":
    raise SystemExit(subprocess.call([str(python), str(ROOT / "Pinball/tools/serve_studio.py"), *args[1:]], env=env, cwd=ROOT))
needs_compiler = (args[0] in ("build", "upload", "card") or
                  args[0] == "export" and "--no-build" not in args or
                  args[0] == "run" and "--device" in args)
if platform.system() == "Darwin" and platform.machine() == "arm64" and needs_compiler:
    native = ROOT / ".toolchains/current/native"
    if not (native / "chgame-current.json").exists():
        raise SystemExit("Run python3 pinball.py native-toolchain first.")
    overrides = ROOT / ".arduino15/packages/CHGame/hardware/ch32v/0.3.0/platform.local.txt"
    if not overrides.exists() or str(native / "bin") not in overrides.read_text():
        subprocess.run([sys.executable, str(ROOT / "tools/build_current_gcc.py"), "--stage", "verify", "--activate"],
                       cwd=ROOT, env=env, check=True)
if args[0] == "build":
    raise SystemExit(subprocess.call([str(python), str(ROOT / "Pinball/tools/build_studio.py"),
                                    "--build-firmware", *args[1:]], env=env, cwd=ROOT))
if args[0] == "upload":
    subprocess.run([str(python),str(ROOT / "Pinball/tools/build_studio.py"),"--build-firmware",
                    *(["--debug"] if "--debug" in args else [])],env=env,cwd=ROOT,check=True)
    raise SystemExit(subprocess.call([str(python),str(ROOT / "Pinball/tools/install_built.py"),*args[1:]],env=env,cwd=ROOT))
if needs_compiler:
    # Validate the browser target before an upload/export can publish a game update.
    subprocess.run([str(python), str(ROOT / "Pinball/tools/build_studio.py")], env=env, cwd=ROOT, check=True)
elif args[0] in ("export", "card"):
    subprocess.run([str(python), str(ROOT / "Pinball/tools/build_studio.py"), "--check",
                    "--firmware", str(ROOT / "Pinball/build/release/Pinball.ino.bin")], env=env, cwd=ROOT, check=True)
raise SystemExit(subprocess.call([str(python), str(ROOT / "tools/sd_saves.py"), "run",
                                "--sketch", str(ROOT / "Pinball"), *args], env=env, cwd=ROOT))
