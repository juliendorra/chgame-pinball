# Firmware compiler

The production Apple-silicon compiler is GCC 16.2 with binutils 2.47 and the
CHGame/WCH instruction patches. [CURRENT-GCC.md](CURRENT-GCC.md) records the
build and validation details; `python3 pinball.py native-toolchain` builds and
activates it. Downloads are pinned by SHA-256 in `tools/build_current_gcc.py`.

The web build does not need this toolchain. It uses Emscripten 4.0.15 and a
native Clang compiler for byte-for-byte gameplay and pixel parity validation.
See [licenses and patch notices](patches/README.md) and
[the build-script license](LICENSE-BUILD-SCRIPTS).
