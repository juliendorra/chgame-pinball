# CHGame device validation

## 1.4.15 stable help for real trapped balls

The 1.4.13 detector rejected the actual upper-right flipper/guide trap because
its subpixel rebound corrections repeatedly reset the stationary timer. A
recorded console trace spanned only 0.58 pixels vertically, despite individual
steps exceeding the old 0.25-pixel cutoff. Detection now uses a fixed two-pixel
position tolerance over time, so jitter cannot cancel progress and slow rolling
still resets the timer.

Normal play now displays a persistent informational warning. The old automatic
rescue kick is removed: the warning cannot move a ball, drain it, start a turn
or switch screens. Tilt retains retirement of a trapped, forfeited ball. User
shakes or escape from the resting area clear the warning.

The real trap is reproduced in the native gate with released, held and repeatedly
pressed left-flipper controls. Each run checks 990 frames, including 15 seconds
with uninterrupted help, no life loss and no automatic kick. The old detector
fails this reproduction. The complete gate passes 9,282 stuck-help checks,
native/WASM parity, all nine tables, collision tests and repeated synthetic plays.

On the console, one continuous observation of the original board kept the
warning visible for 13.37 seconds, with no resets or board changes
during the observation. Read-only snapshots verified the filled control icon,
three lives, an active ball, no pause and only subpixel position changes.
Render and physics rates measured 59.29 Hz in the quiet timing interval.

The 50,748-byte image and matching `GAMES/MYGAMESP/MIDNIGHT.CHG` cart are installed.
Uncached cart readback passes; all 95 other files/allocation chains, board/menu
hashes and the full SD score journal remain unchanged. The original RAM board
remains loaded. Detailed evidence: `out/stuck-jitter/install/final-installed.json`.

## 1.4.13 ramp entry and stationary-ball help

Installed and verified the console firmware and matching SD bootloader cart
at `GAMES/MYGAMESP/MIDNIGHT.CHG`. The 50,684-byte image fits the Rev0 cartridge
region; PBT1 storage now has explicit word alignment while retaining its
96-byte header, 12-byte objects and exact wire offsets.

The short-funnel entrance uses the selected floating arrow at the mouth,
shifted one native pixel left. A ramp rider passes underneath that marker;
the ramp floor captures its leading edge and carries it continuously to the
configured exit. The actual game matches all 150 frames of the reviewed
arrow proposal.

Stationary balls show a large **BALL STUCK! / ▶ OR A SHAKE** panel after
1.5 seconds. A physical LCD capture verifies all 60 pixels of the filled
triangle. Both console shake controls free the stationary test ball. The
active help panel measured 59.48 render and physics frames per second; all
five normal/ramp timing cases passed the 57 Hz gate at approximately 60 Hz.
The native suite also covers slow rolling, held flippers, multiball, pause,
overview preservation and the existing tilted-ball retirement.

The SD cart was read back uncached and its game binary matched the installed
image. All 95 other file entries and allocation chains, 26 board/menu hashes,
and the complete `MPIN.SAV` journal were preserved. The original RAM table was
restored after testing.

Firmware SHA-256: `060b9479749e39ac77c46b88a44b57f4ddb8463dd09179afc0dfa6085990b00c`.
SD cart SHA-256: `5a3072c0cc3b476b3d5989378c4ca4b9e1e13f485f95f4fef9b20e3d975999e6`.
Detailed local evidence: `out/stuck-help/install/final-installed.json`.

## 1.4.12 mirrored rubber joints and three-level shake

The left bumper directly mirrors the right bumper's body and moving rubber,
including face shading. Board-space shadows still fall down/right. Its
collision path uses the same mirrored geometry: 1,799 curve samples and
5,551 hardware pixels across all 19 flex poses pass independent mirror checks.
The [comparison animation](rubber-joint-comparison.gif) shows the original
left, its mirrored replacement and a mirrored right reference.

Shake has three levels corresponding to the previous strengths 1, 3 and 5.
A fourth rapid press tilts. Level 3 exactly matches the old maximum across
43 samples of ball motion, wobble and PWM rumble. All 171,509 native shake,
tilt and score-render checks pass. The release passed 18 physical checks;
active shake measured 59.13 fps, and PC0/TIM2 CH4 returned to zero.
The full physical render/physics timing gate also passed, including two ramps.

## 1.4.5 visible shake impacts

The first tap now produces a three-pixel visual jolt, rising to six horizontal
pixels and one vertical pixel at level 5. Two short edge pulses and directional
chevrons mark contact. The larger footer meter turns orange at level 4 and red
at level 5; the tilt warning persists until drain. Ball inertia, gravity, the
420 ms escalation window and sixth-tap tilt are unchanged. Studio adds the
same timed rim highlight and a direction/strength badge.

All 41 physical-device checks pass, including the actual LCD edge pixels,
both directions, the large meter, pause, tilt, expiry and PC0 PWM shutoff.
Active shake measured 58.97 fps. All 171,520 native shake/render checks pass
under UBSan/bounds, covering 13 exact translations and all 90 score glyphs.
The full native gameplay suite, 18 JavaScript tests and 15 Python tests pass.

Firmware is 50,072 bytes, static RAM is 17,804 bytes, and both flash
save pages remain available. CRC32 is `0x5BFC8D6A`. The exact matching
64,046-byte cart at `GAMES/MYGAMESP/MIDNIGHT.CHG` passed uncached readback. All
54 current surrounding game/board files, all nine original tables and both
custom boards remain intact. The console is left on the SD Pirate table with
a fresh ball. Reports are under `out/device/v1.4.5/`; the browser proof is
`out/editor/shake-feedback-danger.jpg` and the native animation is
`out/shake-feedback/shake-feedback.gif`.

## 1.4.4 board selection emblems

The CHGame library now places a 48×32 theme crest beside the layout preview,
using the selected board’s theme and felt palette even when another game is
suspended. The same source artwork appears on every Studio picker row.

All nine original themes pass 15,372 native and 15,373 actual-device menu checks.
These check every scaled crest pixel, selection navigation and resuming the
suspended game. The full native UBSan/bounds gameplay suite passes, along with
18 JavaScript and 15 Python editor/FAT tests.

The installed 1.4.4 release is 49,632 bytes with 17,804 bytes static RAM
and two flash save pages retained. CRC32 is `0x6BDCE3D4`. Its matching
63,534-byte SD cart at `GAMES/MYGAMESP/MIDNIGHT.CHG` passed uncached readback. All
77 surrounding game/board assets, nine original boards and both custom boards
remain unchanged. The console is left on the SD Pirate board with a fresh ball.

## 1.4.3 progressive shake and tilt

A shoves the cabinet left and Right shoves it right during play. Before
launch, A still operates the plunger; Down always launches. Fresh taps within
420 ms build levels 1–5, restarting Flipkit's damped 700 ms wobble. Levels
4–5 warn DANGER; a sixth rapid tap tilts. Held keys and USB heartbeats count
once. Tilt disables scoring, flippers and powered saves until all balls drain.
Captured ramp/saucer balls keep following their mechanism. Every drain settles
the cabinet, including the final life. Shake and tilt drive the existing PC0 PWM
rumble controller. The score and warning strip stay fixed while the board moves.

The release passes 100 physical-device checks: 20 cover input edges, both
impulse directions, all strength levels, tilt, drain reset, PWM and timing;
80 cover the retained large headers/corner emblems on all nine themes and
rumble hardware. Active wobble measured 59.11 fps in the short sampling window
(approximately 60 Hz); the static full-header pause overlay measured 56.55 fps.
The paused-overlay check is reported separately with a 55 fps floor; it did
not meet the previous 57 fps benchmark. Gameplay remains checked near 60 Hz.

All native UBSan/bounds regressions pass, including 116,302 shake/tilt and
pixel checks, 90 losslessly packed score glyphs, eight exact framebuffer
translations, all nine full-length ramps and photographed drain regressions.
The 3,691 header and 256 gate checks pass. Fifteen editor/FAT tests and sixteen
JavaScript control/USB-stream tests pass. Native browser input confirms both
A and Right shaking, level 5 followed by tilt=3, and the persistent red warning
on Buccaneer Bay. Fast press/release edges are retained in both websocket and
USB streams. The pause button follows the actual native paused state.

The final firmware is 49,512 bytes with 17,804 bytes of static RAM and a
separate 2,048-byte stack. Both save pages remain available. CRC32 is
`0xA8CB75D7`. The ordinary-flash score decoder caches one glyph; the trial RAM
decoder was removed after unreliable startup during target validation.

The matching 63,534-byte cart is installed at
`GAMES/MYGAMESP/MIDNIGHT.CHG`, preserving the existing personal-games menu.
It was replaced through the live USB sector API using a new FAT chain,
uncached verification before publication and another exact readback afterward.
All 77 surrounding game/board assets match their current pre-update hashes,
including all nine original boards and both custom boards. FAT link updates
are coalesced per sector. The bootloader was not changed. CHGame is left on
the SD Buccaneer Bay board with a fresh ball in the shooter lane, keys released
and tilt cleared. Reports are in `out/device/v1.4.3/`, `out/device/sd-installed.json`
and `out/device/final-installed.json`. The browser proof is
`out/editor/progressive-shake.jpg`.

## 1.4.2 restored large top decorations

The large 36×24 themed crests are restored above the roof, on shaded
supports that join its rails. The smaller corner and side ornaments remain.
The felt background continues through the header. The live camera reaches
world y=-24, and Studio renders those extra rows above its editable playfield.

All 80 release-device checks pass: every large crest and retained corner
emblem matches the native Studio renderer pixel for pixel, and PC0 PWM,
launch/bumper strength, expiry and pause shutoff still work. The active
full-header view measured 60.11 fps; the header plus pause overlay measured
57.13 fps. The nine SD originals and both custom boards are available.
The 3,691 native header checks cover all nine distinct designs, every crest
pixel, shared felt, camera reveal, Studio overview and invalid camera bounds.
The full native regression suite, 256 gate checks, rumble tests and 11 editor/FAT
tests pass; Chrome checks confirm theme switching, precise placement at
(86,124), undo and alignment of the selection overlay below the header.

The installed release is 50,192 bytes, static RAM remains 17,504 bytes, and
both save pages are preserved. Firmware CRC32 is `0x25707DD4`. Its matching
63,006-byte SD cart was read back after remounting; all 44 earlier game/menu
assets, nine original board files and both custom boards were preserved.
The card was safely unmounted before the console was returned to Pinball.
The existing 4,460-point run was saved through the ordinary table restart
before flashing. Raw reports are under `out/device/v1.4.2/` and `out/headers/`.

## 1.4.1 rumble, gates and emblems

The 50,344-byte release was installed and tested on 2026-10-23. It uses
17,504 bytes of static RAM and retains both flash save pages. CRC32 is
`0x45E7213C`. The matching SD cart is 63,006 bytes; remounted readback confirms
the exact firmware and all nine original PBTs, with all 44 existing game/menu
files and both custom boards preserved.

The release passed 62 target checks, including actual PC0 alternate-function
configuration, TIM2 CH4 full remap, launch PWM duty 588/1000, bumper duty
823/1000, timer expiry to zero duty and immediate pause shutoff. It measured
59.91 fps over two seconds. These checks inspect the actual hardware registers;
motor strength and feel have not been physically measured.

Both larger corner emblems on every theme match the native Studio renderer
pixel for pixel. The actual LCD frames are in `out/device/v1.4.1/`. A desktop
Chrome check also confirms both pirate emblems in the live full-board editor.
The gate passed 256 native checks for visible-arm collision, motion, both
directions, reversed endpoints, bank locking and pause. The full native
UBSan/bounds suite, 14 model tests, 11 editor/FAT tests and rumble timing,
priority, shutoff and clock-wrap checks pass.

## Earlier 1.4.0 measurements

Validated the 1.4.0 editor build on the connected CHGame Rev0 on 2026-10-23.
The diagnostic build uses the real SD card, solver, display driver and flash
save code. Inputs were injected through USB; physical switch feel and enjoyment
require a human playtest. Native UBSan/bounds checks also pass.

| Scenario | Measured fps | Average render | Maximum frame work | Late intervals / frames | Peak stack |
| --- | ---: | ---: | ---: | ---: | ---: |
| pirate normal play | 60.20 | 6.68 ms | 12.23 ms | 0 / 302 | 1236 / 2048 B |
| ramp follow and score popup | 60.21 | 6.44 ms | 12.28 ms | 0 / 302 | 1236 / 2048 B |
| pirate multiball and zoom | 60.18 | 7.21 ms | 11.52 ms | 0 / 302 | 1236 / 2048 B |

All three five-second timing runs passed: at least 57 fps, at most two
intervals over 17.5 ms, and stack below 1900 bytes. These final runs recorded
zero late intervals. Transition intervals are included. Timing instrumentation
is absent from the release.

The 76 device checks loaded every board from the physical SD, verified Left/B
flippers, equal fixed-power A/Down launch, one-way shooter exclusion, full-length
ramp follow and exact exit, round/lucky score celebrations and expiry, scrolling,
pause, three-bank multiball, special zoom and return, SD rescan with suspended
state, high-score persistence, retry, and fault status. Both rubber bands flex
on actual contacts and settle; rounded flippers strike on both sides.
Twelve physical-device gutter cases check both sides, released/held bats and
two board heights. The native suite checks 180 photographed-pocket regressions
across all nine boards, every ramp's full ride, all score styles and board-colored
ball shadows. The independent flipper probe covers 4,768 contacts across both
sides, all nine poses and all eleven permitted lengths; maximum visible contact
error is 0.4693 pixels (`flipper-collision.json`).

Rounded walls use a shaded five-pixel body and a rubber crown, with shared
upper-left lighting. Ball, flipper and raised-element shadow silhouettes are
baked into span sprites without moving their original anchors. Their tint is
derived from each board's felt on load, including custom SD boards.
Themed top caps follow the sloping roof rails; the corner emblems have transparent
backgrounds that expose that same felt. Side ornaments include the outer rail
face and stay clear of the ball paths and plunger. `borders.png` shows actual
upper and lower game views for all nine skins.

Rendering uses generated flipper poses, joined rounded beam spans, whole-run
culling, packed-pixel zoom sampling with repeated-row reuse, and partial LCD
transfers when the score/message bars are unchanged. Physics overlaps the last
LCD transfer; framebuffer rendering waits for completion. UI, SD, palette and
save transitions wait before shared display work. An independent pixel reference
validates 72 camera views across all animation scales, including the upper
corners, shadows, fixed HUD and palette.

The final 1.4.0 release image is 49,076 bytes; static RAM is
17,488 bytes out of 18,416, with a separate 2,048-byte stack. It keeps
both flash save pages. Firmware CRC32 is `0x549448DE`. The package
produces a 61,470-byte `GAMES/MIDNIGHT.CHG` and nine SD board files.

The SD cart and all nine boards were copied, unmounted, remounted and read back.
The cart CRC and firmware match the final release exactly; all 44 pre-existing
games and menu assets match their previous SHA-256 hashes. The two editor-created custom boards, `EDITLAB.PBT` and `PIRAT001.PBT`,
were also preserved. The card was safely ejected after verification. The same release firmware is installed directly
on the device.

The ordinary release adds the Pinball Studio USB protocol. Twelve release-device
checks passed, including atomic RAM upload/readback, preserved ball/score/time,
keyboard injection and heartbeat release, all-library retrieval, and actual SD
create/resize/rescan/readback. The final release measured 60.26 fps over a
one-second sample. The diagnostic timing build omits that protocol to retain
the larger probes within flash. See [editor validation](../editor/validation.md)
for browser and FAT tests.

Automated tests exercise direct firmware upload and SD table loading; physical
selection of the cart in the bootloader menu remains a human check. Hold START
for three seconds to open that menu and choose MIDNIGHT PINBALL.

## 1.4.6: raised ramp rail layering

Ramp rails now render after balls and all flipper pairs, before camera zoom and
shake. The shared renderer uses this order on CHGame and in the WASM editor.
Pixel regression fixtures cover a ball and an upper flipper crossing the ramp.
Native/WASM parity passed on nine boards with 239 complete state/pixel snapshots.

The release was flashed on CHGame and accepted by the bootloader's CRC check
(`0xD338B5D5`). The installed game identifies itself as 1.4.6. Seven physical
checks passed: 134 visible rail pixels remained in front of genuinely overlapping
ball and flipper sprites, and both flipper controls operated correctly. Test
fixtures were applied only to RAM; the Pirate table was restored afterward.
Evidence: `out/device/v1.4.6/layering-hardware.json`.

The release image is 50,148 bytes, retaining both flash save pages; static RAM
is 17,804 bytes, with the separate 2,048-byte stack.

The matching 1.4.6 SD bootloader cart was written through the live USB sector
API and verified by uncached readback. All 71 baseline directory records and
allocation chains remained unchanged; 24 board/menu hashes also matched. The
Pirate SD table was loaded, unpaused, with a fresh ball and released controls.
Evidence: `out/device/v1.4.6/sd-installed.json`.

## 1.4.7: ramp riders use the elevated ball layer

Balls with an active ramp ride now draw above ramp rails. Grounded balls and
flippers remain underneath. Ending a ride or deleting its ramp returns the
ball to the ground layer. Each active ball is drawn once, so multiball can
show balls at different heights together. The rule is shared with WASM.

Native/WASM parity passed across nine boards, 2,411 ticks, 86 live edits and
242 full state/pixel snapshots. A ramp rider exposes 45 sprite pixels that
are correctly occluded when the same ball position is grounded. The previous
ground-ball and flipper occlusion regressions also pass.

The 50,188-byte release retains both save pages. Installed firmware CRC32:
`0x5A121881`. Evidence: `out/device/v1.4.7/`.

On CHGame, the 134-pixel ground-layer occlusion fixture and both flipper
controls passed again. A physical launch captured a ramp and followed its
path; its LCD frame is in `out/device/v1.4.7/riding-ball-lcd.png`. The matching
SD cart passed uncached readback, preserving 71 baseline directory records
and allocation chains plus 24 board/menu hashes. Pirate is restored,
unpaused, with a fresh ball and released controls.
