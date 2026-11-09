# Captured Pinball messages

Open `index.html`, or serve this directory as a static site. The page includes all 91 captured states in nine themes, their animations, and full LCD images.

These are actual C++ renderer captures at the native LCD resolution; CSS enlarges pixels without smoothing. Captures are stored losslessly at native resolution to avoid committing enlarged duplicates.

Regenerate after changing game messages:

```sh
python3 Pinball/tools/preview_popups.py
python3 Pinball/tools/preview_popups.py --publish-only
```

`--check-layout` runs the margin, target-sprite gap, and score-caption padding regressions without regenerating the images. `layout-checks.json` records the checked renderer hash.
