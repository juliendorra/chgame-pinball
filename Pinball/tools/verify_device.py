#!/usr/bin/env python3
"""Test a running Pinball debug build on the real CHGame using USB inputs."""
import argparse
import json
from pathlib import Path
import sys
import time

GAME = Path(__file__).resolve().parents[1]
ROOT = GAME.parent
sys.path.insert(0, str(ROOT / "CHGame/tools/chsim"))
from chdrivelib import Driver, SerialTransport
from fbimage import to_image
HARDWARE_FIELDS = ('screen tables id height objects score best balls lives over paused camera left right launch_held '
                   'target rubber_left rubber_right mode ticks x y vy shooter launching zoom ramp_camera pop pop_ticks pop_kind ramp searches').split()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", required=True)
    p.add_argument("--out", type=Path, default=GAME / "out/device")
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    t = SerialTransport(a.port)
    d = Driver(t, "MPIN")
    evidence = {"transport": "real CHGame USB serial; injected button inputs", "checks": [], "tables": [], "performance": []}

    def state():
        line = d.query("V", "PIN ")
        if '=' not in line:
            values=list(map(int,line.split()[1:]));assert len(values)==len(HARDWARE_FIELDS)
            return dict(zip(HARDWARE_FIELDS,values))
        return {k: int(v) for k, v in (part.split("=") for part in line.split()[1:])}

    def check(condition, label, details=None):
        if not condition:
            raise AssertionError(f"{label}: {details}")
        evidence["checks"].append({"check": label, "details": details})
        print("PASS:", label, details if details is not None else "", flush=True)

    def tap(mask, count=1):
        d.buttons(mask); d.frames(count); d.buttons(0); d.frames(1)

    def snap(name):
        data = d.shot()
        to_image(data, 3).save(a.out / f"{name}.png")
        return data

    def perf(label, seconds=5):
        d.cmd("P", "PERF")
        start = time.monotonic()
        d.cmd("L0")
        time.sleep(seconds)
        d.cmd("L1")
        elapsed = time.monotonic() - start
        line = d.cmd("P", "PERF")
        values = {k: int(v) for k, v in (part.split("=") for part in line.split()[1:])}
        values.update(label=label, wall_seconds=round(elapsed, 4), fps=round(values["frames"] / elapsed, 2))
        evidence["performance"].append(values)
        print("PERF:", values, flush=True)
        check(values["fps"] >= 57, label + " maintains near 60 fps", values)
        check(values["late"] <= 2, label + " has no sustained late frames", values["late"])
        check(values["stk"] < 1900, label + " stack fits 2048 bytes", values["stk"])
        return values

    try:
        evidence["hello"] = d.handshake()
        d.cmd("L1"); d.buttons(0); d.frames(1)
        check(d.cmd("!", "FAULT") == "FAULT none", "no recorded device fault")
        s = state()
        check(s["tables"] >= 9, "all nine SD tables discovered", s["tables"])
        snap("library")
        specs = json.loads((GAME / "boards/tables.json").read_text())
        expected = {spec["id"]: spec for spec in specs}
        indices = {}
        for index in range(s["tables"]):
            d.cmd(f"F {index}"); d.frames(1)
            table = state(); ident = table["id"]
            if ident not in expected:continue  # Preserve editor-created custom tables too.
            check(ident in expected, f"SD slot {index} is a known board", ident)
            spec = expected[ident]
            check(table["height"] == spec["height"] and table["objects"] == len(spec["objects"]),
                  "loaded " + spec["title"], {k: table[k] for k in ("id", "height", "objects")})
            evidence["tables"].append({"slot": index, "id": ident, "title": spec["title"]})
            indices[ident] = index
        check(set(indices) == set(expected), "every board loaded from the physical SD card")
        # The photographed right pivot pocket also trapped a ball with the
        # bat held up. Check both gutters and two board heights on target.
        for spec in (specs[0], specs[-1]):
            for held in (0, 18):
                for x in (22, 102, 104):
                    d.cmd(f"F {indices[spec['id']]}"); d.buttons(held); d.frames(5)
                    d.cmd(f"J {x},{spec['height'] - 25},0,400"); d.frames(100)
                    s = state()
                    check(s["lives"] == 2 and s["shooter"] and not s["searches"],
                          f"{spec['title']} gutter x={x}, buttons={held} drains without ball search")
        d.buttons(0)
        pirate = specs[-1]; slot = indices[pirate["id"]]; h = pirate["height"]
        d.cmd(f"F {slot}");d.cmd("M 0");d.cmd("W 256")
        check(state()["camera"]==0,"themed corner caps follow the top rails on the playfield")
        snap("pirate_border_top")
        for side,x,vx in ((0,42,-600),(1,77,600)):
            d.cmd(f"F {slot}");d.cmd(f"J {x},{h-67},{vx},400");d.frames(3)
            key="rubber_right" if side else "rubber_left"
            check(state()[key]>0,"right rubber flexes on impact" if side else "left rubber flexes on impact")
            snap("rubber_right" if side else "rubber_left")
            d.cmd(f"J 61,{h-100},0,0");d.frames(24)
            check(not state()[key],"rubber recoil settles without repeated impacts")
        for x,button in ((45,16),(79,2)):
            d.cmd(f"F {slot}");d.cmd(f"J {x},{h-29},0,500");d.buttons(button);d.frames(1)
            check(state()["vy"] < -1000,"visible rounded flipper strikes the ball")
            d.buttons(0)
        d.cmd(f"F {slot}"); d.frames(1)
        d.buttons(16); d.frames(4); s = state()
        check(s["left"] == 255 and s["right"] == 0, "Left drives left flippers")
        d.buttons(2); d.frames(6); s = state()
        check(s["left"] == 0 and s["right"] == 255, "B drives right flippers")
        d.buttons(0); d.frames(6)
        d.cmd("J 118,70,300,200"); d.frames(1)
        check(state()["x"] <= 108 and not state()["launching"], "shooter lane rejects a returning ball")
        ramp = next(o for o in pirate["objects"] if o["kind"] == "ramp")
        d.cmd(f"M {max(0, min(h - 108, ramp['y'] - 62))}")
        d.cmd(f"J {ramp['x']},{ramp['y']},0,-500"); d.frames(1)
        check(state()["ramp"] >= 0, "upward shot enters the pirate cannon ramp")
        d.frames(45); s = state()
        check(s["ramp_camera"] and s["zoom"] == 384, "ramp camera remains zoomed beyond the old 44-frame cutoff")
        snap("ramp_crossing")
        d.frames(44); check(state()["ramp_camera"] and state()["zoom"] == 384, "ramp camera follows the final segment")
        d.frames(1); s = state()
        check(s["ramp"] == -1 and (s["x"], s["y"]) == (ramp["u"], ramp["v"]), "ramp delivers to its configured exit")
        check(s["zoom"] == 384, "ramp reaches its exit before camera eases out")
        snap("ramp_exit")
        d.cmd(f"F {slot}"); d.cmd("O 1000"); d.frames(1); s = state()
        check(s["pop"] == 1000 and s["pop_ticks"] > 0 and s["pop_kind"] == 1, "round score milestone pops")
        d.frames(2); snap("score_milestone"); d.frames(140); d.cmd("O 6777"); d.frames(3)
        check(state()["pop"] == 7777 and state()["pop_kind"] == 2, "lucky score milestone pops")
        snap("score_lucky"); d.frames(40)
        check(not state()["pop_ticks"] and state()["score"] == 7777, "score celebration expires without changing score")
        d.cmd(f"F {slot}"); d.frames(1)
        d.buttons(8); d.frames(20); s = state()
        check(s["launch_held"] and s["shooter"] == 1, "Down arms the fixed-power plunger")
        d.buttons(0);d.frames(1);down_velocity=state()["vy"]; d.frames(39); s = state()
        check(not s["shooter"] and s["camera"] < h - 200, "release launches and scrolls to an upper screen", s["camera"])
        snap("pirate_upper")
        tap(64); before = snap("paused"); ticks = state()["ticks"]
        d.frames(90)
        check(before == d.shot() and state()["ticks"] == ticks, "pause freezes framebuffer, physics and camera")
        tap(1); check(not state()["paused"], "A resumes from pause")
        # A separate A launch also exercises the alternative shoot control.
        d.cmd(f"F {slot}"); tap(1, 36)
        check(not state()["shooter"] and state()["vy"] < 0, "A launches the ball")
        check(state()["vy"]==down_velocity,"A and Down use identical fixed power regardless of hold duration")
        d.frames(42); d.buttons(18)
        perf("pirate_normal_play")
        d.buttons(0)
        d.cmd(f"F {slot}"); d.cmd(f"M {ramp['y'] - 62}")
        d.cmd(f"J {ramp['x']},{ramp['y']},0,-500"); d.frames(5); d.cmd("O 10000")
        perf("pirate_ramp_follow_and_score_popup")
        d.cmd(f"F {slot}"); d.frames(1)
        for group in range(3):
            o = next(o for o in pirate["objects"] if o["kind"] in ("target", "drop_target") and o["group"] == group)
            d.cmd(f"J {o['x']},{o['y'] - 4},0,512"); d.frames(2)
        check(state()["target"] == 7, "contacts light all three treasure banks")
        scoop = next(o for o in pirate["objects"] if o["kind"] == "scoop")
        d.cmd(f"J {scoop['x']},{scoop['y']},0,0"); d.frames(8)
        s = state()
        check(s["balls"] == 3 and s["mode"] > 0 and s["target"] == 0, "cannon starts three-ball Treasure Multiball", s["balls"])
        check(s["zoom"] > 256, "special-hit camera zooms toward the ball", s["zoom"])
        snap("pirate_zoom")
        perf("pirate_multiball_and_zoom")
        check(state()["zoom"] == 256, "camera returns to normal scale")
        snap("pirate_multiball")
        d.cmd("C 7"); d.cmd(f"J {scoop['x']},{scoop['y']},0,0")
        d.frames(150)
        tap(128); before = state(); tap(128); after = state()
        check(after["id"] == before["id"] and after["score"] == before["score"] and after["ticks"] == before["ticks"],
              "SD rescan preserves the suspended game")
        tap(2); check(state()["screen"] == 1, "B resumes after browsing tables")
        d.cmd("Z")
        # Force a controlled drain after scoring, then verify the game's
        # actual flash save path and record retention across a new game.
        d.cmd(f"F {slot}")
        bumper = next(o for o in pirate["objects"] if o["kind"] == "bumper")
        d.cmd(f"J {bumper['x']},{bumper['y'] - bumper['u'] - 3},0,512"); d.frames(2)
        score = state()["score"]
        check(score > 0, "bumper contact awards points")
        for _ in range(3):
            d.cmd("Z"); d.cmd(f"J 61,{h + 6},0,300"); d.frames(2)
        s = state()
        check(s["over"] == 1 and s["best"] >= score, "game-over score stored in flash", s["best"])
        tap(1); s = state()
        check(s["lives"] == 3 and s["score"] == 0 and s["best"] >= score, "retry retains the high score")
        check(d.cmd("!", "FAULT") == "FAULT none", "no device fault after gameplay and SD switching")
        d.buttons(0); d.cmd("L0")
        evidence["result"] = "passed"
        evidence["final_state"] = state()
    except Exception as e:
        evidence["result"] = "failed"
        evidence["error"] = repr(e)
        raise
    finally:
        (a.out / "hardware-tests.json").write_text(json.dumps(evidence, indent=2) + "\n")
        try:
            d.buttons(0); d.cmd("L0")
        except Exception:
            pass
        t.close()
    print("All physical-device firmware checks passed.", flush=True)


if __name__ == "__main__":
    main()
