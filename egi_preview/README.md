# EGI V16 · isolated render preview (NO PUBLISH)

This directory stages the **approved EGI V16 visual language** without changing V7 production or publishing. This is not the production migration; `strategy_egi_v16_preview.json` is not loaded by production. Previous V8 PR #25 is a historical preflight plan and has not been merged.

## Current proof-of-concept

- **Software:** URL → DNS → TCP handshake → TLS → HTTP → distinct HTML / CSS / JavaScript files → browser structure, styling and behavior. Continuous original procedural 2.5D scene, no storyboard cuts or embedded reference videos.
- **Technology:** V15-grade wireless charging with an exclusive V16 transient event schedule; further visual enrichment pending owner review.
- **Mechanics:** existing separately reviewed engine V8.8, turbo V8.9 and intercooler V9.1 pilots remain outside this branch until separately migrated.
- Transient event cards have a single owner/time schedule; persistent state (lock, received files, charge progress) is independent of cards.
- Semantic files and cause/effect animations are **not** replaced with an undifferentiated `RESOURCES` bubble.

## Run locally

Python 3.10+; FFmpeg, NumPy, Pillow, and fonts (Inter preferred, DejaVu fallback). No paid service, YouTube credentials or private source footage required.

```bash
python3 -m pip install numpy pillow
export EGI_OUTPUT_DIR="$PWD/outputs/egi_v16"
python3 egi_preview/qa_v16.py
python3 egi_preview/egi_v16_rich_resources.py --mode software --preview
python3 egi_preview/egi_v16_rich_resources.py --mode software --seconds 2
# Full pilot (takes longer):
python3 egi_preview/egi_v16_rich_resources.py --mode software
```

## CI and safety boundary

`egi-v16-preview.yml` runs on this preview branch only. It has `contents: read` permissions, no OAuth secrets, no release, no `daily-latest`, no YouTube upload, no publisher dispatch, and no production file changes. It validates temporal exclusivity, semantic resources, sample frames, codecs, duration, storyboard and an original full-length MP4, then stores them as a 7-day **workflow artifact**.

**Never merge this branch or point the existing publisher at its output without separate review and explicit owner approval.** Production requires strategy/manifest migration, QA on all 3 categories, safe areas, new upload idempotency review, and retirement of scheduled V7 jobs in one reviewed change. Existing videos/subscribers are preserved.
