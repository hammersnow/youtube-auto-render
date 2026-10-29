# Production Puzzle QA Gate

Every V7 puzzle family must pass both **visual clarity** and **puzzle validity** before production integration or continued high-weight rotation.

## 1. Single-answer validity

- Exactly one intended answer must exist.
- The answer must be derivable from visible deterministic rules.
- Reveal must prove *why* the answer is correct, not merely circle it.
- If a generator cannot numerically validate its answer, it needs an explicit deterministic assertion/simulation test.

## 2. Non-triviality

Reject a variant when the answer is obvious from the first static frame unless the family is explicitly a reaction-speed challenge.

Examples that must fail:

- a laser already has a visible unobstructed line to the core;
- the complete winning path is pre-drawn before reveal;
- a supposed moving difference is rotation-only on a rotation-invariant glyph;
- two or more candidates are effectively equivalent;
- the marked answer differs only below phone-size readability.

## 3. Mobile perceptibility

- The meaningful difference must be visible at phone size.
- Motion differences should create a material position/speed/path/phase delta, not a cosmetic sub-pixel change.
- Key puzzle objects must remain inside a safe central composition and retain adequate contrast.

## 4. Reveal proof

Reveal should include at least one of:

- highlighted trajectory/path;
- side-by-side reference comparison;
- replay/ghost trail;
- collision/miss marker;
- explicit reason label such as `OPPOSITE MOTION`, `WRONG BOUNCE`, or `3 REFLECTIONS`.

## 5. CI / smoke requirements

Before a renderer or quality change is promoted:

1. deterministic self-test/assertions pass;
2. solve and reveal preview frames decode successfully;
3. the solve/reveal output differs materially;
4. branch CI is green;
5. branch runs do not update `daily-latest` or trigger YouTube publishing.

## 6. Family-specific guard: `spot_difference`

The anomaly must remain visible regardless of glyph type. Do not depend solely on rotation because circles, axis-aligned squares and plus signs can make rotation visually meaningless. Prefer positional, temporal, path, speed or phase differences and require a numerical motion delta.

## 7. Family-specific guard: `laser_core`

- At least three meaningful reflection/interactions per candidate.
- Exactly one endpoint reaches the core.
- Wrong endpoints must miss by a clear margin.
- Do not pre-draw complete candidate routes during solve time.
- The winning route must be materially bent rather than a near-straight shot.

## 8. Reviewer rule

A successful render is **not** proof of a successful puzzle. CI that only checks file generation is insufficient. Reviewer & Integrator must reject visually ambiguous, trivial, or unprovable puzzle logic even when encoding succeeds.
