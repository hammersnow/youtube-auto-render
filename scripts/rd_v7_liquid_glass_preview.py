#!/usr/bin/env python3
"""Non-production V7 R&D: animated CPU liquid-glass/refraction smoke preview."""
from pathlib import Path
import math
import time
import cv2
import numpy as np

W, H = 540, 960
FPS, SECONDS = 24, 2.5
FRAMES = int(FPS * SECONDS)
RX, RY = 155, 205
OUT = Path("outputs/rd-v7-liquid-glass")
OUT.mkdir(parents=True, exist_ok=True)

# Precompute the displacement/masks once. Only the lens ROI is remapped per frame.
yy, xx = np.mgrid[-RY:RY+1, -RX:RX+1].astype(np.float32)
nx, ny = xx / RX, yy / RY
r2 = nx * nx + ny * ny
mask = np.clip(1.0 - r2, 0.0, 1.0).astype(np.float32)
soft = cv2.GaussianBlur(mask, (0, 0), 1.4)[..., None]
strength = 28.0 * mask * mask
MAP_X = (xx + RX - nx * strength).astype(np.float32)
MAP_Y = (yy + RY - ny * strength).astype(np.float32)
RIM = np.clip(
    (mask > 0).astype(np.float32)
    - cv2.erode((mask > 0).astype(np.float32), np.ones((7, 7), np.uint8)),
    0, 1,
)[..., None]
HIGHLIGHT = (
    np.exp(-(((nx + .35) / .45) ** 2 + ((ny + .35) / .22) ** 2) * 3.0)[..., None]
    * soft
)


def background():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    a = np.array([18, 8, 42], np.float32)
    b = np.array([70, 30, 8], np.float32)
    q = (y / H)[..., None]
    im = a * (1 - q) + b * q
    for cx, cy, color in [(150, 330, (240, 80, 255)), (410, 610, (255, 210, 55))]:
        d = np.exp(-((x-cx)**2 + (y-cy)**2) / (2 * 150**2))[..., None]
        im += d * np.array(color, np.float32) * .30
    im = np.clip(im, 0, 255).astype(np.uint8)

    # High-frequency geometry makes displacement/refraction visually unambiguous.
    for y0 in range(180, 790, 44):
        cv2.line(im, (45, y0), (495, y0), (150, 150, 210), 2, cv2.LINE_AA)
    for x0 in range(65, 500, 55):
        cv2.line(im, (x0, 180), (x0, 790), (100, 115, 180), 1, cv2.LINE_AA)
    for i, (sx, sy) in enumerate([(130, 350), (270, 480), (390, 620), (170, 700)]):
        cv2.circle(im, (sx, sy), 24, (235, 225, 80), 3, cv2.LINE_AA)
        cv2.putText(im, chr(65+i), (sx-9, sy+9), cv2.FONT_HERSHEY_SIMPLEX,
                    .8, (245, 245, 255), 2, cv2.LINE_AA)
    path = np.array([[85, 590], [190, 520], [300, 675], [455, 540]], np.int32)
    cv2.polylines(im, [path], False, (80, 245, 230), 5, cv2.LINE_AA)
    cv2.putText(im, "FOLLOW THE PATH", (92, 135), cv2.FONT_HERSHEY_SIMPLEX,
                .72, (245, 245, 255), 2, cv2.LINE_AA)
    return im


def liquid_glass_roi(im, cx, cy):
    # Motion bounds guarantee a complete fixed-size ROI: no full-frame remap.
    x0, y0 = cx - RX, cy - RY
    x1, y1 = cx + RX + 1, cy + RY + 1
    roi = im[y0:y1, x0:x1]
    assert roi.shape[:2] == MAP_X.shape

    refr = cv2.remap(roi, MAP_X, MAP_Y, cv2.INTER_CUBIC,
                     borderMode=cv2.BORDER_REFLECT_101)
    out = roi.astype(np.float32) * (1-soft*.80) + refr.astype(np.float32) * (soft*.80)
    blur = cv2.GaussianBlur(refr, (0, 0), 2.2)
    out = out * (1-soft*.08) + blur.astype(np.float32) * (soft*.08)
    out += RIM * 75 + HIGHLIGHT * 65

    result = im.copy()
    result[y0:y1, x0:x1] = np.clip(out, 0, 255).astype(np.uint8)
    return result


def frame_at(i, base):
    p = i / float(FRAMES - 1)
    # Smooth closed path; first/last composition nearly loops.
    cx = int(190 + 160 * (.5 - .5 * math.cos(2 * math.pi * p)))
    cy = int(470 + 80 * math.sin(2 * math.pi * p))
    return liquid_glass_roi(base, cx, cy)


base = background()
png = OUT / "preview.png"
mp4 = OUT / "preview.mp4"
first = frame_at(0, base)
assert cv2.imwrite(str(png), first)

writer = cv2.VideoWriter(str(mp4), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
assert writer.isOpened(), "OpenCV MP4 writer unavailable"
t0 = time.perf_counter()
for i in range(FRAMES):
    writer.write(frame_at(i, base))
writer.release()
elapsed = time.perf_counter() - t0

# Smoke assertions: both artifacts exist and MP4 decodes to expected dimensions/frame count.
assert png.exists() and png.stat().st_size > 1000
assert mp4.exists() and mp4.stat().st_size > 1000
cap = cv2.VideoCapture(str(mp4))
assert cap.isOpened()
assert int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) == W
assert int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) == H
assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) == FRAMES
ok, decoded = cap.read()
cap.release()
assert ok and decoded is not None and decoded.shape == (H, W, 3)

print(png)
print(mp4)
print("render_seconds=%.3f ms_per_frame=%.2f frames=%d" %
      (elapsed, elapsed * 1000.0 / FRAMES, FRAMES))
