# Automatic build and install checks

`python3 pinball.py build` and `python3 pinball.py web` publish output only
after the host checks pass. Console builds also enforce flash, static RAM and
the reserved stack limit. `python3 pinball.py upload` builds the paired firmware
and web bundle, installs the firmware, then checks real console timing.

| Gate | Workload | Problems caught |
| --- | --- | --- |
| Generated assets | Source sprites, 18 flipper poses/collision masks, tables | Stale generated artwork, masks or built-in geometry. |
| Native/WASM parity | All nine boards, deterministic inputs, live edits, full-board/LCD pixels | Browser/console-model configuration differences, divergent simulation, incorrect layers, cup visibility, popup and game-over rendering. |
| Sanitized simulation | Real solver, ramp rides, tilt, rubber flex, 180 gutter cases, SD images | Undefined arithmetic, invalid access, stuck drains, ramp follow ending early, launcher re-entry and broken recovery. |
| Visible flipper contact | Both sides, nine poses and eleven sizes; near misses, overlaps and a fast swept strike | A collision outline that disagrees with the actual opaque sprite pixels, including contacts with neighboring stair-step corners. |
| Seeded players with rendering | Nine boards × no-flipper/random/reactive policies × two seeds, 30 seconds maximum, every run repeated | Nondeterministic outcomes or spin traces, crashes during actual play, costly drawing during the states players reach. |
| Drawing work budgets | Every rendered play frame, complete layouts at 1×/1.5×, 1/2/3/4/6/8/12 long ramps across viewport positions | Excessive direct line/pixel calls, long-line overdraw, excessive spans or sprite calls, including the historical solid-ramp slowdown. Crowded stress fixtures use explicit per-ramp work ceilings; shipped layouts retain the existing ceilings. |
| Editor and browser SD | Keyboard edges, live edits, codecs, FAT16/FAT32 failure/readback tests | Lost controls, disruptive editing, damaged or incorrect card exports. |
| Physical-console timing after upload | Original, no-ramp, one-ramp, two-ramp and empty RAM-only fixtures; three seconds each | Render or physics rate below 57 Hz against the 60 Hz target, including costs specific to flash access and the real display. |

The post-build play/work report is bundled as `validation/regressions.json`.
Individual plays include score, trace, stalls, ball searches and scoring
droughts. Those metrics help compare gameplay; they are not a human fun score.
Only invariants and drawing ceilings fail this gate. A gameplay change can
legitimately change scores, so historical study baselines are not silently
updated or treated as universal expected scores.

The drawing budget counts calls issued directly by the actual C++ renderer.
It is a deterministic early warning, not an instruction-level emulator or a
complete measurement of drawing cost. Current plays/sweeps peak at 14 line
calls per frame; the old slow renderer reaches 126 and fails the 64-call
ceiling. Firmware code inside a shared primitive can become slower without
changing these counts: the on-device timing gate is still necessary. Host
milliseconds are never converted into claimed console FPS.

The physical check preserves the board data and SD files, but restarts the
current game when restoring its table. A missing or busy device fails install
validation; a successful build alone does not mark hardware timing as passed.
Reports are written to `Pinball/out/install-validation/` and identify the
paired source and firmware hashes. Use the following to test an already
running game without installing anything:

```sh
python3 Pinball/tools/verify_device_fps.py --port /dev/cu.usbmodem101 --out Pinball/out/device/fps.json
```

The newer board-specific benchmark isolates ramp count and fixed-camera
rendering, then runs seeded launches. Its optional active FPS gate applies to
the original user layouts; deliberately crowded stress fixtures are reported
separately. Paused samples include a full LCD transfer and are not gameplay
FPS. SD files are untouched.

```sh
python3 Pinball/tools/benchmark_ramp_device.py --port /dev/cu.usbmodem101 \
  --stress-ramps 4 6 8 12 --min-active-hz 57 \
  --out Pinball/out/device/board-ramps.json
```

For a renderer optimization that should preserve the image, retain its previous
`Render.cpp` and compare complete packed LCD bytes:

```sh
python3 Pinball/tools/compare_renderer.py --reference /path/to/previous/Render.cpp
```

The browser SD controller/writer also has a real-device diagnostic. It creates
only its absent `PBAUTOT.PBT/PBK` fixtures, verifies automatic saving and revert
using production JavaScript, then removes those fixtures. It checks existing
boards/checkpoints and the active RAM board remain unchanged. Do not run it
while another process owns the console or writes the card.

```sh
node Pinball/tools/verify_device_storage.mjs /path/to/python /dev/cu.usbmodem101 \
  Pinball/out/device/storage.json
```

After an explicit CHSave migration, the normal release can also be checked
without adding a diagnostic command to the game. This test stages zero-score
game-over screens and compares their BEST digits with the report's expected
values, then verifies the journal is byte-identical and restores the RAM
board. It restarts the current game; it does not submit a new high score.

```sh
python3 Pinball/tools/verify_device_score_load.py --port /dev/cu.usbmodem101 \
  --migration-report /path/to/device-migration.json \
  --out Pinball/out/device/score-load.json
```

To run only the post-build play/work suite:

```sh
python3 Pinball/tools/verify_regressions.py
```

To reproduce a historical renderer failure, supply its saved source with
`--renderer PATH --out PATH`. This validates that a known bad implementation
is rejected without replacing the active game code or updating a baseline.
