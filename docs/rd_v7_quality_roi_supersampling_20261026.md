# V7 quality R&D — ROI 2x supersampling

Date: 2026-10-26

## Finding

The V7 engine already has mesh backgrounds, particles, glass panels, glow, selective bloom, vignette, grain, easing and family-specific trails. A useful next step is therefore not another full-frame decorative pass, but higher raster quality on the moving puzzle object itself.

This R&D renders only the selected puzzle ROI at 2x resolution and downsamples it with `cv2.INTER_AREA`. OpenCV documents `INTER_AREA` as suitable for image decimation. The approach keeps the 1080x1920 production frame unchanged and avoids the cost of full-frame 2x rendering.

## Expected benefit

- cleaner rotating polygon/orb/path edges on phone screens
- more stable thin neon outlines and specular edges
- better-looking glow cores without globally increasing render resolution
- reusable across families without changing puzzle logic

## Cost / compatibility

- CPU only
- OpenCV + NumPy only; no new dependency
- no external assets, paid API, GPU or copyrighted footage
- isolated preview only; production renderer/config untouched
- branch smoke runner already discovers `scripts/rd_v7_*_preview.py`

## Preview / assertions

`scripts/rd_v7_quality_supersampling_preview.py` renders a 72-frame 540x960 before/after comparison MP4, writes stills, asserts output dimensions/file size and requires a measurable pixel delta. It prints native and supersampled mean render time plus edge metrics for reviewer comparison.

## Promotion rule

Do not integrate globally unless branch CI succeeds and the measured per-frame overhead is acceptable. If accepted, implement as a reusable ROI helper and apply first to one family/object class rather than supersampling the whole frame.
