# Midnight Pinball Studio

A mode-less board editor for the CHGame Pinball game, following Flipkit's
edit-and-play workflow. The ball keeps moving while parts are selected, added,
removed, dragged or adjusted. There is no edit/play switch.

The editor uses one full-board view with live play and pointer editing.
**Fit** includes the complete board and its top crest. When manually zoomed
past the visible area, scrolling follows the actual C++ console camera crop,
adapted to the measured HTML viewport. Resizing updates the available area.
Dragging parts, editing properties, pausing or temporarily scrolling by hand
takes priority over automatic following.

Connection, board retrieval and live-edit controls are in the top toolbar.
The strip below it holds play mode, score, lane progress and play controls.
Board selection, SD saving and parts are on the left; element and board
properties are on the right. The center remains available for the board.

Selected ramps show a green **ENTRY** handle at the front lip and a violet
**EXIT** handle. Drag the track to move the entire ramp, or a handle to move
that end. The active drag target is highlighted and named in the inspector.
Lane indicators remain steady; collected lanes change appearance.

Start from the repository root:

```sh
python3 pinball.py editor --open
```

Or double-click `Start Pinball Studio.command` in Finder. The app runs at
<http://127.0.0.1:8765>. Launch builds the shared C++ game as WASM and validates
native/WASM parity; `--no-build` checks and reuses the current bundle.
`--port 8766` changes the port. See [static builds](../docs/static-studio.md)
for the pinned compiler setup and deployment to a static host.

## Build and play together

- Choose one of nine original boards or a board saved in this browser. Each
  picker row shows its theme emblem on its own felt color. The selected board
  keeps its emblem visible. Arrow keys, Home/End and Enter navigate the picker;
  Escape closes it. These keys do not operate the game while the picker has focus.
- Click a part in the bin to add it near the visible board center, or drag it
  onto the board. While dragging, its transparent sprite follows at the board's
  zoom level, with an anchor marker and exact drop coordinates. Rails, ramps
  and flipper pairs preview their footprint too. Drop outside the board or press
  Escape to cancel. All thirteen game elements are available, including flexing rubber slingshots.
- Select and drag existing parts. Rails, gates and ramps also have endpoint
  handles. Use the inspector for exact coordinates, dimensions, group and score.
- The two rubber slingshots are selectable hardware too. Move, resize, mirror,
  duplicate or remove them; add more from **Rubber slingshot**. Each flexes
  independently, and its collision follows the visible band and metal base.
  Existing browser drafts and imported SD boards gain editable versions of
  their original pair automatically. Removing both stays removed on export.
- Delete removes the selected part. Duplicate copies it. Cmd/Ctrl-Z undoes;
  Shift-Cmd/Ctrl-Z redoes. Both remain available during play.
- Clone gives a board its own ID, SD filename and high-score identity. New
  creates an empty board with the standard cabinet, drain guides and flippers.
- Change theme to swap the felt, hardware palette, border artwork and score
  sprites. Board name, mission, height and gravity are editable too.
- Double-click empty board space, Alt-click, or use Drop to place a test ball.
  Restart starts another game with a new physics seed. Shift-click Restart to
  replay with the current seed. Fit and +/- control the board view.
- Import reads PBT or JSON. Export produces a device-ready PBT; Shift-click
  Export for JSON. Drafts and last-valid board data are saved in localStorage.

Keyboard controls keep Flipkit's Shift flippers and Space/Enter launcher,
with A and Right arrow assigned to CHGame's directional shakes:

| Action | Keys |
| --- | --- |
| Left flippers | Left Shift, Left arrow |
| Right flippers | Right Shift, D, B |
| Launch | Space, Enter, numpad Enter, Down; A before launch |
| Shake left / right | A / Right arrow |

Tap within 420 ms to build levels 1–3; level 3 matches the old maximum force,
rumble and wobble. A fourth rapid shake tilts: scoring,
flippers and saves stay disabled until the ball drains. Held keys count once.
Quick presses and releases are queued for at least one game frame, including
USB input, so rapid taps are not lost between frames. The whole editor board,
including its header, wobbles with the shared game. A directional
SHAKE/DANGER badge and cabinet rim highlight reinforce each shove; the native
LCD adds edge impacts and a larger strength meter. Pause freezes the effects.

Typing in an input/select does not operate the game. Lost focus, hidden tabs,
closed connections and missed device key heartbeats release the controls.

Changes to the current board preserve balls, score, lives and game time.
Unchanged mechanisms retain their cooldown/state and unchanged ramp rides keep
following their path. Changing board identity or height starts a new game.
A changed/deleted ramp releases its rider into the playfield.

Invalid geometry stays in the draft while the previous valid board keeps
playing. The inspector explains the limit to fix. Incomplete target banks,
rollover sets or missing scoops are warnings, allowing empty or simple boards
to remain playable; those missing mechanisms cannot award their mission bonus.
This deliberately relaxes the old mission-completeness restriction in the PBT
encoder and game validator. Header, checksum, bounds and element limits remain
mandatory. PBT1's binary layout is unchanged.

## Work with CHGame

Install the Pinball **1.4** cart/release once, then connect the handheld by USB.
The ordinary release carries the live protocol; diagnostic hardware builds
omit it to leave space for the larger performance/testing interface.

**Connect CHGame** uses Web Serial directly in desktop Chrome or Edge.
Choose CHGame in the browser's device chooser. Use HTTPS or localhost;
other browsers can still play and edit without a device connection.
Only one browser tab or application can own the serial port at a time.

With **Send edits live** enabled, valid edits are sent after a short debounce
and read back from device RAM. The handheld keeps playing. Keyboard controls,
restart, pause and ball placement are sent to the device as well.

**↑ Get boards from console** reads the built-in and SD libraries from the device. Identical
boards are deduplicated; differing versions are imported as separate copies
so local work is retained.

The save panel distinguishes the browser draft, console RAM and SD file.
**Auto-save to SD** is enabled by default. After the editing debounce, it checks
the console state inside the USB queue. While a game is running (including a
ball waiting in the launcher), the save stays queued without pausing or releasing
the player's controls. It writes when the tester pauses or the game has no balls
left. The save panel says **Auto-save queued · pause console to save**; browser
drafts keep saving and RAM live edits continue in both console-play and separate
web-play modes. Connecting or selecting a board alone never overwrites a layout.
**Save to SD now** and **All boards → Save all pending** explicitly save
immediately and may briefly pause a running game.
The previous SD version is protected as `<filename>.PBK` before the first
overwrite. **Revert…** restores that checkpoint; later auto-saves retain it.
Different SD versions or changed cards require review rather than overwriting
them silently. Existing browser drafts survive updated shipped defaults.

SD persistence uses browser-side FAT code on the same USB connection. It
writes `PINBALL/<filename>.PBT`, verifies it and rescans the library without
switching the active RAM board. The handheld pauses during the save and its
previous pause state is restored. No drive mount, game exit, firmware reflash
or bootloader change is needed for board edits or SD saves.

The save path supports FAT16/FAT32, mirrored FATs, existing or new PINBALL
folders, directory growth, fragmented files, and boards up to 960 bytes.
Unsupported FAT geometries are refused. It writes and verifies a new cluster
chain before changing the destination directory entry, then releases the old
chain. Uncertain directory-write failures leave the new allocation intact;
a power interruption can leave orphaned clusters, so filesystem repair may
be needed after an interrupted SD operation.

## Shared C++ engine, static browser app

The browser compiles the actual sketch, physics, collision shapes and renderer
into WASM. `live::apply()` is shared with the handheld's USB path. The full-board
renderer reuses the game renderer in slices without advancing physics.
Selection, drag/drop and undo stay in JavaScript; editing never pauses play.

`python3 pinball.py build` builds firmware and WASM and runs parity checks from
the same source snapshot. `python3 pinball.py web` builds a deployable static
bundle at `Pinball/build/studio`. `web-check` rejects stale game/editor/assets.
See [build guarantees and validation](../docs/static-studio.md).

The native simulator remains available for diagnostics and hardware-focused
regression tests; it is no longer the browser editor's runtime server.
