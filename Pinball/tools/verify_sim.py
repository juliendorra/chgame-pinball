#!/usr/bin/env python3
"""Exercise the real sketch, FAT reader, solver and camera under UBSan."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import random
import struct
import sys

GAME = Path(__file__).resolve().parents[1]
ROOT = GAME.parent
(ROOT / ".cache/tmp").mkdir(parents=True, exist_ok=True)
os.environ["TMPDIR"] = str(ROOT / ".cache/tmp")
sys.path.insert(0, str(ROOT / "CHGame/tools/chsim"))
sys.path.insert(0, str(GAME / "tools"))
from chdrivelib import Driver, SimTransport
from sim_build import build
from boards import checksum, encode, image

OUT = GAME / "out/verify"
OUT.mkdir(parents=True, exist_ok=True)
specs = json.loads((GAME / "boards/tables.json").read_text())
files = {t["file"] + ".PBT": encode(t) for t in specs}
# These checks run on the host; no GitHub or macOS CI job is dispatched.
sanitizers = os.environ.get("PINBALL_SANITIZERS", "undefined,bounds")
# Limit exclusions to known issues in pinned upstream implementations;
# every check stays enabled for Pinball itself. See sanitizer.ignore.
os.environ["CHSIM_FLAGS"] = (f"-fsanitize={sanitizers} -fsanitize-ignorelist={GAME / 'tools/sanitizer.ignore'} "
                           "-fno-sanitize-recover=all -fno-omit-frame-pointer")
exe = build(GAME, out=OUT / "sim-verify")


@contextmanager
def session(card=None):
    if card:
        os.environ["CHSD_CARD"] = str(card)
    else:
        os.environ.pop("CHSD_CARD", None)
    transport = SimTransport(exe)
    d = Driver(transport, "MPIN")
    try:
        d.handshake()
        d.frames(1)
        yield d
    finally:
        rc = transport.close()
        assert rc == 0 and not any("BUG:" in s or "runtime error" in s or "Sanitizer" in s for s in transport.bugs), transport.bugs


def state(d):
    line = d.query("V", "PIN ")
    return {k: int(v) for k, v in (part.split("=") for part in line.split()[1:])}


def tap(d, buttons, frames=1):
    d.buttons(buttons)
    d.frames(frames)
    d.buttons(0)
    d.frames(1)


def place(d, x, y, vx=0, vy=0):
    d.cmd(f"J {x},{y},{vx},{vy}")


def pixel(data, x, y):
    return (data[y * 64 + x // 2] >> ((x & 1) * 4)) & 15


with session() as d:
    assert state(d)["tables"] == 1
    tap(d, 1)
    assert state(d)["shooter"] == 1
    d.buttons(16); d.frames(1)
    assert state(d)["left"] > 0 and state(d)["right"] == 0, "LEFT must drive only the left flippers"
    d.buttons(2); d.frames(4)
    assert state(d)["left"] == 0 and state(d)["right"] == 255, "B must drive only the right flippers"
    d.buttons(18); d.frames(4)
    assert state(d)["left"] == state(d)["right"] == 255
    d.buttons(0); d.frames(6)
    # Switching shoot buttons while held is still one release to launch.
    d.buttons(8); d.frames(20)
    assert state(d)["shooter"] and state(d)["launch_held"]
    d.buttons(1); d.frames(10)
    assert state(d)["shooter"] and state(d)["launch_held"]
    d.buttons(0); d.frames(1)
    assert not state(d)["shooter"] and state(d)["vy"] < 0
    d.frames(90)
    assert state(d)["camera"] < 50, "launch must reach another screen"
    tap(d, 64)
    before, info = d.shot(), state(d)
    d.frames(120)
    assert before == d.shot() and state(d)["ticks"] == info["ticks"], "pause must freeze solver and camera"
    tap(d, 1)
    assert not state(d)["paused"]
    # A press against a descending ball must strike upward on both sides.
    for x, button, direction in ((45, 16, 1), (79, 2, -1)):
        d.cmd("F 0"); place(d, x, 355, 0, 500); d.buttons(button); d.frames(1)
        s = state(d)
        assert s["vy"] < -1000 and s["vx"] * direction > 0, ("flipper impulse", s)
        d.buttons(0)
    # A lost ball is saved during grace, then consumes exactly one life.
    d.cmd("F 0"); tap(d, 1, 5); place(d, 61, 390, 0, 300); d.frames(1)
    assert state(d)["lives"] == 3 and state(d)["balls"] == 1 and state(d)["x"] == 118
    d.cmd("Z"); place(d, 61, 390, 0, 300); d.frames(1)
    assert state(d)["lives"] == 2 and state(d)["shooter"]
    # Tilt locks the flippers until the current ball is lost.
    d.cmd("F 0")
    place(d, 60, 180)
    for _ in range(4): tap(d, 1)
    assert state(d)["tilt"] == 3
    d.buttons(18); d.frames(5)
    assert state(d)["left"] == state(d)["right"] == 0
    d.buttons(0)
    velocities=[]
    for button,hold in ((1,1),(1,60),(8,1),(8,60)):
        d.cmd("F 0");tap(d,button,hold);s=state(d)
        velocities.append((s["vx"],s["vy"]))
    assert len(set(velocities))==1, ("launch power must not depend on hold duration or button",velocities)
    for side,x,vx in ((0,42,-600),(1,77,600)):
        d.cmd("F 0");place(d,x,317,vx,400);d.frames(1)
        key="rubber_right" if side else "rubber_left"
        assert state(d)[key]>0, ("rubber must flex on actual impact",side,state(d))
        tap(d,64);ticks=state(d)[key];before=d.shot();d.frames(20)
        assert state(d)[key]==ticks and d.shot()==before, "pause must freeze rubber flex"
        tap(d,1);place(d,61,290);d.frames(24)
        assert state(d)[key]==0, "rubber must settle back to its rest position"
print("PASS: fixed-power A/Down launch, scrolling, pause, flipper strikes, ball save, tilt and impact-driven rubber flex")

with session() as d:
    d.cmd("F 0"); d.cmd("O 990"); d.frames(1)
    assert state(d)["pop_ticks"] == 0
    d.cmd("O 10"); d.frames(1); s = state(d)
    assert (s["score"], s["pop"], s["pop_kind"]) == (1000, 1000, 1) and s["pop_ticks"] > 0
    d.frames(36)
    assert state(d)["score"] == 1000 and state(d)["pop_ticks"] == 0, "celebration must expire without changing score"
    d.frames(120); d.cmd("O 6777"); d.frames(1)
    assert state(d)["pop"] == 7777 and state(d)["pop_kind"] == 2, "lucky score must celebrate"
    tap(d, 64); frozen, ticks = d.shot(), state(d)["pop_ticks"]
    d.frames(40)
    assert d.shot() == frozen and state(d)["pop_ticks"] == ticks, "pause must freeze score animation"
    d.cmd("F 0")
    for _ in range(101): d.cmd("O 1000000")
    d.frames(1)
    assert state(d)["score"] == 99999999, "eight-digit score must saturate safely"
print("PASS: round/lucky score milestones, temporary animation, pause, and eight-digit score limit")

# An isolated table exercises the reusable element behaviors without unrelated
# shots hiding an accidental score, collision or capture in the assertions.
lab = json.loads(json.dumps(specs[0]))
lab.update(height=480, title="Element Lab")
def obj(kind, x, y, u=7, v=0, group=0, value=500):
    return dict(kind=kind, x=x, y=y, u=u, v=v, group=group, value=value)
lab["objects"] = [obj("lane", x, 25, group=g) for g, x in enumerate((25, 60, 95))]
lab["objects"] += [obj("drop_target", x, 60, 8, 6, g) for g, x in enumerate((20, 50, 90))]
lab["objects"] += [obj("scoop", 20, 120), obj("spinner", 60, 130, 12),
                   obj("ramp", 80, 250, 20, 90, 1), obj("kickback", 14, 390, 6),
                   obj("gate", 44, 180, 72, 192), obj("saucer", 82, 325),
                   obj("gate", 44, 290, 72, 290, 2)]
card = OUT / "elements.img"
image(card, {"LAB.PBT": encode(lab)})
with session(card) as d:
    d.cmd("F 1")
    place(d, 20, 56, 0, 512); d.frames(2)
    s = state(d)
    assert s["target"] == 1 and s["drops"] == 1
    place(d, 20, 56, 0, 512); d.frames(2)
    assert state(d)["score"] == s["score"] and state(d)["vy"] > 0, "lowered drop target must stop colliding"
    place(d, 60, 130, 0, 800); d.frames(1); s = state(d)
    assert s["spinners"] == 1
    d.frames(20)
    assert state(d)["score"] > s["score"], "spinner must pay during its animation"
    place(d, 80, 262, 0, -400); d.frames(1)
    assert state(d)["ramp"] >= 0 and state(d)["ramps"] == 1
    d.frames(90); s = state(d)
    assert s["ramp"] == -1 and (s["x"], s["y"]) == (20, 90), ("curved ramp must deliver to its configured exit", s)
    place(d, 14, 390, 0, 400); d.frames(1)
    assert state(d)["kickbacks"] == 1 and state(d)["vy"] < 0
    place(d, 14, 390, 0, 400); d.frames(1)
    assert state(d)["kickbacks"] == 1 and state(d)["vy"] > 0, "kickback is one-shot"
    for x in (25, 60, 95):
        place(d, x, 25); d.frames(1)
    assert state(d)["mult"] == 2 and state(d)["lanes"] == 0
    # Wait out the short impact cooldown, clear of the rescue trigger.
    place(d, 60, 300); d.frames(55)
    place(d, 14, 390, 0, 400); d.frames(1)
    assert state(d)["kickbacks"] == 2, "lane set must rearm kickback"
    place(d, 58, 180, 0, 700); d.frames(1)
    assert state(d)["vy"] < 0, "one-way gate must reject the blocked direction"
    place(d, 58, 196, 0, -900); d.frames(20)
    assert state(d)["y"] < 180 and state(d)["vy"] < 0, "one-way gate must swing clear and let the ball pass"
    place(d, 82, 325); d.frames(1)
    assert state(d)["hold"] == 60 and state(d)["saucers"] == 1
    d.frames(60); s = state(d)
    assert s["hold"] == 0 and s["y"] > 337 and s["vx"] < 0 and s["vy"] > 0, ("saucer must eject beyond its lip", s)
    place(d, 118, 70, 300, 200); d.frames(1)
    assert state(d)["x"] <= 108 and not state(d)["launching"], "ball must not return to shooter lane"
    place(d, 11, 270, -1000, 0); d.frames(1)
    assert 0 < state(d)["vx"] < 600, "passive rubber must lose rebound energy"
    d.cmd("F 1"); place(d, 58, 285); d.frames(220)
    s=state(d)
    assert s["searches"]==0 and abs(s["y"]-285)<=2 and s["lives"]==3 and not s["over"], "shake help must not kick a settled ball or change the turn"
    for x, inward in ((24, 1), (94, -1)):
        d.cmd("F 1"); place(d, x, 420, 0, 500)
        reached = False
        for _ in range(120):
            d.frames(1); s = state(d)
            if s["y"] >= 450:
                assert s["x"] >= 30 if inward > 0 else s["x"] <= 94, ("return lane must feed onto flipper", s)
                reached = True; break
        assert reached, ("inlane must not trap the ball", x, state(d))
    d.cmd("F 1"); place(d, 12, 420, 0, 700); d.frames(90)
    assert state(d)["lives"] < 3, "narrow outlane must remain a real drain"
print("PASS: drop targets, spinner animation scoring, curved ramp transport, kickback/rearm, directional gate, saucer eject, closed shooter lane and damped rubber")
print("PASS: informational stuck-ball help, return lanes onto both flippers and a narrow working outlane")

# Reproduce the photographed pocket around the flipper's outer base, with
# flippers already held (which used to disable the automatic ball search).
card = OUT / "drains.img"
image(card, files)
drain_cases = 0
with session(card) as d:
    huds = []
    for index, spec in enumerate(specs, 1):
        for held in (0, 18):
            for x in (22, 24, 100, 102, 104):
                for vy in (0, 400):
                    d.cmd(f"F {index}"); d.buttons(held); d.frames(5)
                    place(d, x, spec["height"] - 25, 0, vy); d.frames(100)
                    s = state(d)
                    assert s["lives"] == 2 and s["shooter"] and s["searches"] == 0, ("side gutter must drain without a recovery nudge", spec["title"], x, held, vy, s)
                    drain_cases += 1
        d.buttons(0); d.cmd(f"F {index}"); d.cmd("O 123450"); d.frames(1)
        huds.append(d.shot()[:10 * 64])
        # Shadows use each felt's RGB components, without shifting the
        # ball anchor. They remain part of the playfield camera transform.
        place(d, 64, spec["height"] - 40)
        d.cmd("W 256"); shaded = d.shot(); s = state(d)
        row = spec["height"] - 40 - s["camera"] + 12
        assert pixel(shaded, 64, row) == 1, "ball sprite must stay on its collision center"
        assert pixel(shaded, 66, row + 7) == 2, "ball must cast a lower-right shadow"
        from fbimage import palette_rgb
        colors = palette_rgb(shaded[8192:])
        assert colors[2] == tuple(v // 34 * 17 for v in colors[0]), ("shadow must follow felt color", spec["title"], colors)
        # Every ramp gets a continuous ride across multiple viewport heights.
        for ramp in (o for o in spec["objects"] if o["kind"] == "ramp"):
            d.cmd(f"F {index}"); d.cmd(f"M {max(0, min(spec['height'] - 108, ramp['y'] - 62))}")
            # Low side ramps can border a slingshot. Enter through the
            # outer half of the mouth so this camera test does not start
            # with an unrelated rubber-band collision under contact spin.
            approach=ramp["x"]+(-4 if ramp["x"]<60 else 4)
            place(d, approach, ramp["y"]+4, 0, -500); d.frames(1)
            assert state(d)["ramp"] >= 0, ("ramp entrance rejected",spec["title"],ramp,state(d))
            for frame in range(1, 91):
                d.frames(1); s = state(d)
                if frame >= 4: assert s["zoom"] == 384, ("ramp zoom ended before the exit", spec["title"], frame, s)
                if frame < 90: assert s["ramp_camera"] and s["ramp"] >= 0
                # The followed ball stays visible as camera and crop cross screens.
                crop_h = 1 + 107 * 256 // s["zoom"]
                y0 = max(0, min(108 - crop_h, s["y"] - s["camera"] - 54 * 256 // s["zoom"]))
                screen_y = 12 + (s["y"] - s["camera"] - y0) * s["zoom"] // 256
                assert 12 <= screen_y < 120, ("ramp camera lost the ball", spec["title"], frame, s)
            assert (s["x"], s["y"], s["ramp"]) == (ramp["u"], ramp["v"], -1)
    assert len(set(huds)) == 9, "each board must have its own score glyphs"
(OUT / "drain-regression.json").write_text(json.dumps({"cases": drain_cases, "result": "passed", "recovery_nudges": 0}) + "\n")
print(f"PASS: {drain_cases} photographed-gutter regressions across nine boards, full-length ramp camera rides, nine score styles and felt-tinted ball shadows")

for fs in ("fat16", "fat32"):
    card = OUT / f"pack-{fs}.img"
    image(card, {"PINBALL/" + k: v for k, v in files.items()}, fs=fs,
          fragment={"PINBALL/PIRATES.PBT": 2}, spc=1)
    with session(card) as d:
        assert state(d)["tables"] == len(specs) + 1
        for index, spec in enumerate(specs, 1):
            d.cmd(f"F {index}")
            s = state(d)
            assert (s["id"], s["height"], s["objects"]) == (spec["id"], spec["height"], len(spec["objects"]))
            assert s["score"] == 0 and s["lives"] == 3
        # Drive the pirate rules using actual contacts in all three banks.
        pirate = specs[-1]
        for group in range(3):
            o = next(o for o in pirate["objects"] if o["kind"] in ("target", "drop_target") and o["group"] == group)
            place(d, o["x"], o["y"] - 4, 0, 512); d.frames(2)
        assert state(d)["target"] == 7 and state(d)["score"] > 0
        # Move away from the lower deck so the special-hit zoom may engage.
        scoop = next(o for o in pirate["objects"] if o["kind"] == "scoop")
        place(d, scoop["x"], scoop["y"]+6, 0, -500); d.frames(6)
        s = state(d)
        assert s["balls"] == 3 and s["mode"] > 1000 and s["target"] == 0, s
        assert s["zoom"] > 256, "scoop must whip the camera toward the ball"
        d.frames(90)
        assert state(d)["zoom"] == 256, "special zoom must return to the wide table"
        # Rescanning SD and returning from the library preserves live state.
        tap(d, 128); before = state(d)
        tap(d, 128); after = state(d)
        assert after["tables"] == len(specs) + 1 and after["id"] == before["id"]
        assert after["score"] == before["score"] and after["ticks"] == before["ticks"]
        tap(d, 2)
        assert state(d)["screen"] == 1
        before = state(d)
        d.cmd("E 1"); d.cmd("F 1")
        after = state(d)
        assert (after["id"], after["score"], after["ticks"]) == (before["id"], before["score"], before["ticks"])
        d.cmd("D"); assert state(d)["tables"] == 1
        d.cmd("E 0"); d.cmd("D"); assert state(d)["tables"] == len(specs) + 1
print("PASS: FAT16/FAT32, folder discovery, every table, three-bank multiball, zoom trigger/return and rescan/resume")

# Compare the in-place packed-pixel zoom to an independent, out-of-place
# nearest-neighbor reference, including extreme crop positions and every
# camera scale used by the animation. The HUD must remain byte-identical.
with session() as d:
    d.cmd("F 0")
    for x, y, camera in ((6,285,276),(63,330,276),(122,382,276),
                         (64,28,0),(8,18,0),(124,22,0)):
        d.cmd(f"M {camera}")
        place(d, x, y)
        d.cmd("W 256"); plain = d.shot(); info = state(d)
        for zoom in range(272, 449, 16):
            d.cmd(f"W {zoom}"); actual = d.shot()
            width, height = 1 + 127 * 256 // zoom, 1 + 107 * 256 // zoom
            x0 = max(0, min(128 - width, x - 64 * 256 // zoom))
            y0 = max(0, min(108 - height, y - info["camera"] - 54 * 256 // zoom))
            for dy in range(12, 120):
                for dx in range(128):
                    expected = pixel(plain, x0 + dx * 256 // zoom, 12 + y0 + (dy - 12) * 256 // zoom)
                    assert pixel(actual, dx, dy) == expected, ("zoom sampling", zoom, dx, dy)
            assert actual[:12 * 64] == plain[:12 * 64]
            assert actual[120 * 64:] == plain[120 * 64:], "zoom must preserve HUD and palette"
print("PASS: 72 zoom frames including the themed upper corners match an independent pixel reference; fixed HUD and palette are intact")

# Invalid inputs are real files on a card, with valid checksums on malformed
# structures so structural checks cannot accidentally hide behind CRC checks.
original = files["NEON.PBT"]
bad_files = {"BADCRC.PBT": original[:-1] + bytes([original[-1] ^ 1]),
             "SHORT.PBT": original[:80], "LONG.PBT": original + b"\0"}
for name, offset, value in (("BADKIND", 96, 99), ("COUNT", 6, 73), ("THEME", 5, 9),
                            ("BADPOS", 98, 255), ("BADTEXT", 20, 1), ("BADVER", 4, 2)):
    data = bytearray(original); data[offset] = value
    struct.pack_into("<I", data, 16, checksum(data))
    bad_files[name + ".PBT"] = bytes(data)
card = OUT / "invalid.img"
image(card, {**bad_files, "GOOD.PBT": files["PIRATES.PBT"]}, fs="fat16")
with session(card) as d:
    d.cmd("F 0"); before = state(d)
    for index in range(1, len(bad_files) + 1):
        d.cmd(f"F {index}")
        after = state(d)
        assert after["id"] == before["id"] and after["lives"] == before["lives"]
    d.cmd(f"F {len(bad_files) + 1}")
    assert state(d)["id"] == specs[-1]["id"], "good file after corrupt files must still load"
print("PASS: corrupt, truncated, oversized, unsupported and structurally invalid tables leave the running table intact")

# Long play with changing inputs, all table geometries and maximum launch
# velocity. The sanitizers inspect every raster and collision operation.
card = OUT / "pack-fat16.img"
rng = random.Random(0x50494E)
with session(card) as d:
    for index, spec in enumerate(specs, 1):
        d.cmd(f"F {index}"); tap(d, 1, 60)
        for _ in range(120):
            s = state(d)
            if s["over"]: tap(d, 1)
            elif s["shooter"]: tap(d, 8, rng.randrange(1, 61))
            else:
                d.buttons(rng.choice((0, 2, 16, 18)))
                d.frames(rng.randrange(2, 25))
            s = state(d)
            assert 0 <= s["x"] <= 127 and 0 <= s["y"] <= spec["height"] + 6, s
            assert -24 <= s["camera"] <= spec["height"] - 108 and 256 <= s["zoom"] <= 448
        d.buttons(0)
print(f"PASS: extended play on all nine tables with {sanitizers} sanitizers")
print("All pinball simulator checks passed.")
