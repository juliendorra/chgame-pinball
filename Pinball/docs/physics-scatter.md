# Seeded impact scatter

Pinball 1.4.9 adds small angular variations at impacts and controlled ejects.
The solver remains fixed-step, integer-based and reproducible: the same board,
seed and frame-timed controls/edits produce the same physics.

## Why this approach

Visual Pinball exposes scatter per material and scales it with difficulty.
Its collision implementation applies scatter after the normal impulse,
skips low-speed contacts and rotates the outgoing velocity. Box2D emphasizes
same-input determinism and keeping timer/random-event dependencies out of
the solver. Our choice is contact-triggered scatter from an explicit,
simulation-owned PRNG; there is no per-frame position noise.

Primary references:

- [Visual Pinball physics guidance](https://github.com/vpinball/vpinball/blob/master/docs/PhysicValues.txt)
- [Visual Pinball wall collision implementation](https://github.com/vpinball/vpinball/blob/master/src/physics/hitball.cpp)
- [Box2D determinism](https://box2d.org/documentation/md_questions.html)

The algorithm here is independently implemented for this integer solver.

## Bounds and timing

| Event | Nominal maximum angle |
| --- | --- |
| Firm passive wall, guide, post or rubber rebound | about ±0.43° |
| Powered bumper, sling or target contact | about ±1.74° |
| Scoop, saucer or kickback eject | about ±0.87° |

The signed sample has a symmetric triangular distribution, favoring small
angles near zero. Passive/powered contact sampling requires an incoming normal
velocity greater than 256 Q8 units (one nominal pixel/frame). Resting, separating
and soft contacts do not consume random samples. Each ball receives at most
one angular perturbation per physics update, covering both collision substeps
without repeatedly jittering at a rail junction.

Collision geometry, contact separation, flipper strokes, fixed-power launch,
shake controls and ramp transport retain their existing rules. The Q14 rotation
is conservatively rounded so it cannot increase speed; integer rounding may
lose a very small amount. No trigonometric library is needed on the console.

## Seeds and replay

The initial seed and the evolving xorshift32 state live in `Game`. They are
separate from the autoplayer's salted input stream and all drawing code. A new
game chooses its next default seed from the previous stream, table ID and a
fixed constant. It does not read wall-clock time. Explicit nonzero 32-bit seeds
are supported; zero means choose the next default seed.

- C++: `newGame(seed)`.
- WASM: `pb_restart(seed)`; state includes unsigned `seed` and `rng`.
- USB: `@R 305419896` restarts with that seed.
- USB: `@Z` returns `LIVE DATA` followed by eight bytes: initial seed and evolving RNG state, both little-endian uint32.
- Studio: Restart chooses a fresh seed; Shift-click Restart reuses the current
  seed. A directly connected console receives that same explicit replay seed.

Live geometry/theme edits preserve the RNG stream. Pausing freezes it. Rendering
extra frames does not consume it. To reproduce a run, keep the initial board,
seed, frame-timed controls and any edits; a seed alone cannot reproduce different
inputs or board geometry.

## Validation and console budget

Native and WASM replays compare seed/state, ball motion, PBT readback and complete
full-board pixels. Tests cover repeated seeds, different first-bumper rebounds,
extra rendering, pause, live theme edits, quiet contact and firm wall impacts.
The native replay driver additionally tests 40,960 integer rotations across all
five supported strengths for angle bounds, no energy gain, repeatability and the one-event
cap. Sanitizer regressions exercise all nine boards, launch, gates, gutters,
multiball, ramp rides and flipper contacts.

To retain both console save pages, release builds omit counters used solely by
host/debug evaluation. Their updates remain in native/WASM and diagnostic builds;
no gameplay decision reads them. The scoop/saucer placement code is shared, and
the redundant hidden tilt announcement was removed: the persistent tilt warning
continues to render directly from tilt state.

## Repeatable gameplay benchmark

```sh
python3 Pinball/tools/benchmark_scatter.py --check
# After reviewing an intentional physics/tuning change:
python3 Pinball/tools/benchmark_scatter.py --record-baseline
# Optional figure (requires matplotlib):
python3 Pinball/tools/plot_scatter.py Pinball/out/scatter-benchmark/report.json
```

The default workload uses 32 frozen physics/control seeds, two player policies,
all nine boards and a 120-second session cap. A separate frozen stream supplies
512 seeds for each of 18 real contact fixtures, covering normal/oblique impacts,
two approach speeds and typical/maximum-valid bumper strength. Each complete
native experiment runs twice and must produce identical measurements.

The benchmark shares Studio's engine sources and compiler configuration. It
links the actual solver, geometry, input rules and autoplay; it does not imitate
physics in Python. Only `Physics.cpp` and the experiment banner are rebuilt for
each compile-time ablation. Production strengths live in `Scatter.h`. There is
no runtime tuning state or benchmark instrumentation in the console build.

The nine configurations include scatter off, passive alone, powered alone,
current settings, half-powered strength, double-passive strength, and three
controls retaining the conservative cosine while zeroing the sine. Those last
controls isolate angular variation from the small constant speed loss. Supported
rotation strengths are compile-time checked to preserve the energy bound.

Fixed-input sessions receive exactly the same complete button tape under every
configuration, including periodic Down launch pulses. The reactive player uses
the existing timing model and responds to the changed path. Its control seed
stays fixed; its actual input sequence changes with ball motion. The report
keeps these two experiments separate.

Measurements include outgoing velocity and angle, displacement at 1/15/30/60
frames, one-ball-diameter path divergence sampled once per second over the
common active first-ball portion, scores, life losses per minute, coverage,
ramps, flipper hits, stalls and search recoveries. Controlled flights assert
that a scatter event happened and no second contact contaminated the window.
Soft contacts must preserve RNG state and remain identical across variants.

`report.json`, `report.md` and raw per-configuration JSONL go under
`out/scatter-benchmark/`. The checked-in `scatter-baseline.json` records the
workload, all configuration measurement hashes and complete summarized results.
`--check` rejects changed workload or measurements. It always writes a new report
for review before failing. Recording a new baseline is an explicit command.

The report shows paired 95% bootstrap intervals over seed clusters, retaining
all nine boards in every sampled cluster, plus per-board intervals. It compares
current settings both with scatter off and with half-strength powered scatter.
A 4 px fixture shift, a 15% observed duration loss or a 20% score loss is a
**review threshold**, not a validated fun criterion. Local regressions must
remain visible when aggregate results improve. Sessions still running at the
cap are censored; these results cannot estimate uncapped ball/session lifetime.
Human playtesting remains necessary for enjoyment and physical button feel.

### Initial findings with the 1.4.9 strengths

Passive scatter is small locally: p95 displacement after a second is 0.42 px
for oblique wall rebounds, and effectively zero for centered normal rebounds
once integer friction has erased the sideways velocity. It still changes later
routes by at least a ball diameter in all 288 fixed-input board sessions. The
angle-only control confirms that this is not just the conservative speed loss.

At the 280 bumper kick used by all nine shipped boards, powered oblique rebounds
have a 2.32 px p95 displacement after a second (3.16 px maximum in the corpus).
At the maximum allowed 1600 kick, p95 grows to 5.93 px: a useful warning for
future custom boards. Halving powered scatter reduces those p95 values to
1.19 px and 2.91 px respectively.

Compared directly with half-powered scatter, the current setting changes mean
observed reactive duration by -0.07% (95% CI -2.35 to +2.44%) and score by
+9.4% (CI -11.6 to +34.4%). This test does not establish a benefit from halving
the current strength, so the defaults remain unchanged. Individual boards
still require review: Orbital Robot, Shuttle Run and Dragon Keep score worse
versus no scatter. The report includes their uncertainty and shows that halving
powered scatter does not consistently remedy those differences.
