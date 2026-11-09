# Contact spin experiment

`Spin.h` adds an optional, deterministic contact-friction model. The production
default is `PINBALL_SPIN_GRIP=0`; the normal Studio build retains the existing
seeded-scatter physics. The console playtest uses light spin (grip 16) with
scatter disabled, through an isolated firmware snapshot; this does not change
the tracked production defaults. The experiment does not silently select a
new default based on a bot's score.

Each ball stores rotation about the playfield normal as its surface speed
(`omega * radius`) in Q16. Oblique contact creates spin by friction; the same
spin changes tangential motion at later contacts. It is not randomly chosen.
Q16 storage preserves small rotation during its approximately three-second
half-life, instead of losing one whole Q8 velocity unit per frame. New serves,
ball saves, scripted ramp transport and cup captures clear it.

For a solid sphere with inertia `2/5 * mass * radius²`, the slip-removing
tangential impulse per unit mass is `-2/7 * slip`. We bound its magnitude by
`grip * normalImpulse`. The opposite torque changes the stored surface speed
by `-5/2 * impulse`. This is a small integer specialization of the usual
[contact-friction impulse method](https://box2d.org/files/ErinCatto_SequentialImpulses_GDC2006.pdf),
not a copy of Pokémon's abstract spin accumulator.

Wall, target, bumper and art-derived flipper contacts use the same helper.
Flippers supply a contact-point vertical surface speed estimated from their
stroke and distance from the pivot. Their existing normal launch impulse,
silhouettes and swept collision solver remain intact. Grip choices of 1/16,
1/8 and 1/4 are experimental settings, not measured material coefficients.
This models a single rotation axis, not full three-dimensional rolling,
topspin, airborne motion or a fully dynamic flipper mechanism.

Integer normals and component rounding can produce a small energy increase
near rolling contact. The helper rejects any such tangential impulse, checking
combined linear and rotational energy with integer arithmetic in the surface
frame. A moving bat can still transfer energy in the board frame. Passive
friction cannot create energy. The existing normal collision and powered kick
remain separate from this check.

Spin state exists in all host experiment builds so variant object files share
one layout. Disabled console builds omit it and compile out the spin helper,
decay and clears. The console version has not been replaced with this prototype.

## Reproduce the comparison

```sh
python3 Pinball/tools/benchmark_spin.py --check
python3 Pinball/tools/benchmark_spin.py --check --sanitize --verify-wasm
```

No emulator or Python approximation of the physics is used: the harness builds
the actual C++ game, libraries and board geometry through Studio's shared build
recipe. The corpus uses all nine boards, 32 seeds per board, two synthetic
players and a 120-second session cap. Seven models produce 4,032 sessions;
each complete run is repeated byte for byte. Isolated wall/bumper flight
fixtures use the earlier scatter benchmark's 512-seed corpus as well.

The fixed player receives identical complete button tapes across models. The
reactive player retains its timing policy and seed but responds to the changed
ball path. Its resulting button sequence therefore differs. The report shows
both players, per-board results, coverage, ramps, flipper hits, stalls and
seed-cluster bootstrap intervals. Scores are sensitive to different payout
scales between boards, so a leave-one-board-out sensitivity check exposes
aggregate results dominated by a single board.

Models:

| Name | Contact grip | Passive scatter | Powered / eject scatter | Spin history |
| --- | ---: | --- | --- | --- |
| `current` | 0 | Production | Production | None |
| `no_scatter` | 0 | Off | Off | None |
| `spin_light` | 1/16 | Off | Off | Persistent |
| `spin` | 1/8 | Off | Off | Persistent |
| `spin_grippy` | 1/4 | Off | Off | Persistent |
| `hybrid` | 1/8 | Off | Production | Persistent |
| `spin_no_memory` | 1/8 | Off | Off | Cleared before every contact |

The no-memory ablation retains contact friction while removing its history.
Comparing it with `spin` separates the effect of stored rotation from merely
reducing sideways speed. Spin-only isolated shots must be identical across
different RNG seeds. Legacy scale-zero scatter still advances its RNG, but
does not affect the trajectory.

The helper's 105,400 contact checks cover mirrored impacts, Coulomb limits,
slip reduction, moving surfaces, stored-spin effects and combined energy,
including the solver's truncated integer normals. `--sanitize` instruments
the full native game. `--verify-wasm` compares complete spin and hybrid probe
output, including spin-state hashes, with pinned Emscripten builds: 72 board
sessions per model plus contact fixtures. The normal Studio parity suite
continues to cover the production model's rendering and live board edits.

Reports and raw JSONL go to `out/spin-benchmark/`. The checked-in
`spin-baseline.json` freezes the workload, configurations and all raw hashes;
`--check` fails if these change, while leaving a new report to review. Use
`--record-baseline` only after reviewing intended changes. The initial report
also checks the current and no-scatter outputs against the previous scatter
baseline, proving that the control has not changed with the experiment.

Optional plot (requires matplotlib):

```sh
python3 Pinball/tools/plot_spin.py Pinball/out/spin-benchmark/report.json
```

Observed duration is capped session time; surviving games are censored. The
synthetic players do not establish physical realism, human enjoyment or button
feel. A higher score can reflect a repetitive lucrative route. These results
are evidence for further tuning and human comparison, not an automatic reason
to change the shipping physics.

## Initial results

Relative to the unchanged production scatter model, the reactive player's
paired results are:

| Model | Observed duration change (95% CI) | Score change (95% CI) |
| --- | ---: | ---: |
| Light spin | -10.1% [-13.4, -7.0] | +35.3% [+2.1, +77.2] |
| Spin | -7.0% [-11.2, -3.2] | -35.0% [-48.4, -19.4] |
| Strong spin | -18.0% [-20.7, -15.2] | -51.1% [-60.7, -40.6] |
| Spin + powered scatter | +1.5% [-0.7, +3.7] | -23.1% [-38.6, -5.1] |

Light spin's score gain is dominated by Storm Riders. Removing that board
changes the aggregate score result to -28.4%. Mean reactive coverage falls
from 61.1 to 46.7 of 96 cells, and ramp rides from 2.14 to 1.56 per session.
The fixed-input player also loses score with light spin: -18.7% (CI -30.8 to
-5.7). This does not support treating the aggregate reactive score gain as a
general gameplay improvement.

At 1/8 grip, persistent spin versus the same friction without contact history
changes reactive duration by +3.3% (CI -1.6 to +8.2) and score by +0.9%
(CI -13.4 to +16.1). Neither establishes a clear benefit from the history term
in this cohort. The hybrid preserves coverage better than spin alone but
reduces scores, particularly on Midnight Manor.

All seven configurations repeated exactly. The production and no-scatter
control outputs match their previous frozen raw hashes. Full native sanitizer
runs and spin/hybrid native-WASM trace comparisons passed. The experiment stays
available for further tuning; the production physics remains the default.
