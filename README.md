# Midnight Pinball for CHGame

Nine original, SD-loadable pinball tables and a live, modeless board editor.
The firmware and browser share the same C++ physics, rules, sprites and renderer.

**[Play and edit in Pinball Studio](https://juliendorra.com/chgame-pinball/)**

Move, add, delete and clone elements while the ball keeps playing. Connect a
CHGame through desktop Chrome/Edge Web Serial to retrieve boards, apply edits
live or save them to its SD card. The hosted editor is entirely static.

Rubber slingshots are editable parts too: move, resize, mirror, duplicate or
remove the existing pair, or add more while playing. Use firmware 1.4.17 or
newer for these layouts on CHGame; older boards retain their original pair.

The current development build adds console-led browser play: the editor replays the inputs
actually sampled by CHGame. Enable **Separate web play** to keep two
independent players while sharing live board edits. Score, mission progress
and play controls sit together above the board. Storm Riders and Dragon Keep
use the revised layouts exported on November 10, 2026. The next packaged
release is being held while more boards are revised.

Download the console cart and matching offline editor from the
[latest release](https://github.com/juliendorra/chgame-pinball/releases/latest).

| Key | Action |
| --- | --- |
| Left / B | Left / right flippers |
| Down | Launch |
| A | Launch in shooter lane; shake during play |
| Right | Shake; repeated strong shakes cause tilt |
| Pause button in editor / START on CHGame | Pause |

See [the game guide](Pinball/README.md) and [build guarantees](Pinball/docs/static-studio.md).

## Build the editor

Install Python 3.12+, Node.js 22 and Clang, then:

```sh
git clone https://github.com/juliendorra/chgame-pinball.git
cd chgame-pinball
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
git clone https://github.com/emscripten-core/emsdk.git .toolchains/pinball-emsdk
python3 .toolchains/pinball-emsdk/emsdk.py install 4.0.15
python3 .toolchains/pinball-emsdk/emsdk.py activate 4.0.15
python3 pinball.py web
python3 pinball.py editor --no-build --open
```

The build runs native/WASM state and pixel parity, editor tests, independent
FAT readback tests, sanitized physics regressions and repeated synthetic play.
Only a validated bundle is published to `Pinball/build/studio/`. A freshness
manifest records game inputs and artifact hashes. No generated build files
or proprietary Game Boy ROMs are included in this repository.

## Firmware

Install `uv` and Arduino CLI, then run `python3 pinball.py setup`.
On Apple silicon, this also builds the native RISC-V compiler; see
[toolchain requirements](tools/toolchain/CURRENT-GCC.md).
`python3 pinball.py build` builds firmware and its matching validated editor.
`python3 pinball.py upload` builds and installs on a connected CHGame.

## Publishing

[The deployment guide](docs/deployment.md) describes OVH directory scoping,
repository secrets and the site-only deployment trigger.

This initial source snapshot comes from workspace commit
`000005c4e34636799bb5ea9eeb329852b60ea8b8` (game 1.4.15).
The standalone packaging changes build paths, not game behavior.
CHGame libraries and host tools are bundled at the exact revision used by
the game; see [SDK provenance](CHGame/VENDOR.json).
See [third-party notices](NOTICE) for dependency licenses.

## SD saves

Pinball uses [CHSave 0.6.0](https://github.com/juliendorra/chgame-sd-saves/tree/v0.6.0).
Scores and mute settings are saved automatically in `/SAVES/`.

To keep scores from 1.4.18, move its `2A69WJNM.SAV` and `O92D2HN3.SAV`
from the card root into `/SAVES/`. Keep any existing files in that folder.
