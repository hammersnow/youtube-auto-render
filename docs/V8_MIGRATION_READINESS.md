# V8 migration readiness — DRAFT / NO PUBLISH
Date: 2026-11-17
Repository: hammersnow/youtube-auto-render
Authority: owner approval required for launching V8

## Editorial direction
Retire visual-puzzle format from the **next approved V8 launch**, preserving all historical videos, upload records and rollback references. New promise: **See how it really works**. Two original English-language series:
- **Inside the Machine:** truthful 2.5D/3D cutaways; fuel-to-motion, turbochargers, differential, valves, hydraulics.
- **Physics in Motion:** physically consistent marble/ramp/chains; narrative uncertainty and satisfying resolution. Label stylized fiction where real physical behavior is not simulated.

## Output / schedules
Maximum **2 original Shorts/day**, not a production quota: fewer when quality is insufficient.
Pilot A: 26s four-stroke *spark-ignition gasoline engine* cutaway, 1080×1920, H.264/AAC. A refined V8.1 preview has been rendered locally and **not published**.
Pilot B: independent marble/physics prototype pending.
14-day first experiment target: 14 A + 14 B; rotate publication slots across formats. Do not compare raw total views across unequally aged Shorts.

## Mandatory quality gates
- Engineering model: piston TDC/BDC and slider-crank motion; 720° crank rotation per full four-stroke cycle; intake valve during intake, exhaust valve during exhaust; spark near end compression/start of power for this schematic.
- Clearly label simplified geometry and avoid claiming photorealistic 3D when video is 2.5D.
- Opening visual question within 1s; distinct progression; closing explanation; legible text at phone scale.
- Native 9:16 and H.264/AAC, no clipped safe areas or missing audio; sound-level check; original or licensed assets.
- At least two seed/episode variants; no near-duplicate loops or fake scientific claims.
- Reviewer checks playable MP4, full sequence, and user review before any production rollout.
- Existing uploaded puzzles preserved. Duplicate markers and daily-slot idempotency preserved.

## Release / publisher hard block
DO NOT modify `main`, `daily-latest`, `publish-youtube.yml`, current V7 schedule, or YouTube content on the basis of this draft PR.
DO NOT flip `publish_enabled` or attach `strategy_v8_preview.json` to a production renderer automatically.
Production transition needs an explicit owner **start** command after both pilots are reviewed. Then update renderer, manifest count=2, publisher count=2, health checks, and rollback as a single reviewed change. Confirm all production workflows skip branch smoke.
This PR MUST stay draft and must not auto-merge.

## Measurement plan
- Baseline from 2026-11-17 YouTube preflight: 25 videos, median 207 views, max 1180; only 2/25 >=1000. **Not age-matched 72h baseline**.
- Per video at 24/48/72h and 7d: chose-to-view, engaged views, average view duration/percentage, shares, gained subscribers. Preserve missing-metric flags.
- >=10 age-mature samples per series before selecting winner; control for publish slot and length.
- Proposed *test threshold* (not promise): median 72h engaged views >=2x comparable legacy baseline without a retention decline.
- Quality failures or misleading visuals block new uploads; do not force 2/day.

## Follow-on engineering tasks (not yet deployed)
1. Integrate portable V8.1 engine renderer and independently validated sound/caption mix on an isolated branch.
2. Produce and visually review the physics/marble pilot.
3. Build V8 manifest schema and 2-item publisher; add idempotency and rollback tests; branch CI without release/upload permissions.
4. Present both outputs to owner; only after explicit start approval perform production switch.
