# V7 quality R&D — restrained kinetic hook typography

Date: 2026-10-29

## Gap

The current V7 engine already has animated mesh lighting, parallax particles, glass panels, glow, selective bloom, vignette, grain, easing and family-specific trails. The shared `header()` itself is static, however. That leaves the first ~0.5 s visually weaker than the puzzle motion and misses a cheap cross-family hook-quality lever.

## Candidate

Animate only the short hook typography during the first ~0.42 s: small 0.88→1.0 scale settle with an ease-out-back curve, ~22 px vertical settle, opacity ramp and a restrained semantic underline sweep. After the entrance, text is fully static for readability.

This follows the current motion-design direction toward bold kinetic typography without adding decorative full-frame effects. It also preserves the project's requirement that the task be understandable immediately.

## Cost / compatibility

- CPU only
- Pillow + OpenCV + NumPy already present in V7
- no new dependency, GPU, paid API, network call or external asset
- DejaVu font already installed by the workflow
- production renderer/config untouched
- mobile readability preserved because motion ends in ~0.42 s and final type size/position stays stable

## Preview / smoke

`scripts/rd_v7_quality_kinetic_type_preview.py` generates a 72-frame, 540x960 side-by-side MP4 plus before/after PNGs. It asserts writer/decode success, exact frame count, dimensions, artifact size and measurable pixel delta, and prints static-vs-kinetic mean frame time.

## Promotion gate

Do not integrate globally until branch smoke CI is green and reviewer confirms the entrance remains readable at phone size. If promoted, implement as a reusable header entrance helper with motion disabled after the first ~0.42 s; do not animate long subtitles continuously.
