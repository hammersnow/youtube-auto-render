# V7 R&D — Flow-field trace puzzle (2026-10-22)

## Finding
A procedural **flow-field trace / find-the-broken-stream** family combines a puzzle task with satisfying continuous motion. It is materially different from current `wrong_motion`, `animated_maze`, `memory_shuffle`, `spot_difference`, `physics_error`, `portal_path`, and `laser_core` families.

## Why test it
- YouTube's Culture & Trends team reported 60M+ views for Puzzle Box-related videos in H1 2025, supporting continued puzzle demand.
- Adobe's 2026 design trend material emphasizes tactile/sensory motion, playful distortion and immersive visuals.
- Current motion-design tooling continues toward vector/parametric motion and richer motion typography.
- The mechanism has an immediate question, continuous eye-tracking, a reveal, and naturally loops.

## Implementation
`scripts/rd_v7_flow_field_preview.py` is intentionally isolated from production. It uses only NumPy + OpenCV already present in the GitHub Actions render image. The vector field is analytic (sin/cos), so no shader/GPU dependency exists. Glow is an OpenCV Gaussian blur pass. No external assets, fonts, network calls, paid APIs, model credits, or copyrighted media are used.

## License / CI
No new package is introduced. NumPy is BSD-3-Clause; OpenCV is Apache-2.0. The repository workflow already installs `python3-opencv` and `python3-numpy` on `ubuntu-latest`, and the existing branch smoke-test glob `scripts/rd_v7_*_preview.py` will execute this preview on branch pushes.

## Promotion gate
Do not add to `strategy_v7.json` yet. First require successful branch smoke test plus visual review. If promoted later, introduce it only as an experiment family and measure viewed-vs-swiped, retention/completion, replay behavior and engagement against current experiment families.
