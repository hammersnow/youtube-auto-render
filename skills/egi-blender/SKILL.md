---
name: egi-blender-kokoro-pilot
description: Source-pinned 3D mechanism and natural narration R&D reference; no production publication.
---

# Blender + Kokoro pilot

Use EGI project memory and original EGI skill pack (PR #35, commit 513dabba0f0f29339fb2f76fc0a4087371e3f881). Compare against Pillow and Manim prototypes. This branch is not a new publication episode.

Read vendor Blender core, hard-surface, PBR, lighting, animation, rendering and asset QA as relevant. Simulation is reference only: no validated electrical or vehicle simulation is claimed. Upstream skills target Blender 5.2+; pilot uses Ubuntu's Blender package and deliberately uses older-compatible APIs. Do not execute upstream scripts or assume linked resources are vendored. Keep source-pinned docs and licenses. For any missing references inspect exact upstream revision first.

Use original procedural geometry, bevels, material distinctions, connected objects, no copied assets, light rig and continuous framing. Render pilot on CPU with Cycles. Native resolution 540x960 at 12 fps, encoded at 1080x1920/24 fps by scaling and frame duplication to reduce initial cloud cost. This is explicitly a lower-native-resolution comparison, not production quality. Measure runtime and peak RSS. Do not upgrade production based on this pilot.

Kokoro 0.9.4, CPU PyTorch, af_heart, 24kHz, downloaded open weights from hexgrad/Kokoro-82M. Model repository/license reference: https://huggingface.co/hexgrad/Kokoro-82M ; software source https://github.com/hexgrad/kokoro/tree/dfb907a02bba8152ca444717ca5d78747ccb4bec . Voice quality and rights review still required before publishing. No commercial API or payment credentials.

Event timing: 0–3 wheels; 3–6 generator; 6–10 three-phase AC; 10–13 power electronics; 13–16 recovered energy. Animated signals and charge indicators are illustrative, not numerical electrical data. Source, geometry checks, blend, narration, render timings, actual MP4, frame samples and ffprobe in artifact. Full motion and audio review required; decode and sampled frames are not approval. Existing separate catalog, no-repeat and publication gates remain. No merge, publish or runtime dependency changes to main.
