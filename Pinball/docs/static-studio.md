# Static Studio and shared game builds

Studio runs the actual `Pinball.ino`, every game translation unit, and the
repository's CHGame/CHGfx drawing, palette and input code as WebAssembly. The
only replacement is hardware I/O: browser time, direct framebuffer access and
no physical LCD/SD transport. JavaScript owns editing and UI; there is no
JavaScript pinball physics and no emulated serial connection to the engine.

The editor has one full-board view, including the themed roof decoration.
It never needs to scroll after the ball or switch between editing and playing.

## Build

Install the pinned Emscripten SDK once (or set `EMXX` to its `em++`):

```sh
git clone https://github.com/emscripten-core/emsdk.git .toolchains/pinball-emsdk
python3 .toolchains/pinball-emsdk/emsdk.py install 4.0.15
python3 .toolchains/pinball-emsdk/emsdk.py activate 4.0.15
```

Python 3.10+, Node.js and a native C++ compiler are required for validation.
The ordinary CHGame setup is also required to build firmware.

```sh
python3 pinball.py build       # firmware + WASM + parity tests, one source snapshot
python3 pinball.py web         # browser bundle + checks, no firmware/hardware operation
python3 pinball.py web-check   # fail if sources or any deployed artifact are stale
python3 pinball.py editor --open
```

`editor --no-build` still checks freshness before serving. `--port 8766` chooses
another local port. The server only serves static files; the game executes
inside the browser. `Pinball/editor/server.py` is retained for native diagnostic
sessions/tests, rather than the production editor launch path.

Upload the **contents** of `Pinball/build/studio/` to any static HTTPS host.
URLs are relative, so deployment in a subdirectory works. Serve `.wasm` as
`application/wasm`. No Python, WebSocket server, USB relay, npm runtime,
cross-origin isolation or hardware emulator is needed on the host. Localhost
HTTP also works for development; a plain `file://` URL does not.

## Build guarantees and limits

The build discovers the same game translation units as Arduino, compiles
shared sources for WASM and native C++, and rejects stale generated sprites,
flipper collision masks or built-in tables. Emscripten is pinned to 4.0.15.
The shared library sources come from the same vendored directories used by
the firmware build. `pinball.py build` succeeds only when both targets build
and validation passes.

Every build also runs the sanitized simulation regressions and
`verify_regressions.py`: 54 seeded games (nine boards, three synthetic players,
two seeds), each repeated exactly with a render after every physics tick.
Full-layout sweeps at 1×/1.5× and one/two long-ramp fixtures cover areas the
players might not reach. Drawing-call ceilings reject excessive line/pixel
work. The old 43.5 Hz ramp renderer fails this gate; these counters do not
estimate console FPS. `validation/regressions.json` is included in the verified
static build. See [regression testing](regression-testing.md) for coverage and limits.

Firmware compiles from a temporary source-only snapshot, avoiding Arduino's
scan of generated captures and nested test builds. Successful combined builds
publish the matching firmware artifacts to `Pinball/build/release/` (or `debug/`).
`pinball.py upload` installs that paired build, then runs the physical-console
render/physics gate at a minimum 57 Hz, with original, empty and one/two-ramp
fixtures. The result is recorded in `Pinball/out/install-validation/installed.json`.
Hardware performance is only verified once that on-device test passes.

Deterministic replays cover all nine boards, launches, flippers, ramp rides,
geometry moves/deletions/undo, theme edits, pause, restart and invalid data.
They compare the complete exported state, packed full-board pixels and PBT
readback byte for byte between native and WASM. Browser FAT saves are tested
against an independent FAT reader on FAT16 and FAT32 images, including write
failures and preservation of unrelated files. Input queue tests preserve
sub-frame press/release edges during editing.

`build.json` records source hashes, compiler version and artifact SHA-256s;
combined builds also record the firmware's hash and size. Output is published
only after checks pass. Engine filenames include the source hash to avoid
mixing cached WASM with a different loader. `web-check --firmware PATH` also
checks the firmware pairing. Upload/export commands validate WASM first;
`export --no-build` requires a current paired build. Direct Arduino/shared CLI
commands bypass this Pinball-specific gate: use `pinball.py` for releases.

The standard physics defaults live in `Spin.h` and `Scatter.h`: light contact
spin (grip 16/256), spin memory enabled, and all three synthetic scatter strengths
zero. `tools/game.py` reads those defaults into the explicit flags consumed by
firmware, WASM and native diagnostic builds, keeping direct C++ builds and build
manifests consistent. Comparison benchmarks explicitly select their fixed
historical no-spin/scatter reference rather than inheriting shipping defaults.

The WASM API exports its compiled physics constants and the ball's spin state.
The parity replay checks those constants against `assets/physics.json` and
against native C++, confirms an oblique hit generates spin, and confirms that
different seeds produce identical trajectories with synthetic scatter disabled.
`build.json` records the active physics configuration. To also check it against
an installed-console build report:

```sh
python3 Pinball/tools/build_studio.py --check --console-build Pinball/out/device/final-installed.json
```

A mismatched console profile is rejected before building or accepting the web
bundle; this does not reflash or change the console.

These checks prevent accidental source drift and catch differences exercised
by the replays. They do not claim cycle-exact peripheral emulation or replace
CHGame testing of LCD timing, flash, USB and PC0 rumble. The existing RISC-V
emulator can separately validate the shipped firmware; it is not in the
editor's interaction path. Browser audio is currently silent, as in the
native simulator.

## Modeless edit transaction

Pointer selection, drag sprites, handles, inspector fields, delete/duplicate,
clone and undo/redo stay in JavaScript. Valid board snapshots are queued and
the newest snapshot is applied atomically before the next physics tick.
The C++ `live::apply()` implementation is shared by the direct WASM API and
the handheld's USB protocol.

Changing geometry/theme on the same board keeps ball positions/velocities,
score, lives and game time. Unchanged elements retain state/cooldowns, even
when deletion changes their indexes. Changed or deleted occupied ramps release
the ball; unchanged ramps keep their rider. Editing board identity or height
starts a new game, matching the handheld. Undo restores geometry, not past
ball motion. Invalid drafts remain editable while the last valid board plays.

Keyboard input continues through pointer drags. Inputs/selects reserve keys
for typing. Focus loss releases controls. The fixed 60 Hz clock retains quick
key transitions and discards accumulated time after a background-tab delay.

## Physical CHGame

**Connect CHGame** uses desktop Chrome/Edge Web Serial directly, on HTTPS or
localhost. Browser permission is required once. Uploads and board retrieval
use the existing release protocol. **Save to SD** now uses browser-side FAT
code on that same connection, with copy-on-write file allocation and readback
before publishing the directory entry. The handheld is paused during the SD
transaction and its previous pause state is restored afterward. No drive
mount, serial emulation, firmware reflash or Python bridge is involved.

The SD writer supports mirrored FAT16/FAT32 volumes and PINBALL folder
creation/growth. An uncertain directory-write failure can leave an allocated
orphan rather than free a potentially published file, matching the existing
Python writer's conservative behavior. Clone a board before overwriting an
original if you want to keep both.
