#!/usr/bin/env python3
"""Production V7 flow-field experiment. CPU-only OpenCV/NumPy; no external assets."""
import math
import cv2
import numpy as np


def _field(x, y, phase):
    a = (1.25 * math.sin(y * 0.005 + phase) +
         0.85 * math.cos(x * 0.0065 - phase * 0.7) +
         0.45 * math.sin((x + y) * 0.003))
    return math.cos(a), math.sin(a)


def _trace(seed, phase, steps=92):
    x, y = seed
    pts = []
    for _ in range(steps):
        pts.append((int(x), int(y)))
        vx, vy = _field(x, y, phase)
        x += vx * 10.4
        y += vy * 10.4
        if x < 70 or x >= 1010 or y < 310 or y >= 1760:
            break
    return pts


def render(t, seed, frame_idx, v):
    im, accent, secondary = v.mesh_background(seed, 1, t)
    im = v.header(im, "WHICH FLOW BREAKS?", "Trace the motion — one path bends against the field")
    v.glass_panel(im, (80, 330, 1000, 1460), 46, (12, 25, 40), .58, (95, 160, 190), .30)
    phase = 0.65 * math.sin((t / max(v.ACTIVE_DURATION, .1)) * math.tau)
    seeds = [(190, 560), (190, 790), (190, 1020), (190, 1250)]
    paths = [_trace(s, phase) for s in seeds]
    odd = seed % 4
    defect = []
    for j, p in enumerate(paths):
        q = list(p)
        if j == odd and len(q) > 45:
            for k in range(28, min(55, len(q))):
                px, py = q[k]
                q[k] = (px + int(36 * math.sin((k - 28) / 27.0 * math.pi)), py)
        defect.append(q)

    glow = np.zeros_like(im)
    for p in defect:
        if len(p) >= 2:
            cv2.polylines(glow, [np.array(p, np.int32)], False, accent, 24, cv2.LINE_AA)
    glow = cv2.GaussianBlur(glow, (0, 0), 18)
    im = cv2.addWeighted(im, 1.0, glow, .40, 0)

    solve_q = v.clamp((t - .25) / max(v.ACTIVE_REVEAL - .5, .1), 0, 1)
    for j, p in enumerate(defect):
        if len(p) < 2:
            continue
        cv2.polylines(im, [np.array(p, np.int32)], False, (220, 242, 255), 5, cv2.LINE_AA)
        head = min(len(p) - 1, int(v.ease(solve_q) * (len(p) - 1)))
        v.glow_circle(im, p[head], 14, accent if j % 2 == 0 else secondary, intensity=.55)
        im = v.pil_text(im, str(j + 1), (135, seeds[j][1]), 28, fill=(205, 216, 240), stroke=1)

    if t >= v.ACTIVE_REVEAL:
        p = defect[odd][min(42, len(defect[odd]) - 1)]
        v.reveal_pulse(im, p, t)
        cv2.circle(im, p, 64, (78, 245, 151), 6, cv2.LINE_AA)
        im = v.footer_result(im, "FLOW %d BREAKS THE FIELD" % (odd + 1))
    v.timer(im, t, accent)
    return v.finish_frame(im, seed, frame_idx)
