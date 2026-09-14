#!/usr/bin/env python3
from pathlib import Path
import cv2
import numpy as np
import math
import wave
import subprocess
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

OUT = Path("outputs/latest")
OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS, DUR = 540, 960, 18, 8
TODAY = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d")
SEED = int(TODAY.replace("-", ""))
rng_global = np.random.default_rng(SEED)


def tone_file(path: Path, freq: float, seconds: int = DUR):
    sr = 16000
    t = np.arange(sr * seconds) / sr
    sig = 0.055*np.sin(2*np.pi*freq*t) + 0.018*np.sin(2*np.pi*(freq*1.5)*t)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((np.clip(sig, -1, 1) * 32767).astype("<i2").tobytes())


def encode_short(name, frame_fn, freq):
    raw = OUT / f"{name}_raw.mp4"
    wav = OUT / f"{name}.wav"
    final = OUT / f"{name}.mp4"
    writer = cv2.VideoWriter(str(raw), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    for i in range(FPS * DUR):
        writer.write(frame_fn(i / FPS, i))
    writer.release()
    tone_file(wav, freq)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-i", str(wav),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "64k", "-shortest", "-movflags", "+faststart", str(final)
    ], check=True)
    raw.unlink(missing_ok=True)
    wav.unlink(missing_ok=True)
    return final


yy, xx = np.mgrid[0:H, 0:W]
cx, cy = W/2, H/2
phase = (SEED % 360) * math.pi / 180.0


def mesmerizing(t, i):
    dx, dy = xx-cx, yy-cy
    r = np.sqrt(dx*dx + dy*dy)
    a = np.arctan2(dy, dx)
    v = (np.sin(a*7 + r*0.04 - t*3.4 + phase) + 1) / 2
    img = np.zeros((H, W, 3), np.uint8)
    img[..., 0] = (18 + 65*v).astype(np.uint8)
    img[..., 1] = (28 + 75*v).astype(np.uint8)
    img[..., 2] = (65 + 170*v).astype(np.uint8)
    cv2.putText(img, "CAN YOU LOOK AWAY?", (55, 835), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (245,245,245), 2, cv2.LINE_AA)
    return img


def optical(t, i):
    img = np.full((H, W, 3), 236, np.uint8)
    wobble = int(18*math.sin(t*2.1 + phase))
    for y in range(245, 670, 48):
        cv2.line(img, (50, y), (490, y), (45,45,55), 3)
    cv2.line(img, (165+wobble, 270), (165-wobble, 650), (225,70,70), 10, cv2.LINE_AA)
    cv2.line(img, (375-wobble, 270), (375+wobble, 650), (65,115,225), 10, cv2.LINE_AA)
    cv2.putText(img, "PARALLEL OR NOT?", (95, 790), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (25,25,35), 2, cv2.LINE_AA)
    cv2.putText(img, "Look twice.", (175, 835), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (60,60,70), 1, cv2.LINE_AA)
    return img

rain_seed = np.random.default_rng(SEED + 33)
rain_drops = [(int(rain_seed.integers(10, W-10)), float(rain_seed.uniform(0,H)), float(rain_seed.uniform(70,150)), int(rain_seed.integers(1,3))) for _ in range(55)]

def rain(t, i):
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = (42, 33, 26)
    for x0, y0, spd, th in rain_drops:
        y = int((y0 + spd*t) % H)
        cv2.line(img, (x0,y), (x0-3,y+18), (150,165,178), th, cv2.LINE_AA)
    cv2.putText(img, "8 SECONDS OF RAIN", (80, 825), cv2.FONT_HERSHEY_SIMPLEX, 0.76, (238,238,242), 2, cv2.LINE_AA)
    return img


def loop_orbit(t, i):
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = (27, 22, 39)
    for k in range(14):
        ang = t*1.55 + k*2*math.pi/14 + phase
        rad = 65 + (k % 5)*46
        x0 = int(cx + rad*math.cos(ang))
        y0 = int(cy + rad*math.sin(ang))
        rr = 11 + (k % 3)*4
        cv2.circle(img, (x0,y0), rr, (90+k*7, 80+k*5, 170+k*4), -1, cv2.LINE_AA)
    cv2.putText(img, "PERFECT LOOP", (145, 835), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (245,245,245), 2, cv2.LINE_AA)
    return img


def blink(t, i):
    img = np.full((H, W, 3), 22, np.uint8)
    n = max(0, 7-int(t))
    cv2.putText(img, "DON'T BLINK", (132, 315), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (240,240,240), 2, cv2.LINE_AA)
    cv2.putText(img, str(n), (210, 590), cv2.FONT_HERSHEY_SIMPLEX, 4.0, (245,245,245), 7, cv2.LINE_AA)
    if t >= 7:
        cv2.putText(img, "DID YOU MAKE IT?", (85, 760), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (100,220,130), 2, cv2.LINE_AA)
    return img


files = [
    encode_short("short_1_mesmerizing", mesmerizing, 160),
    encode_short("short_2_optical", optical, 205),
    encode_short("short_3_rain", rain, 130),
    encode_short("short_4_loop", loop_orbit, 180),
    encode_short("short_5_experiment", blink, 240),
]

# Long-form: lightweight 25-minute Pomodoro-style focus session.
long_file = OUT / "long_focus_25min.mp4"
font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
vf = (
    "drawbox=x=0:y=0:w=854:h=480:color=0x202632:t=fill,"
    "drawbox=x=205:y=105:w=444:h=270:color=0x10141c@0.88:t=fill,"
    f"drawtext=fontfile={font}:text='DEEP FOCUS':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=145,"
    f"drawtext=fontfile={font}:text='Study  •  Work  •  Read  •  Relax':fontcolor=0xd5dae2:fontsize=20:x=(w-text_w)/2:y=310,"
    f"drawtext=fontfile={font}:fontsize=62:fontcolor=white:x=(w-text_w)/2:y=215:"
    "text='%{eif\\:max(0\\,1500-t)/60\\:d\\:2}:%{eif\\:mod(max(0\\,1500-t)\\,60)\\:d\\:2}'"
)
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "lavfi", "-i", "color=c=0x202632:s=854x480:r=5:d=1500",
    "-f", "lavfi", "-i", "anoisesrc=color=pink:amplitude=0.045:r=16000:d=1500",
    "-vf", vf,
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "32", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "64k", "-shortest", "-movflags", "+faststart", str(long_file)
], check=True)

manifest = {
    "date": TODAY,
    "timezone": "Europe/Istanbul",
    "shorts": [
        {"file":"short_1_mesmerizing.mp4","title":"Can You Look Away? 🌀 #Shorts","text":"Try to keep your eyes on the center for 8 seconds. #mesmerizing #visual #shorts","tags":["mesmerizing","visual","satisfying","shorts"]},
        {"file":"short_2_optical.mp4","title":"Parallel or Not? Your Eyes May Lie 👀 #Shorts","text":"Are these lines really parallel? Look twice. #opticalillusion #shorts","tags":["optical illusion","visual trick","brain teaser","shorts"]},
        {"file":"short_3_rain.mp4","title":"8 Seconds of Rain 🌧️ #Shorts","text":"A tiny calm break for your feed. #rain #calm #relaxing #shorts","tags":["rain","calm","relaxing","ambient","shorts"]},
        {"file":"short_4_loop.mp4","title":"This Loop Never Ends 🔁 #Shorts","text":"A seamless hypnotic orbit loop. #loop #hypnotic #shorts","tags":["loop","hypnotic","mesmerizing","shorts"]},
        {"file":"short_5_experiment.mp4","title":"Don't Blink Until Zero 👁️ #Shorts","text":"Can you make it to zero without blinking? #challenge #reaction #shorts","tags":["challenge","reaction","visual test","shorts"]}
    ],
    "long": {
        "file":"long_focus_25min.mp4",
        "title":"25 Min Deep Focus Timer 🌧️ Study, Work & Read | Rain Ambience",
        "text":"25 minutes of distraction-free focus with a visible timer and soft rain-style ambience. Use it for studying, working, reading, writing, or quiet concentration.",
        "tags":["deep focus","focus timer","study with me","work with me","pomodoro","rain ambience","productivity","reading ambience"]
    }
}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
