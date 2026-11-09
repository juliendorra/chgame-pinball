# Current GCC WCH patch series

The current port targets CHGame Rev0's integer-only CH32X035, hosted natively on
Apple silicon. Validation results belong in `../CURRENT-GCC.md`; the existence
of these patches alone does not establish hardware equivalence.

Apply in this order to the named pristine releases:

1. `binutils-2.47-xwchc.patch` to binutils 2.47.
2. `gcc-16.2-xwchc.patch` to GCC 16.2.0.
3. `gcc-16.2-wch-fast-interrupt.patch` to GCC 16.2.0.

The three GCC/binutils patches modify GNU software and are distributed under
GPL version 3 or later, consistent with those projects. See [COPYING3](COPYING3). Original
copyrights and authorship remain applicable.

## Provenance

The binutils patch derives from Andy Lin's public v2 submission of 24 November
2025:
https://sourceware.org/pipermail/binutils/2025-November/145893.html

`binutils-xwchc-upstream.patch` preserves that submitted diff. The 2.47 rebase
updates extension tables, parser locations, validation and option handling;
it retains the upstream opcode definitions and tests. Its naming is `Xwchc`
and `qk.c.*`, following the modern implementation, rather than the legacy
vendor spelling `xw` / `c.*`. Ordinary C loads/stores are compressed by GAS.
The source is a submitted patch, not a claim of upstream acceptance.

The GCC fast-interrupt port follows the approach in David Carne's patch as
published by HydraUSB3 for GCC 12.2:
https://github.com/hydrausb3/riscv-none-elf-gcc-xpack/blob/b9b8527/patches/gcc-12.2.0.patch.diff

The 16.2 port uses an explicit list of the sixteen hardware-preserved integer
registers, preserves the remaining register-save rules, handles large-frame
temporary registers and returns with `mret`. It includes attribute documentation
and a compiler regression fixture. Tests for this project do not establish
support for every QingKe core, floating-point ABI or nesting configuration.

The GCC Xwchc patch adds the extension declaration, generated option state,
extension documentation and a regression fixture. Existing GAS compression
performs instruction encoding; the compiler's conservative length accounting
is retained, as for ordinary compressed instructions. This is not a recovered
copy of WCH's undocumented GCC optimizer changes.

## Build and verification

From the workspace root:

```sh
python3 tools/build_current_gcc.py --jobs 2
python3 tools/verify_current_gcc.py
python3 tools/compare_toolchains.py --all-examples --ball-debug \
  --variant wch8-xw native16-xw --output-dir .cache/current-gcc-study
```

The build recipe pins source archive hashes and writes only workspace toolchain
and cache directories. Current GCC, binutils and libgcc are built from source.
For the initial equivalence study, the installed CHGame 0.3.0 board package
supplies its existing RV32IMACXW C/printf runtime. That runtime is a separate
dependency and is not included in the patch series. Building a replacement
newlib is a separate runtime migration, not a prerequisite for testing the
updated compiler.

Our source downloads were also checked against the official detached GNU
signatures using the GNU keyring. GCC's signing key was
`7F74F97C103468EE5D750B583AB00996FC26A641`; binutils' signing key was
`3A24BC1E8FB409FA9F14371813FCEF89DD9E3C4F`.

The assembler verifier checks all compact-register/offset combinations for the
eight instructions, boundary cases, disabled-extension behavior and invalid
operands. It compares bytes with the original vendor assembler. Compiler checks
cover the version macro, compressed C memory operations and interrupt register
preservation at multiple optimization levels. Device fixtures add actual opcode
execution, register sentinels and nested interrupt tests. Hardware results must
be recorded separately; compile-only large-frame tests must not be executed on
the handheld's 2 KB stack.

## Arduino helper portability

`ctags-5.8-arduino11-tempdir.patch` applies to Arduino ctags 5.8-arduino11.
It retains the original TMPDIR override and uses Windows TEMP/TMP when that
override is absent. This derived ctags change is GPL-2.0-or-later, consistent
with ctags' own COPYING notice in the release licenses/ctags directory. The
build recipe also uses /tmp as the POSIX fallback and renames two reserved
macro identifiers which conflict with current Apple SDK headers.
