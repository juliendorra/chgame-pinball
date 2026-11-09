# Automated board playtests

Real physics and element behaviors, normal button inputs only; deterministic seeds; no ball placement or forced scores. The reactive player varies flipper timing and uses a legal Up nudge after a second at rest, respecting the cooldown.

Scores are playability proxies. Player enjoyment, aesthetics and physical button feel require human playtesting.

Launch power is fixed; each seed varies release timing and reactive timing. Games stop at the time limit; survival at that limit is censored. The hand-weighted 0–100 proxy rewards variety, a timing advantage, progression, flow and readable speed; it is a design diagnostic, not a validated enjoyment rating. Flags remain visible even on high-scoring tables.

| Board | Proxy /100 | Reactive score | Random score | Median seconds | Flags |
| --- | ---: | ---: | ---: | ---: | --- |
| Neon Pursuit | 40.0 | 15000.0 | 23290.0 | 46.6 | reactive player did not reach a ramp; timing advantage not established by this player model; bank progression needs a human check |
| Orbital Robot | 86.5 | 112170.0 | 12870.0 | 120.0 |  |
| Shuttle Run | 30.2 | 28920.0 | 59700.0 | 120.0 | a seed had long scoring droughts; repetitive routes: inspect shot variety; reactive player did not reach a ramp; timing advantage not established by this player model; bank progression needs a human check |
| Storm Riders | 62.2 | 67560.0 | 9500.0 | 120.0 | a seed had long scoring droughts; repetitive routes: inspect shot variety; bank progression needs a human check |
| Solar Temple | 78.0 | 35640.0 | 14980.0 | 97.5 | repetitive routes: inspect shot variety; bank progression needs a human check |
| Midnight Manor | 82.8 | 95360.0 | 28280.0 | 120.0 | repetitive routes: inspect shot variety; bank progression needs a human check |
| Cosmic Carnival | 79.1 | 29610.0 | 11160.0 | 79.4 | repetitive routes: inspect shot variety |
| Dragon Keep | 60.0 | 28130.0 | 6910.0 | 111.4 | a seed had long scoring droughts; repetitive routes: inspect shot variety; reactive player did not reach a ramp; bank progression needs a human check |
| Buccaneer Bay | 62.1 | 12240.0 | 6430.0 | 67.1 | repetitive routes: inspect shot variety |
