#!/usr/bin/env python3
"""Seeded autoplay of the real engine: measurable playability proxies, not a claim to measure human fun."""
import argparse
import json
import os
from pathlib import Path
import statistics
import sys

GAME = Path(__file__).resolve().parents[1]
ROOT = GAME.parent
sys.path.insert(0, str(ROOT / "CHGame/tools/chsim"))
sys.path.insert(0, str(GAME / "tools"))
from sim_build import build
from chdrivelib import Driver, SimTransport
from boards import encode, image


def clamp(x): return max(0, min(1, x))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds", type=int, default=6)
    p.add_argument("--seconds", type=int, default=120)
    p.add_argument("--out", type=Path, default=GAME / "docs/playability.json")
    a = p.parse_args()
    if not 1 <= a.seeds <= 32 or not 10 <= a.seconds <= 300:
        raise SystemExit("use 1..32 seeds and 10..300 seconds")
    out = GAME / "out/evaluation"; out.mkdir(parents=True, exist_ok=True)
    specs = json.loads((GAME / "boards/tables.json").read_text())
    card = out / "tables.img"
    image(card, {t["file"] + ".PBT": encode(t) for t in specs})
    os.environ["CHSD_CARD"] = str(card)
    os.environ["CHSIM_FLAGS"] = "-O2"
    exe = build(GAME, out=out / "evaluate-sim")
    t = SimTransport(exe); d = Driver(t, "MPIN")
    report = {"method": "Real physics and element behaviors, normal button inputs only; deterministic seeds; no ball placement or forced scores. "
                        "The reactive player varies flipper timing and uses a legal A/Right shake after a second at rest, respecting the cooldown.",
              "limitation": "Scores are playability proxies. Player enjoyment, aesthetics and physical button feel require human playtesting.",
              "seeds": a.seeds, "max_seconds_per_game": a.seconds, "tables": []}
    try:
        d.handshake(); d.cmd("L1"); d.frames(1)
        for index, spec in enumerate(specs, 1):
            trials = []
            for policy, name in enumerate(("no_flippers", "random", "reactive")):
                for seed in range(1, a.seeds + 1):
                    d.cmd(f"F {index}")
                    line = d.query(f"Y {a.seconds * 60},{seed * 1777},{policy}", "EVAL ")
                    result = {k: int(v) for k, v in (part.split("=") for part in line.split()[1:])}
                    result.update(policy=name, seed=seed)
                    trials.append(result)
            grouped = {name: [t for t in trials if t["policy"] == name] for name in ("no_flippers", "random", "reactive")}
            med = lambda group, key: statistics.median(t[key] for t in grouped[group])
            frames = max(med("reactive", "frames"), 1)
            variety = clamp(med("reactive", "types") / 6)
            skill_score = clamp((med("reactive", "score") - med("random", "score")) / max(med("random", "score"), 1500))
            skill_survival = clamp((frames - med("no_flippers", "frames")) / max(med("no_flippers", "frames"), 600))
            skill = (skill_score + skill_survival) / 2
            progress = clamp((med("reactive", "ramps") + med("reactive", "bank_sets") +
                              med("reactive", "lane_sets") + 2 * med("reactive", "multiballs") +
                              min(med("reactive", "saucers"), 1)) / 4)
            flow = clamp(1 - (med("reactive", "stalled") + med("reactive", "drought") / 2 +
                              med("reactive", "repeated") / 2) / frames)
            pace = clamp(1 - med("reactive", "fast") / frames)
            score = round(25 * variety + 25 * skill + 20 * progress + 20 * flow + 10 * pace, 1)
            warnings = []
            if any(t["nudges"] for t in grouped["reactive"]): warnings.append("reactive player needed a nudge")
            if any(t["searches"] for t in grouped["reactive"]): warnings.append("ball search recovered a stuck ball")
            if any(t["stalled"] / max(t["frames"], 1) > .03 for t in grouped["reactive"]):
                warnings.append("a seed stalled: inspect traps and returns")
            if any(t["drought"] / max(t["frames"], 1) > .25 for t in grouped["reactive"]):
                warnings.append("a seed had long scoring droughts")
            if med("reactive", "repeated") / frames > .25: warnings.append("repetitive routes: inspect shot variety")
            if med("reactive", "ramps") == 0: warnings.append("reactive player did not reach a ramp")
            if med("reactive", "score") <= med("random", "score"): warnings.append("timing advantage not established by this player model")
            if med("reactive", "bank_sets") == 0: warnings.append("bank progression needs a human check")
            entry = {"title": spec["title"], "id": spec["id"], "playability_proxy": score,
                     "components": {"variety": round(variety, 3), "skill": round(skill, 3), "progress": round(progress, 3), "flow": round(flow, 3), "readability": round(pace, 3)},
                     "median_reactive_seconds": round(frames / 60, 1), "median_reactive_score": med("reactive", "score"),
                     "median_random_score": med("random", "score"), "warnings": warnings, "trials": trials}
            report["tables"].append(entry)
            print(f"{spec['title']}: {score}/100 playability proxy; {frames / 60:.1f}s median; " + "; ".join(warnings), flush=True)
    finally:
        rc = t.close()
        if rc or t.bugs: raise SystemExit(f"simulator error: {t.bugs}")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2) + "\n")
    md = ["# Automated board playtests", "", report["method"], "", report["limitation"], "",
          "Launch power is fixed; each seed varies release timing and reactive timing. Games stop at the time limit; survival at that limit is censored. "
          "The hand-weighted 0–100 proxy rewards variety, a timing advantage, progression, flow and readable speed; "
          "it is a design diagnostic, not a validated enjoyment rating. Flags remain visible even on high-scoring tables.", "",
          "| Board | Proxy /100 | Reactive score | Random score | Median seconds | Flags |",
          "| --- | ---: | ---: | ---: | ---: | --- |"]
    for t in report["tables"]:
        md.append(f"| {t['title']} | {t['playability_proxy']} | {t['median_reactive_score']} | {t['median_random_score']} | {t['median_reactive_seconds']} | {'; '.join(t['warnings'])} |")
    a.out.with_suffix(".md").write_text("\n".join(md) + "\n")
    print(a.out)


if __name__ == "__main__": main()
