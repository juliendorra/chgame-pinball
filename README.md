# Midnight Pinball for CHGame

Nine original, SD-loadable pinball tables and a live, modeless board editor.
The firmware and browser share the same C++ physics, rules, sprites and renderer.

**[Play and edit in Pinball Studio](https://juliendorra.com/chgame-pinball/)**

Move, add, delete and clone elements while the ball keeps playing. Connect a
CHGame through desktop Chrome/Edge Web Serial to retrieve boards, apply edits
live or save them to its SD card. The hosted editor is entirely static.

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
git clone --recurse-submodules https://github.com/juliendorra/chgame-pinball.git
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
Scores and settings use an isolated `MPIN.SAV` journal on SD.

## Publishing

[The deployment guide](docs/deployment.md) describes OVH directory scoping,
repository secrets and the site-only deployment trigger.

This initial source snapshot comes from workspace commit
`000005c4e34636799bb5ea9eeb329852b60ea8b8` (game 1.4.15).
The standalone packaging changes build paths, not game behavior.
See [third-party notices](NOTICE) for dependency licenses.
