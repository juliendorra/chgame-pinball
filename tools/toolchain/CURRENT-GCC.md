# Native current GCC port: validation record

Validated on 22 October 2026. This file records completed evidence, not a
blanket assertion of equivalence with every undocumented WCH compiler change.
LLVM work follows this GCC baseline.
The [exploration record](EXPLORATION.md) also preserves failed approaches and
corrected assumptions, including the separate Clang experiment.

## Toolchain

- GCC 16.2.0, current stable release, built for native ARM64 macOS.
- GNU binutils 2.47, rebuilt with the public Xwchc patch rebased to this release.
- Target: `riscv-none-elf`, `rv32imac_zicsr_xwchc`, ILP32, CHGame Rev0 / CH32X035.
- WCH fast interrupt handling ported to the GCC 16 backend.
- GCC 16 libgcc, C++ headers, libstdc++ and libsupc++ rebuilt from source.
  The nano library names alias the same `-Os` builds. A C++17 container link
  smoke test passed. C++23 standard library modules are not validated with the
  legacy C runtime; their optional build reported missing C math aliases.
- The initial comparison retains the board package's RV32IMACXW C/printf runtime
  to isolate the compiler migration. It does not claim a newlib upgrade.
- Installation: `.toolchains/current/native`, selected in the local Arduino
  overrides. The GCC 12 installation remains available as a fallback.

The official GCC and binutils source archives passed detached-signature checks
using the GNU keyring. Archive hashes are pinned in `tools/build_current_gcc.py`.
Public patch provenance and licensing are in [patches/README.md](patches/README.md).

## Completed checks

All compiler drivers, assembler/linker/archive utilities, C/C++ frontends,
collect2, LTO backend/wrapper and LTO plugin were checked as native ARM64.
The compiler reports GCC 16.2.0.

`tools/verify_current_gcc.py` passed:

- 8,776 memory instruction cases match the original vendor assembler byte for
  byte. These include all 8,704 compact-register/offset combinations for the
  eight XW forms and 72 boundary cases which remain ordinary instructions.
- The same 8,776 cases without Xwchc contain only ordinary four-byte encodings.
- Eight invalid explicit operands and two incompatible extension combinations
  are rejected.
- Leaf handlers, non-leaf handlers clobbering all ABI-preserved registers, and
  compile-only 5,000-byte stack-frame handlers pass at `-Os`, `-O2`, and `-O3`.
  They return with `mret`, preserve required s-registers, and avoid redundant
  saves of hardware-preserved registers.
- Four C byte/halfword load/store functions produce compressed XW instructions;
  the `__riscv_xwchc` version macro is correct.
- Both upstream-style GCC regression fixtures compile successfully.
- Arduino plain-`ar` archives resolve slim LTO objects using the installed BFD
  plugin; an end-to-end archive link test passed.
- The complete patch series applies cleanly to pristine copies of the touched
  release files, including generated options, documentation and tests.

Raw checks are in `.toolchains/current/verification/results.json` and its
assembly/object/disassembly files. Large-frame fixtures are compile-only and
must not be executed on the handheld's 2 KB stack.

## Firmware and device evidence

All **25 configurations** (Ball release/debug, all 20 upstream games and three
apps) compile and fit flash, save-page and static-RAM limits with both compilers.
Sources are hash-identical for each pair. GCC 16 produces smaller flash images
in every pair: reductions range from 0.89% to 5.11%. Static RAM changes in either
direction; all builds fit. These are build checks for the upstream examples,
not a claim that all their gameplay paths were tested on hardware.
The [size breakdown](SIZE.md) explains the common-code savings and their limits.
Ball's dense music benchmark uses the newer local game sources, which are
separate from the GCC tooling commit. The previously committed single-ball
sketch was also built with GCC 16: release 8,168 bytes / 11,428 bytes RAM and
debug 10,720 bytes / 11,608 bytes RAM, both within the unchanged limits.

| Sketch / mode | GCC 8.2 flash | GCC 16.2 flash | Change | GCC 8.2 RAM | GCC 16.2 RAM |
|---|---:|---:|---:|---:|---:|
| Ball release | 11,964 | 11,372 | -592 | 18,104 | 18,068 |
| Ball debug | 15,500 | 14,708 | -792 | 18,304 | 18,268 |
| CHBackgammon release | 49,488 | 48,856 | -632 | 16,524 | 16,624 |
| CHBingo release | 36,964 | 36,048 | -916 | 14,800 | 14,808 |
| CHBlackjack release | 46,388 | 45,908 | -480 | 15,468 | 15,456 |
| CHBoardwalk release | 49,832 | 48,912 | -920 | 14,924 | 14,964 |
| CHCheckers release | 41,864 | 40,576 | -1,288 | 16,932 | 16,992 |
| CHChess release | 48,480 | 47,236 | -1,244 | 17,368 | 17,372 |
| CHCraps release | 50,384 | 49,304 | -1,080 | 15,464 | 15,372 |
| CHCrossword release | 50,020 | 49,552 | -468 | 17,100 | 17,092 |
| CHDominoes release | 43,436 | 42,716 | -720 | 16,744 | 16,888 |
| CHFour release | 36,736 | 35,864 | -872 | 16,300 | 16,408 |
| CHMahjong release | 48,776 | 47,536 | -1,240 | 17,700 | 17,688 |
| CHPoker release | 48,952 | 47,804 | -1,148 | 15,384 | 15,392 |
| CHRoulette release | 49,892 | 49,448 | -444 | 15,968 | 16,012 |
| CHSlots release | 48,076 | 47,020 | -1,056 | 14,796 | 14,652 |
| CHSnakes release | 37,280 | 36,324 | -956 | 15,240 | 15,312 |
| CHSolitaire release | 31,304 | 30,656 | -648 | 16,580 | 16,568 |
| CHTicTacToe release | 50,248 | 49,220 | -1,028 | 14,540 | 14,556 |
| CHWordWheel release | 50,120 | 49,580 | -540 | 14,904 | 14,940 |
| CHWords release | 50,044 | 48,860 | -1,184 | 15,612 | 15,596 |
| CHYacht release | 44,652 | 43,872 | -780 | 15,140 | 15,036 |
| CHSDtoSerial release | 46,224 | 44,692 | -1,532 | 17,192 | 17,120 |
| CHSDtoUSB release | 43,072 | 41,028 | -2,044 | 16,900 | 16,836 |
| CHStlView release | 31,856 | 30,744 | -1,112 | 16,148 | 16,032 |

The temporary `fixtures/PortProbe/` ran on the physical CHGame Rev0:

- 64 execution cases cover all eight XW forms at minimum/maximum offsets and
  four edge values, cross-checked against forced ordinary encodings: zero errors.
- 20,000 software interrupts deliberately clobber hardware-saved registers and
  all s-registers; register sentinels and stack balance: zero errors.
- 100 software interrupts preempt SysTick using the configured two-level hardware
  stack: all passed, zero nesting failures.

The generated assembly is reproducible with `fixtures/generate_port_probe.py`.
It does not write saves or SD data. The probe was removed after testing.

Ball's GCC 16 debug build sustained **2,393 balls at 60 fps**, with four music
voices, during the 10-second steady interval: 602 frames, zero late frames,
16.075 ms mean / 16.299 ms maximum full-frame time, 732-byte stack high-water.
This is 11.4% more balls than the previous GCC 12 measurement of 2,148. Mute,
pause/resume, colour rendering and continued sequencing were checked. Startup
and control transitions are outside this steady-state timing measurement.

The [fixed-count performance follow-up](PERFORMANCE.md) confirms an improvement
and separates application XW selection from other toolchain changes. The 11.4%
observed population increase is not a pure GCC-version speedup claim.

The normal `ball.py build` produced exactly the same release binary as the
isolated comparison build. It was exported and uploaded successfully:
**11,372 bytes, CRC32 `0x6C9B2D98`**, SHA-256
`4463f5068dc61f09f727fe8554dae00662e172781e5bde3b5ee800fe38ff129b`.
The bootloader accepted its CRC and started the application.

Machine-readable results: [all paired builds](current-gcc-results.json),
[compiler checks](evidence/compiler.json), [device probe](evidence/device-probe.json),
[Ball timing](evidence/device-ball.json), [release upload](evidence/device-release.json)
and [toolchain manifest](evidence/manifest.json).

This establishes the documented XW and fast-interrupt features required by
CHGame on CH32X035. It does not establish bit-identical code generation, recover
undocumented vendor optimizers, cover every QingKe/FPU configuration, or replace
a full GCC/binutils regression campaign. The included compiler regression
fixtures were run directly; the complete DejaGNU suites were not run.

## Reproduce

```sh
python3 tools/build_current_gcc.py --jobs 2 --activate
python3 tools/verify_current_gcc.py
python3 tools/compare_toolchains.py --all-examples --ball-debug \
  --variant wch8-xw native16-xw --output-dir .cache/current-gcc-study
```

Source downloads, builds, logs, installed tools and temporary files stay on the
workspace drive. Running the vendor baseline assembler/compiler for comparison
uses the existing Rosetta installation; the new compiler build and its host
executables are native. The system compiler is unchanged. `--activate` selects the new toolchain only
in this workspace’s Arduino package; omitting it leaves those settings alone.
The build recipe never uploads firmware.
