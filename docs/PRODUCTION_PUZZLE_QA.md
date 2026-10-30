# Production Puzzle QA Gate

Every V7 puzzle family must pass both **visual clarity** and **puzzle validity** before production integration or continued high-weight rotation.

## 1. Single-answer validity

- Exactly one intended answer must exist.
- The answer must be derivable from visible deterministic rules or trackable motion.
- Reveal must prove *why* the answer is correct, not merely circle it.
- If a generator cannot numerically validate its answer, it needs an explicit deterministic assertion/simulation test.

## 2. Non-triviality

Reject a variant when the answer is obvious from the first static frame unless the family is explicitly a reaction-speed challenge.

Examples that must fail:

- a signal/laser already has a visible unobstructed line to the core;
- the complete winning path is pre-drawn before reveal;
- a supposed moving difference is rotation-only on a rotation-invariant glyph;
- two or more candidates are effectively equivalent;
- the marked answer differs only below phone-size readability;
- a portal family reuses one fixed topology/chain/exit pattern across rounds.

## 3. Mobile perceptibility

- The meaningful difference must be visible at phone size.
- Motion differences must create a material position/speed/path/phase delta, not a cosmetic sub-pixel change.
- Dense comparison grids should prefer fewer/larger objects when the task depends on motion perception.
- Key puzzle objects must remain inside a safe central composition and retain adequate contrast.
- A numeric CI threshold is a floor, not proof of human readability; preview review is still required.

## 4. Reveal proof

Reveal should include at least one of:

- highlighted trajectory/path;
- side-by-side reference comparison;
- replay/ghost trail;
- collision/miss marker;
- explicit reason label such as `DIFFERENT PATH`, `WRONG BOUNCE`, `GATE FAILED`, or `3 REFLECTIONS`.

## 5. CI / smoke requirements

Before a renderer or quality change is promoted:

1. deterministic self-test/assertions pass;
2. solve and reveal preview frames decode successfully;
3. solve/reveal output differs materially;
4. alternate-seed preview is used where topology/route variety matters;
5. branch CI is green;
6. branch runs do not update `daily-latest` or trigger YouTube publishing.

## 6. Family-specific guard: `spot_difference_v2`

- Production uses a 4x4 comparison grid so symbols stay large enough on phones.
- The bad copy must follow a materially different positional path; rotation-only differences are forbidden.
- The anomaly must remain hidden on the opening frame, then become human-perceptible during the solve window.
- Across sampled solve times the positional delta must have a strong margin, not merely pass at one instant.
- Reveal must show the compared pair and motion ghosts/path evidence.

Legacy `spot_difference` is retired from weighted selection; runtime aliases it to the V2-safe renderer only for rollback/manual compatibility.

## 7. Family-specific guard: `portal_path_v2`

- Portal layout, chain order, start and exit must be seed-dependent.
- At least four warps are tracked per round.
- No complete source-to-destination route is drawn before reveal.
- CI must verify substantial chain diversity and multiple exit letters across seeds.
- Reveal shows the final breadcrumb chain only after the answer window closes.

Legacy `portal_path` is retired from weighted selection.

## 8. Family-specific guard: `signal_core_v2`

- No static candidate line may touch the core.
- All routes stop at a visible gap before the core so a still frame cannot reveal the answer.
- Each candidate faces three timed gates; exactly one survives all three.
- The three losing routes fail at different gate depths (early/mid/late) to avoid a repeated visual pattern.
- Only the surviving moving signal may cross the final gap near the end of the solve window.

Legacy `animated_maze` is retired from weighted selection because the old version exposed the winning path geometrically.

## 9. Family-specific guard: `laser_core`

- At least three meaningful reflection/interactions per candidate.
- Exactly one endpoint reaches the core.
- Wrong endpoints must miss by a clear margin.
- Do not pre-draw complete candidate routes during solve time.
- The winning route must be materially bent rather than a near-straight shot.

## 10. Reviewer rule

A successful render is **not** proof of a successful puzzle. CI that only checks file generation is insufficient. Reviewer & Integrator must reject visually ambiguous, repetitive, trivial, or unprovable puzzle logic even when encoding succeeds.

Current production QA version: `v3-human-perceptibility`.
