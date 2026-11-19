# EGI V16 catalog proposal — HOLD, not approved

**Earliest available date:** 2026-11-21 (main catalog ends 2026-11-20). Two independent slots: 12:00 / 17:00 Europe/Istanbul.

This is **a review proposal, not an edit to production catalog**. Before adding these entries to `config/egi_episode_catalog.json`, reviewer must inspect complete 1080×1920 MP4 artifacts from [R&D PR #28](https://github.com/hammersnow/youtube-auto-render/pull/28), check mobile readability and causality, verify SHA/episode uniqueness and confirm renderer integration. No placeholder renderer IDs may be published.

Proposed entries:

```json
{
  "2026-11-21": [
    {
      "id": "egi-ssd-wear-leveling-v16",
      "category": "software",
      "renderer": "PENDING_REVIEW_NOT_PRODUCTION",
      "title": "Why Your SSD Moves Data Behind the Scenes #Shorts",
      "description": "How flash controllers remap logical addresses and distribute writes. Original simplified procedural illustration by EGI. #SSD #Storage #Technology #EGI",
      "tags": ["SSD", "flash memory", "wear leveling", "storage", "engineering", "shorts"]
    },
    {
      "id": "egi-heat-pipe-phase-change-v16",
      "category": "science",
      "renderer": "PENDING_REVIEW_NOT_PRODUCTION",
      "title": "How a Heat Pipe Moves Heat Without a Pump #Shorts",
      "description": "Evaporation, condensation and capillary return inside a sealed heat pipe. Original simplified procedural illustration by EGI. #Physics #Cooling #Engineering #EGI",
      "tags": ["heat pipe", "phase change", "thermal engineering", "science", "shorts"]
    }
  ]
}
```

Do not merge this proposal as production. The final catalog PR must replace placeholders with verified renderer registry keys, add the renderers to the EGI daily selector, pass cutover regression and obtain Reviewer approval. No uploads and no filler.
