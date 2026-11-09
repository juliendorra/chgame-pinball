#!/usr/bin/env python3
"""Build native GCC 16.2 + binutils 2.47 with CHGame's WCH extensions.

Everything stays under .toolchains/current. --activate selects it for Arduino.
The installed board package supplies the same target C runtime as the vendor
baseline; the compiler, binutils and libgcc are rebuilt from current sources.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".toolchains/current"
SOURCES = WORK / "src"
DOWNLOADS = WORK / "downloads"
PREFIX = WORK / "native"
TARGET = "riscv-none-elf"
ARCH = "rv32imac_zicsr_xwchc"
PATCHES = ROOT / "tools/toolchain/patches"
PACKAGES = [
    ("gcc-16.2.0.tar.xz", "https://mirrors.kernel.org/gnu/gcc/gcc-16.2.0/gcc-16.2.0.tar.xz",
     "e6738e29597f733270731aa90600f37ffdc045079dfc27ec7e8192cc81085c3e"),
    ("binutils-2.47.tar.xz", "https://mirrors.kernel.org/gnu/binutils/binutils-2.47.tar.xz",
     "154ab23b60070e8f27013c22977f1129425d67d1e8acd6e13010e617811e4cff"),
    ("gmp-6.2.1.tar.bz2", "https://mirrors.kernel.org/gnu/gmp/gmp-6.2.1.tar.bz2",
     "eae9326beb4158c386e39a356818031bd28f3124cf915f8c5b1dc4c7a36b4d7c"),
    ("mpfr-4.1.0.tar.bz2", "https://mirrors.kernel.org/gnu/mpfr/mpfr-4.1.0.tar.bz2",
     "feced2d430dd5a97805fa289fed3fc8ff2b094c02d05287fd6133e7f1f0ec926"),
    ("mpc-1.2.1.tar.gz", "https://mirrors.kernel.org/gnu/mpc/mpc-1.2.1.tar.gz",
     "17503d2c395dfcf106b622dc142683c1199431d095367c6aacba6eec30340459"),
]
CTAGS_PACKAGE = (
    "ctags-5.8-arduino11.tar.xz",
    "https://github.com/arduino/ctags/releases/download/5.8-arduino11/ctags-5.8-arduino11.tar.xz",
    "9591ce86efa2ff7c277561706e6ace376201c5ec5f0b3925c50884ebf365d7e7",
)


def sha(path):
    with path.open("rb") as f:
        digest = hashlib.sha256()
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
        return digest.hexdigest()


def environment():
    env = dict(os.environ)
    env.update(TMPDIR=str(ROOT / ".cache/tmp"), CC="/usr/bin/clang", CXX="/usr/bin/clang++",
               CFLAGS="-O1 -g0", CXXFLAGS="-O1 -g0", MAKEINFO="true",
               PATH=str(PREFIX / "bin") + os.pathsep + env.get("PATH", ""))
    return env


def command(args, cwd, log, env):
    print(f"{time.strftime('%H:%M:%S')} {log.name}", flush=True)
    with log.open("a") as stream:
        stream.write("\nCOMMAND " + repr([str(a) for a in args]) + "\n")
        stream.flush()
        result = subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                                stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        print("\n".join(log.read_text(errors="replace").splitlines()[-35:]), file=sys.stderr)
        raise SystemExit(result.returncode)


def prepare(env):
    for name, url, digest in PACKAGES:
        archive = DOWNLOADS / name
        previous = ROOT / ".toolchains/downloads" / name
        if not archive.exists() and previous.exists():
            shutil.copy2(previous, archive)
        if not archive.exists():
            partial = archive.with_suffix(archive.suffix + ".part")
            command(["curl", "--fail", "--location", "--retry", "3", "--max-time", "600",
                     url, "-o", partial], ROOT, WORK / "downloads.log", env)
            if sha(partial) != digest:
                raise SystemExit(f"Source checksum mismatch: {partial}")
            partial.replace(archive)
        if sha(archive) != digest:
            raise SystemExit(f"Source checksum mismatch: {archive}")
        folder = name.removesuffix(".tar.xz").removesuffix(".tar.bz2").removesuffix(".tar.gz")
        if not (SOURCES / folder / "configure").exists():
            command(["tar", "-xf", archive, "-C", SOURCES], ROOT, WORK / "extract.log", env)
    gcc = SOURCES / "gcc-16.2.0"
    for folder in ("gmp-6.2.1", "mpfr-4.1.0", "mpc-1.2.1"):
        link = gcc / folder.split("-")[0]
        if not link.exists():
            link.symlink_to(Path("..") / folder)
    for source, patch, marker, file in (
        ("binutils-2.47", "binutils-2.47-xwchc.patch", "INSN_CLASS_XWCHC", "opcodes/riscv-opc.c"),
        ("gcc-16.2.0", "gcc-16.2-wch-fast-interrupt.patch", "WCH_FAST_MODE", "gcc/config/riscv/riscv.cc"),
        ("gcc-16.2.0", "gcc-16.2-xwchc.patch", "/* NAME */ xwchc", "gcc/config/riscv/riscv-ext.def"),
    ):
        if marker not in (SOURCES / source / file).read_text():
            command(["patch", "--batch", "--forward", "-p1", "-i", PATCHES / patch],
                    SOURCES / source, WORK / "patch.log", env)

    # Keep libc/printf constant for the initial compiler equivalence study.
    # These are RISC-V objects, not Intel host programs. None is executed here.
    vendor = ROOT / ".arduino15/packages/CHGame/tools/riscv-none-embed-gcc/8.2.0/riscv-none-embed"
    sysroot = PREFIX / TARGET
    if not (sysroot / "lib/libc_nano.a").exists():
        if not (vendor / "lib/rv32imacxw/ilp32/libc_nano.a").exists():
            raise SystemExit("Install CHGame:ch32v@0.3.0 for the vendor runtime baseline")
        shutil.copytree(vendor / "include", sysroot / "include", dirs_exist_ok=True)
        shutil.copytree(vendor / "lib/rv32imacxw/ilp32", sysroot / "lib", dirs_exist_ok=True)


def build_binutils(jobs, env):
    build = WORK / "build/binutils"
    build.mkdir(parents=True, exist_ok=True)
    if not (build / "Makefile").exists():
        command([SOURCES / "binutils-2.47/configure", f"--prefix={PREFIX}", f"--target={TARGET}",
                 "--build=aarch64-apple-darwin", "--host=aarch64-apple-darwin",
                 f"--with-sysroot={PREFIX / TARGET}", "--disable-nls", "--disable-werror",
                 "--disable-gdb", "--disable-gdbserver", "--disable-sim", "--disable-gprofng",
                 "--without-debuginfod", "--disable-shared", "--with-system-zlib"],
                build, WORK / "binutils-configure.log", env)
    command(["make", f"-j{jobs}", "MAKEINFO=true"], build, WORK / "binutils-build.log", env)
    command(["make", "MAKEINFO=true", "install"], build, WORK / "binutils-install.log", env)


def build_gcc(jobs, env):
    build = WORK / "build/gcc"
    build.mkdir(parents=True, exist_ok=True)
    if not (build / "Makefile").exists():
        command([SOURCES / "gcc-16.2.0/configure", f"--prefix={PREFIX}", f"--target={TARGET}",
                 "--build=aarch64-apple-darwin", "--host=aarch64-apple-darwin",
                 "--enable-languages=c,c++", "--enable-lto", "--disable-bootstrap",
                 "--disable-multilib", "--disable-nls", "--disable-shared", "--disable-threads",
                 "--disable-libgomp", "--disable-libquadmath", "--disable-libsanitizer",
                 "--disable-libssp", "--disable-libatomic", "--disable-werror", "--without-isl",
                 "--with-newlib", "--with-gnu-as", "--with-gnu-ld", "--with-system-zlib",
                 f"--with-arch={ARCH}", "--with-abi=ilp32", "--enable-checking=release",
                 f"--with-sysroot={PREFIX / TARGET}", "--with-native-system-header-dir=/include",
                 "--with-pkgversion=CHGame native arm64 GCC 16.2 with Xwchc and WCH fast interrupts"],
                build, WORK / "gcc-configure.log", env)
    command(["make", f"-j{jobs}", "MAKEINFO=true", "configure-gcc"], build, WORK / "gcc-configure.log", env)
    command(["make", "MAKEINFO=true", "riscv-regen"], build / "gcc", WORK / "gcc-regen.log", env)
    command(["make", f"-j{jobs}", "MAKEINFO=true", "all-gcc"], build, WORK / "gcc-build.log", env)
    command(["make", "MAKEINFO=true", "install-gcc"], build, WORK / "gcc-install.log", env)
    command(["make", f"-j{jobs}", "MAKEINFO=true", "all-target-libgcc"], build, WORK / "libgcc-build.log", env)
    command(["make", "MAKEINFO=true", "install-target-libgcc"], build, WORK / "libgcc-install.log", env)


def build_stdcxx(jobs, env):
    """Install matching GCC 16 C++ headers/runtime, including nano aliases."""
    build = WORK / "build/gcc"
    flags = "-Os -g0 -ffunction-sections -fdata-sections"
    command(["make", f"-j{jobs}", "MAKEINFO=true", f"CXXFLAGS_FOR_TARGET={flags}",
             f"CFLAGS_FOR_TARGET={flags}", "all-target-libstdc++-v3"],
            build, WORK / "libstdcxx-build.log", env)
    command(["make", "MAKEINFO=true", "install-target-libstdc++-v3"],
            build, WORK / "libstdcxx-install.log", env)
    for name in ("libstdc++", "libsupc++"):
        library = PREFIX / TARGET / "lib" / (name + ".a")
        shutil.copy2(library, library.with_name(name + "_nano.a"))


def verify(env):
    gcc = PREFIX / "bin" / (TARGET + "-gcc")
    print(subprocess.check_output([str(gcc), "--version"], env=env, text=True).splitlines()[0])
    # Arduino invokes plain ar, not gcc-ar. BFD must discover the matching LTO
    # plugin when indexing slim LTO objects in its library archives.
    plugins = PREFIX / "lib/bfd-plugins"
    plugins.mkdir(parents=True, exist_ok=True)
    plugin = plugins / "liblto_plugin.so"
    if not plugin.exists():
        plugin.symlink_to(Path("../../libexec/gcc") / TARGET / "16.2.0/liblto_plugin.so")
    host = []
    for name in ("gcc", "g++", "as", "ld", "ar", "gcc-ar", "gcc-nm", "gcc-ranlib",
                 "objcopy", "objdump", "readelf", "size", "nm", "ranlib"):
        program = PREFIX / "bin" / (TARGET + "-" + name)
        desc = subprocess.check_output(["file", "-b", str(program)], text=True)
        if "arm64" not in desc or "x86_64" in desc:
            raise SystemExit(f"Host tool is not native ARM64: {program}: {desc}")
        host.append(name)
        alias = PREFIX / "bin" / ("riscv-none-embed-" + name)
        if not alias.exists():
            alias.symlink_to(TARGET + "-" + name)
    for name in ("cc1", "cc1plus", "collect2", "lto1", "lto-wrapper", "liblto_plugin.so"):
        program = PREFIX / "libexec/gcc" / TARGET / "16.2.0" / name
        desc = subprocess.check_output(["file", "-b", str(program)], text=True)
        if "arm64" not in desc or "x86_64" in desc:
            raise SystemExit(f"Internal host tool is not native ARM64: {program}: {desc}")
        host.append(name)
    runtime_lib = PREFIX / TARGET / "lib"
    runtime_hashes = {name: sha(runtime_lib / name) for name in
                      ("libc.a", "libc_nano.a", "libm.a", "libprintf.a", "libnosys.a", "nano.specs", "nosys.specs")}
    manifest = dict(gcc="16.2.0", binutils="2.47", host="arm64-apple-darwin", target=TARGET,
                    march=ARCH, abi="ilp32", wch_fast_interrupts=True, xwchc=True,
                    source_packages=PACKAGES, host_tools=host,
                    runtime="CHGame 0.3.0 vendor RV32IMACXW libc/printf; rebuilt GCC 16.2 libgcc",
                    runtime_hashes=runtime_hashes,
                    cpp_runtime="GCC 16.2 libstdc++ and libsupc++, built with -Os; nano names alias the same libraries",
                    patches={p.name: sha(p) for p in PATCHES.glob("*.patch") if "16.2" in p.name or "2.47" in p.name})
    (PREFIX / "chgame-current.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Native host checks passed. Run tools/verify_current_gcc.py for target semantics.")


def activate(env, jobs):
    """Select the compiler using Arduino's supported, workspace-local overrides."""
    core = ROOT / ".arduino15/packages/CHGame/hardware/ch32v/0.3.0"
    builtin = ROOT / ".arduino15/packages/builtin/tools/ctags/5.8-arduino11/ctags"
    if not core.is_dir() or not builtin.is_file():
        raise SystemExit("Install CHGame:ch32v@0.3.0 before --activate")
    desc = subprocess.check_output(["file", "-b", str(builtin)], text=True)
    if "arm64" not in desc or "x86_64" in desc:
        name, url, digest = CTAGS_PACKAGE
        archive = DOWNLOADS / name
        cached = ROOT / ".toolchains/downloads" / name
        if not archive.exists() and cached.exists():
            shutil.copy2(cached, archive)
        if not archive.exists():
            command(["curl", "--fail", "--location", "--retry", "3", "--max-time", "600",
                     url, "-o", archive], ROOT, WORK / "ctags-download.log", env)
        if sha(archive) != digest:
            raise SystemExit(f"ctags source checksum mismatch: {archive}")
        source = SOURCES / "ctags-5.8-arduino11"
        if not source.exists():
            command(["tar", "-xf", archive, "-C", SOURCES], ROOT, WORK / "extract.log", env)
        for path in list(source.glob("*.c")) + list(source.glob("*.h")):
            original = path.read_bytes()
            fixed = original.replace(b"__unused__", b"CTAGS_UNUSED").replace(b"__printf__", b"CTAGS_PRINTF")
            if fixed != original:
                path.write_bytes(fixed)
        build = WORK / "build/ctags"
        build.mkdir(parents=True, exist_ok=True)
        if not (build / "Makefile").exists():
            command([source / "configure", f"--prefix={PREFIX}"], build, WORK / "ctags-build.log", env)
        command(["make", f"-j{jobs}"], build, WORK / "ctags-build.log", env)
        desc = subprocess.check_output(["file", "-b", str(build / "ctags")], text=True)
        if "arm64" not in desc or "x86_64" in desc:
            raise SystemExit(f"ctags is not native ARM64: {desc}")
        backup = WORK / "original/ctags"
        backup.parent.mkdir(exist_ok=True)
        if not backup.exists():
            shutil.copy2(builtin, backup)
        shutil.copy2(build / "ctags", builtin)
    (core / "platform.local.txt").write_text(
        f"compiler.path={PREFIX}/bin/\n"
        "compiler.objdump.flags=--all-headers --demangle --disassemble\n")
    (core / "boards.local.txt").write_text(
        f"rev0.build.march={ARCH}\nrev0.build.ch_extra_lib=-lprintf\n")
    print("Arduino configured for native GCC 16.2, Xwchc and WCH fast interrupts.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--stage", choices=("prepare", "binutils", "gcc", "stdcxx", "verify", "all"), default="all")
    ap.add_argument("--activate", action="store_true", help="select this compiler in the workspace Arduino package")
    args = ap.parse_args()
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise SystemExit("This build recipe targets native Apple silicon macOS")
    for p in (WORK, SOURCES, DOWNLOADS, PREFIX, ROOT / ".cache/tmp"):
        p.mkdir(parents=True, exist_ok=True)
    env = environment()
    if args.stage in ("prepare", "all"):
        prepare(env)
    if args.stage in ("binutils", "all"):
        build_binutils(max(1, args.jobs), env)
    if args.stage in ("gcc", "all"):
        build_gcc(max(1, args.jobs), env)
    if args.stage in ("stdcxx", "all"):
        build_stdcxx(max(1, args.jobs), env)
    if args.stage in ("verify", "all"):
        verify(env)
    if args.activate:
        if args.stage not in ("verify", "all"):
            raise SystemExit("--activate requires --stage verify or all")
        activate(env, max(1, args.jobs))


if __name__ == "__main__":
    main()
