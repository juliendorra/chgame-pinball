# Pinball Studio validation

## Current three-level shake

The editor badge and native LCD now show levels 1–3. Level 3 is DANGER
and retains the previous level-5 force, wobble and rumble; the fourth rapid
press tilts. The 420 ms window and held-key edge behavior are preserved.
The shared native/WASM build and the 171,509-check shake suite pass. Older
versioned results below describe the five-level system at the time.


Version 1.4.2 restores a large central crest above every board, with the same
felt behind its transparent pixels and shaded supports joining the roof.
The native overview includes 24 extra header rows. A separate header canvas
keeps existing element coordinates and selection overlays aligned. Chrome
checks confirm the pirate and shuttle crests, theme switching, sprite drop
at (86,124), undo and restored draft contents. All nine large crests and
smaller rail emblems match the physical console pixel for pixel. The 11
editor/FAT tests pass with the extended overview. `out/editor/large-headers.png`
records the browser check; `docs/borders.png` shows all nine themes.

The 1.4.1 update was also checked in desktop Chrome: both enlarged pirate
emblems appear in the live full-board view, and the gate is a solid hinged
arm with a direction indicator. All nine pairs of emblem regions match
the actual console framebuffer pixel for pixel. The 14 model tests and
11 native/USB/FAT tests pass again. See
[1.4.1 device checks](../docs/device-validation.md) for rumble and deployment.

Tested on 2026-10-23 against Pinball 1.4.0, including the connected CHGame Rev0.

## Native engine and data

- 14 JavaScript tests pass: all nine originals encode byte-for-byte identically
  to the shipped PBTs; checksum/bounds checks, clone identities, empty boards,
  geometry picking and Flipkit-compatible keyboard mappings are covered.
- 11 Python tests pass: real-engine live updates preserve ball, score and time;
  corrupt, incomplete, oversized and out-of-order uploads are rejected;
  empty boards, all themes, full-height rendering and simultaneous controls work.
  New kickbacks start armed and theme changes preserve ongoing scoop captures.
- The same suite tests FAT16/FAT32, MBR/superfloppy layouts, missing folders,
  directory growth, file resizing, 20 clones and unrelated-file preservation.
  Injected data-write and directory-commit failures retain the previous board.
- The existing native UBSan/bounds regression suite passes, including 180
  photographed gutter-pocket cases, full ramp rides and 72 camera views checked
  against an independent pixel reference.

The browser receives the actual C++ engine's packed frames and full-height
rendering. Rendering the overview does not advance physics. This is a local
server implementation; no standalone WebAssembly build is claimed.
All nine emblem sprite payloads are present in the exact final release image;
the final native engine also renders both pirate emblems in its upper corners.

## Browser interaction

Tested the editor in the in-app browser and desktop Chrome: clone, add bumper,
drag, precise coordinate edits, remove/undo, theme switch, keyboard launch,
fit/zoom and draft persistence. The LCD preview remains visible while scrolling
the inspector. Invalid drafts retain the last valid playable board.
Palette drags use transparent, zoom-matched part artwork. Browser checks cover
single-element bumper and rail drops, a ramp at exact coordinates after zooming,
paired-flipper placement, outside-board cancellation, and ordinary click-to-add
without duplicate drops.

In Chrome, connected directly through Web Serial, retrieved the handheld's board
library, cloned Buccaneer Bay, added a bumper and verified the 348-byte RAM
upload. **Save to SD** released the browser port to the local bridge and saved
`PINBALL/PIRAT001.PBT`, with readback confirmation in the UI. The browser was
then disconnected so firmware deployment could use the port.

## Physical device and SD

The diagnostic build passed 76 gameplay checks across all nine original SD
boards. Three five-second scenarios measured 60.18–60.21 fps with zero late
intervals and 1,236 bytes peak stack out of 2,048. See
[device validation](../docs/device-validation.md) for the timing table and
gameplay coverage. Physical switch feel and enjoyment still need human play.

The final release passed 12 USB/SD checks: library retrieval, exact RAM readback,
preserved paused ball/score/lives/time, corrupt-upload rejection, both flippers,
key release, heartbeat expiry, launch, approximately 60 Hz, a 72-element fixture,
and SD create/resize/rescan/readback with existing boards unchanged. The final
one-second release sample measured 60.26 fps. `EDITLAB.PBT` is the test fixture.

The final 49,076-byte release and matching 61,470-byte `GAMES/MIDNIGHT.CHG` were
installed. After unmounting and remounting, the cart CRC, firmware and all nine
original PBTs matched exactly. All 44 pre-existing game/menu files and the two
custom boards remained intact. The card was safely ejected and the same release
was flashed back to the device. Selecting the cart physically in the bootloader
menu remains a human check; the bootloader itself was not changed.

Machine-readable reports and raw logs are in the ignored `Pinball/out/` folder:
`editor-model-tests.log`, `editor-tests.log`, `verify-editor.log`,
`device/v1.4/hardware-tests.json`, `device/v1.4/editor-hardware.json`,
`device/sd-installed.json` and `device/release-manifest.json`.

## 1.4.3 progressive shake

Native physics/renderer checks cover levels 1–5, the 417 ms accepted / 433 ms
expired boundary at 60 Hz, held/repeated keys, simultaneous controls,
opposing ball inertia with unchanged gravity, captured ramp/saucer immunity,
sixth-tap tilt, disabled flippers/scoring/saves, drain reset, last-life cabinet settling and pause.
An independent full-board render verifies 110,592 shifted playfield pixels
across eight positive/negative displacements. All 90 packed score sprites
match their editable source pixels. The complete shake suite has 116,302
checks, with UBSan and bounds checks enabled.

Browser testing uses native A presses and observes level 5 followed by tilt=3
through the canvas telemetry. The faithful LCD shows the steady red TILT
warning and five-bar gauge. The header and selection layer move with the full
board; picking uses its translated DOM bounds. `out/editor/progressive-shake.jpg`
records the final UI. Local websocket and USB streams preserve fast tap edges,
suppress held-key escalation, remain bounded and release after input expiry.
Their tests cover queued taps, heartbeat behavior, disconnect and overflow.

## 1.4.4 emblem board picker

The browser picker paints the same editable 12×8 crests used by the console,
with integer 4× pixels, theme accents, board felt and derived shadow colors.
Clones use their chosen theme. All 18 JavaScript tests and 15 Python editor/FAT
tests pass. Browser checks cover pointer selection in Safari, arrow/Home/End
navigation, Enter activation, Escape dismissal and readable narrow-sidebar
layout. The selected board receives gameplay focus after activation.
`out/editor/board-picker.jpg` records all nine theme emblems and a saved clone.

`tools/verify_library.py` passes 15,372 native menu checks, including every
crest pixel and resuming the suspended board. The full UBSan/bounds gameplay
suite also passes. `tools/verify_library_device.py` passes 15,373 checks on
the installed 1.4.4 console release across the original SD boards.

## 1.4.5 stronger shake feedback

A first tap produces a three-pixel peak rather than the earlier one-pixel
jolt; maximum displacement is six horizontal pixels and one vertical pixel.
The 171,520 native shake/tilt/render checks pass under UBSan/bounds, covering
13 pixel-exact translations, pulse colors, the larger meter, both directions,
pause, overview capture/restore and expiry. Physics and tilt timing are unchanged.
All 18 JavaScript and 15 Python tests pass; the full native gameplay suite
passes across all nine boards.

Native A/Right browser input reaches DANGER 5/5 and sixth-tap tilt. The badge
uses the actual shove direction, and the cabinet rim brightens on the native
impact frames. Pausing freezes the whole effect. The screenshot is
`out/editor/shake-feedback-danger.jpg`; the native animation is
`out/shake-feedback/shake-feedback.gif`.
