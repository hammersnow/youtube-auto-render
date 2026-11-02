# V7 R&D — laser topology diversity audit — 2026-11-02

## Production finding
`laser_core` passes the current single-answer/reflection guard, but `_laser_paths(seed)` keeps the same three starts and the same three mirror-node triplets for every seed. The seed only changes which candidate terminates at the core. This creates memorization/repetition risk even though the answer itself rotates.

The V2 families are materially better guarded: `spot_difference_v2` samples five solve-window times; `portal_path_v2` numerically requires >=20 chain signatures and >=5 exits; `signal_core_v2` prevents any static candidate endpoint from approaching the core.

## R&D candidate
`rd_v7_laser_topology_preview.py` prototypes seed-dependent laser geometry without touching production. It keeps exactly one core hit, three interaction nodes per candidate and large wrong-answer miss margins while varying vertical ordering, core Y and all three interaction-node Y positions.

Deterministic gate over 64 seeds:
- >=56 unique quantized topology signatures;
- all A/B/C winners represented;
- exactly one core hit per seed;
- every wrong endpoint >=125 px from core;
- two full-resolution-equivalent portrait solve previews plus a short MP4 artifact;
- no complete answer route drawn in solve preview.

## Cost / compatibility
OpenCV + NumPy only; already installed by the existing Ubuntu GitHub Actions workflow. No GPU, API, external asset, font download or new dependency. OpenCV 4.5+ is Apache-2.0; NumPy is BSD-3-Clause. Candidate is R&D-only and branch CI remains preview/smoke-only.

## Promotion rule
Do not wire this into production from this PR. Promote only after preview review confirms the randomized layouts remain traceable on a phone and do not create accidental overlaps. If promoted later, add topology-diversity assertions to the production `quality_self_test()` rather than relying on visual review alone.
