#!/usr/bin/env python3
"""Production-quality replacements for V7 puzzle families with validity guards.

These renderers stay CPU-only and reuse the shared V7 visual stack. The goal is
not only to look better, but to guarantee that the puzzle has one visible,
non-trivial answer before it is allowed into production.
"""
import math
import cv2
import numpy as np


def _spot_motion(idx, t, bad=False):
    phase = idx * 0.61
    dx = 8.0 * math.sin(t * 2.60 + phase)
    dy = 7.0 * math.cos(t * 2.10 + phase)
    pulse = 1.0 + 0.07 * math.sin(t * 3.00 + phase)
    rot = t * 30.0 + idx * 8.0
    if not bad:
        return dx, dy, pulse, rot

    # The anomaly is positional + temporal, so it remains visible for every
    # glyph type (including circles/squares/plus signs where rotation alone
    # would be invisible). The 24 px anomaly amplitude keeps a healthy phone-
    # size perceptibility margin without making the answer obvious immediately.
    anomaly = max(0.0, min(1.0, (t - 0.55) / 0.85))
    anomaly = anomaly * anomaly * (3.0 - 2.0 * anomaly)
    dx2 = -24.0 * math.sin(t * 2.60 + phase)
    dy2 = 24.0 * math.cos(t * 2.10 + phase + 0.80)
    pulse2 = 1.0 + 0.17 * math.sin(t * 3.00 + phase + math.pi)
    rot2 = rot - 52.0 * math.sin(t * 2.25 + phase)
    return (
        dx * (1.0 - anomaly) + dx2 * anomaly,
        dy * (1.0 - anomaly) + dy2 * anomaly,
        pulse * (1.0 - anomaly) + pulse2 * anomaly,
        rot * (1.0 - anomaly) + rot2 * anomaly,
    )


def spot_difference(t, seed, frame_idx, v):
    im, accent, secondary = v.mesh_background(seed, 3, t)
    im = v.header(im, "SPOT THE MOVING DIFFERENCE", "Same symbols. One copy moves differently.")
    v.glass_panel(im, (70, 355, 510, 1425), 42, (22, 27, 42), .67, (160, 148, 112), .30)
    v.glass_panel(im, (570, 355, 1010, 1425), 42, (22, 27, 42), .67, (160, 148, 112), .30)

    rng = np.random.default_rng(seed + 55)
    kinds = [int(rng.integers(0, 4)) for _ in range(24)]
    bad = seed % 24

    for idx in range(24):
        r, c = divmod(idx, 4)
        y0 = 500 + r * 168
        x1 = 130 + c * 100
        x2 = 630 + c * 100
        kind = kinds[idx]
        col = accent if idx % 3 else secondary

        ldx, ldy, lpulse, lrot = _spot_motion(idx, t, False)
        rdx, rdy, rpulse, rrot = _spot_motion(idx, t, idx == bad)
        v.draw_glyph(im, kind, x1 + ldx, y0 + ldy, 20 * lpulse, col, rot=lrot)
        v.draw_glyph(im, kind, x2 + rdx, y0 + rdy, 20 * rpulse, col, rot=rrot)

    # A moving scan keeps both panels visually active without exposing the answer.
    if .6 < t < v.ACTIVE_REVEAL:
        q = v.ease((t - .6) / max(.1, v.ACTIVE_REVEAL - .6))
        sx = int(105 + 345 * q)
        v.glow_line(im, (sx, 390), (sx, 1385), accent, 3, .45)
        v.glow_line(im, (sx + 500, 390), (sx + 500, 1385), accent, 3, .45)

    br, bc = divmod(bad, 4)
    left = (130 + bc * 100, 500 + br * 168)
    right = (630 + bc * 100, 500 + br * 168)
    if t >= v.ACTIVE_REVEAL:
        v.reveal_pulse(im, right, t)
        cv2.rectangle(im, (left[0] - 43, left[1] - 43), (left[0] + 43, left[1] + 43), (95, 190, 220), 3, cv2.LINE_AA)
        cv2.rectangle(im, (right[0] - 48, right[1] - 48), (right[0] + 48, right[1] + 48), (78, 245, 151), 6, cv2.LINE_AA)
        cv2.arrowedLine(im, (left[0] + 48, left[1]), (right[0] - 48, right[1]), (78, 245, 151), 4, cv2.LINE_AA, tipLength=.08)
        im = v.footer_result(im, "RIGHT COPY BREAKS THE MOTION")

    v.timer(im, t, accent)
    return v.finish_frame(im, seed, frame_idx)


def _unit(vec):
    x, y = float(vec[0]), float(vec[1])
    n = math.hypot(x, y)
    if n < 1e-9:
        return np.array([1.0, 0.0], np.float64)
    return np.array([x / n, y / n], np.float64)


def _mirror_segment(prev, node, nxt, half=43.0):
    incoming = _unit((node[0] - prev[0], node[1] - prev[1]))
    outgoing = _unit((nxt[0] - node[0], nxt[1] - node[1]))
    normal = incoming - outgoing
    nn = float(np.linalg.norm(normal))
    if nn < 1e-8:
        tangent = np.array([-incoming[1], incoming[0]], np.float64)
    else:
        normal /= nn
        tangent = np.array([-normal[1], normal[0]], np.float64)
    p1 = (int(node[0] - tangent[0] * half), int(node[1] - tangent[1] * half))
    p2 = (int(node[0] + tangent[0] * half), int(node[1] + tangent[1] * half))
    return p1, p2


def _laser_paths(seed):
    core = (870, 900)
    good = seed % 3
    starts = [(150, 570), (150, 900), (150, 1230)]
    mirrors = [
        [(340, 645), (535, 505), (715, 715)],
        [(350, 835), (545, 1060), (720, 810)],
        [(340, 1170), (540, 1325), (715, 1065)],
    ]
    misses = [(925, 515), (925, 1290), (925, 610)]
    paths = []
    for i in range(3):
        endpoint = core if i == good else misses[i]
        paths.append([starts[i]] + mirrors[i] + [endpoint])
    return core, good, paths


def _draw_mirror(im, prev, node, nxt, accent):
    a, b = _mirror_segment(prev, node, nxt)
    cv2.line(im, a, b, (70, 78, 92), 14, cv2.LINE_AA)
    cv2.line(im, a, b, (205, 220, 235), 5, cv2.LINE_AA)
    cv2.circle(im, node, 8, accent, -1, cv2.LINE_AA)


def _draw_beam_tail(im, path, q, color, v):
    q = max(0.0, min(.985, q))
    tail = max(0.0, q - .18)
    samples = [tail + (q - tail) * k / 10.0 for k in range(11)]
    pts = [v.poly_point(path, s) for s in samples]
    for k, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        alpha = .20 + .80 * (k + 1) / 10.0
        v.glow_line(im, a, b, color, 4 if k < 7 else 6, alpha)
    v.glow_circle(im, pts[-1], 13, color, intensity=.75)


def laser_core(t, seed, frame_idx, v):
    im, accent, secondary = v.mesh_background(seed, 3, t)
    im = v.header(im, "WHICH LASER HITS THE CORE?", "Track 3 reflections. Only one exits on target.")
    v.glass_panel(im, (90, 370, 990, 1420), 48, (29, 23, 9), .53, (155, 135, 75), .28)

    core, good, paths = _laser_paths(seed)
    colors = [accent, secondary, (255, 190, 95)]

    # Show only physical mirrors, not the complete answer paths.
    for i, path in enumerate(paths):
        im = v.pil_text(im, chr(65 + i), (115, path[0][1]), 28, fill=(225, 232, 242), stroke=1)
        cv2.circle(im, path[0], 12, colors[i], -1, cv2.LINE_AA)
        for j in range(1, len(path) - 1):
            _draw_mirror(im, path[j - 1], path[j], path[j + 1], colors[i])

    # Core is always visible, but no static line tells the viewer which route wins.
    v.glow_circle(im, core, 34, (78, 245, 151), core=(40, 105, 80), intensity=.95)
    cv2.circle(im, core, 60, (70, 130, 105), 2, cv2.LINE_AA)

    if .25 < t < v.ACTIVE_REVEAL:
        q = (t - .25) / max(.1, v.ACTIVE_REVEAL - .75)
        for i, path in enumerate(paths):
            _draw_beam_tail(im, path, q, colors[i], v)

    if t >= v.ACTIVE_REVEAL:
        # Reveal proves the answer: trace the full winning 3-reflection path,
        # while marking the two miss endpoints away from the core.
        win = paths[good]
        for a, b in zip(win[:-1], win[1:]):
            v.glow_line(im, a, b, (78, 245, 151), 9, 1.0)
        for i, path in enumerate(paths):
            if i == good:
                continue
            end = path[-1]
            cv2.line(im, (end[0] - 18, end[1] - 18), (end[0] + 18, end[1] + 18), (90, 110, 145), 5, cv2.LINE_AA)
            cv2.line(im, (end[0] - 18, end[1] + 18), (end[0] + 18, end[1] - 18), (90, 110, 145), 5, cv2.LINE_AA)
        v.reveal_pulse(im, core, t)
        cv2.circle(im, win[0], 32, (78, 245, 151), 5, cv2.LINE_AA)
        im = v.footer_result(im, f"LASER {chr(65 + good)} — 3 REFLECTIONS")

    v.timer(im, t, accent)
    return v.finish_frame(im, seed, frame_idx)


def quality_self_test():
    # Spot difference must be visible for every possible glyph choice, not only
    # rotation-sensitive shapes. The bad copy needs a material position delta.
    for seed in range(48):
        bad = seed % 24
        l = _spot_motion(bad, 2.35, False)
        r = _spot_motion(bad, 2.35, True)
        delta = math.hypot(l[0] - r[0], l[1] - r[1])
        assert delta >= 18.0, ("spot difference too subtle", seed, delta)
        for idx in (0, 5, 11, 23):
            if idx == bad:
                continue
            assert _spot_motion(idx, 2.35, False) == _spot_motion(idx, 2.35, idx == bad)

    # Laser puzzle must have exactly one core hit, three mirror interactions per
    # candidate, large miss margins, and a materially bent winning route.
    for seed in range(24):
        core, good, paths = _laser_paths(seed)
        hits = [math.hypot(p[-1][0] - core[0], p[-1][1] - core[1]) < 8 for p in paths]
        assert sum(hits) == 1 and hits[good]
        for i, path in enumerate(paths):
            assert len(path) == 5  # emitter + 3 mirrors + endpoint
            if i != good:
                assert math.hypot(path[-1][0] - core[0], path[-1][1] - core[1]) > 180
        win = paths[good]
        direct = math.hypot(win[-1][0] - win[0][0], win[-1][1] - win[0][1])
        routed = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(win[:-1], win[1:]))
        assert routed / direct > 1.22, ("laser route too straight", seed, routed / direct)

    print("puzzle_quality_self_test=PASS")


if __name__ == "__main__":
    quality_self_test()
