#!/usr/bin/env python3
"""Isolated V7 R&D preview: procedural flow-field trace puzzle.

No external assets, network, paid APIs, or production imports. Uses only packages
already installed by render-daily.yml: OpenCV + NumPy.
"""
from pathlib import Path
import math
import cv2
import numpy as np

W, H, FPS, SECONDS = 540, 960, 24, 3
OUT = Path("outputs/rd_v7_flow_field_preview.mp4")


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def field(x, y, phase):
    # Cheap shader-like curl field: deterministic, smooth and CPU-only.
    a = (1.25 * math.sin(y * 0.010 + phase) +
         0.85 * math.cos(x * 0.013 - phase * 0.7) +
         0.45 * math.sin((x + y) * 0.006))
    return math.cos(a), math.sin(a)


def trace(seed, phase, steps=92):
    x, y = seed
    pts = []
    for _ in range(steps):
        pts.append((int(x), int(y)))
        vx, vy = field(x, y, phase)
        x += vx * 5.2
        y += vy * 5.2
        if x < 35 or x >= W - 35 or y < 155 or y >= H - 80:
            break
    return pts


def frame_at(i):
    t = i / float(FPS * SECONDS - 1)
    yy, xx = np.mgrid[0:H, 0:W]
    base = np.zeros((H, W, 3), np.uint8)
    base[..., 0] = np.clip(20 + 22 * yy / H, 0, 255).astype(np.uint8)
    base[..., 1] = np.clip(14 + 18 * xx / W, 0, 255).astype(np.uint8)
    base[..., 2] = 34

    phase = 0.65 * math.sin(t * math.tau)
    seeds = [(95, 300), (95, 455), (95, 610), (95, 765)]
    paths = [trace(s, phase) for s in seeds]
    odd = 2
    # One path gets a subtle field defect: the actual puzzle target.
    defect = []
    for j, p in enumerate(paths):
        q = list(p)
        if j == odd and len(q) > 45:
            for k in range(28, min(55, len(q))):
                px, py = q[k]
                q[k] = (px + int(18 * math.sin((k - 28) / 27.0 * math.pi)), py)
        defect.append(q)

    glow = np.zeros_like(base)
    for j, p in enumerate(defect):
        if len(p) < 2:
            continue
        cv2.polylines(glow, [np.array(p, np.int32)], False, (95, 190, 255), 12, cv2.LINE_AA)
    glow = cv2.GaussianBlur(glow, (0, 0), 10)
    base = cv2.addWeighted(base, 1.0, glow, 0.55, 0)

    for j, p in enumerate(defect):
        if len(p) < 2:
            continue
        cv2.polylines(base, [np.array(p, np.int32)], False, (220, 242, 255), 3, cv2.LINE_AA)
        head = min(len(p) - 1, int(ease(min(1.0, t * 1.35)) * (len(p) - 1)))
        cv2.circle(base, p[head], 8, (255, 255, 255), -1, cv2.LINE_AA)

    cv2.putText(base, "WHICH FLOW BREAKS?", (46, 92), cv2.FONT_HERSHEY_SIMPLEX, 1.05, (245,245,250), 2, cv2.LINE_AA)
    cv2.putText(base, "Trace the motion", (46, 132), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (165,175,205), 1, cv2.LINE_AA)

    if t > 0.76:
        alpha = ease((t - 0.76) / 0.18)
        overlay = base.copy()
        p = defect[odd][min(42, len(defect[odd]) - 1)]
        cv2.circle(overlay, p, 30, (70, 220, 255), 4, cv2.LINE_AA)
        cv2.putText(overlay, "3", (450, 850), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (70,220,255), 3, cv2.LINE_AA)
        base = cv2.addWeighted(base, 1.0-alpha, overlay, alpha, 0)
    return base


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(OUT), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    if not writer.isOpened():
        raise SystemExit("VideoWriter failed")
    for i in range(FPS * SECONDS):
        writer.write(frame_at(i))
    writer.release()
    cap = cv2.VideoCapture(str(OUT))
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    assert frames == FPS * SECONDS, frames
    assert (width, height) == (W, H), (width, height)
    assert OUT.stat().st_size > 10000, OUT.stat().st_size
    print("flow-field preview ok:", OUT, frames, (width, height))


if __name__ == "__main__":
    main()
