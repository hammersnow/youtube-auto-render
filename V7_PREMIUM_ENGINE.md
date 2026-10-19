# YouTube Shorts Premium Motion V7

## Goal

V7 shifts the channel from high-volume primitive puzzle renders to three higher-quality Shorts per day. The system remains fully procedural and free: Python, OpenCV, NumPy, Pillow, FFmpeg, GitHub Actions, YouTube Data API and YouTube Analytics API only.

## Daily strategy

- 3 Shorts/day
- 2 proven families + 1 experimental family
- Istanbul target slots: 10:00, 15:00, 17:00
- Daily family order rotates so family and time slot are not permanently coupled
- Typical duration: 9.3–9.6 s
- Reveal: 7.0–7.25 s
- 1080x1920, 30 FPS
- H.264 High Profile, `libx264 -preset slow -crf 18`
- AAC 128 kbps stereo

## Proven pool

- `wrong_motion`
- `animated_maze`
- `memory_shuffle`
- `spot_difference`

These were retained because previous YouTube Analytics showed stronger reach and/or replay/retention than the weak families.

## Experimental pool

- `physics_error`
- `portal_path`
- `laser_core`

One experimental family is included per day so new concepts can be evaluated without sacrificing the majority of the daily inventory.

## V7 visual stack

The renderer in `scripts/render_premium_v7.py` adds:

- animated mesh-gradient lighting
- depth/parallax bokeh particles
- translucent glass panels
- bloom and neon glow
- motion trails
- anti-aliased geometry
- DejaVu/Pillow typography instead of Hershey-only text
- auto-fit title safe area
- reveal shockwaves
- vignette
- procedural film grain
- procedural stereo ambience, ticks and reveal chime

No paid generative-video service is required.

## Reliability changes

- obsolete render runs are cancelled when a newer build starts
- daily release is validated for `strategy=premium-motion-v7`
- publisher downloads filenames dynamically from the manifest
- publisher accepts adaptive short counts, with V7 currently enforcing 3
- old release assets are removed before the V7 release is uploaded, avoiding stale video files

## Quality validation

Local validation performed before repository integration:

- Python compile check
- solve/reveal preview frames at 1080x1920
- long-title safe-area fix after visual review
- real H.264/AAC smoke encode
- ffprobe verification: 1080x1920, 30 FPS, yuv420p, H.264 + AAC

GitHub Actions is the production validation environment before merging V7 to `main`.
