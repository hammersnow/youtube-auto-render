#!/usr/bin/env python3
from pathlib import Path
import time
import cv2
import numpy as np

OUT = Path("outputs/rd_v7_quality_supersampling")
OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS, FRAMES = 540, 960, 24, 72
ROI = (90, 270, 450, 690)


def scene_base(t):
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top = np.array((18, 10, 38), np.float32)[None, None, :]
    bot = np.array((8, 38, 50), np.float32)[None, None, :]
    im = (top * (1-y) + bot * y + np.zeros((1, W, 1), np.float32)).astype(np.uint8)
    for i in range(18):
        x = int((50 + i*37 + 18*np.sin(t*.8+i)) % W)
        yy = int(180 + ((i*71 + t*18) % 650))
        cv2.circle(im, (x, yy), 2 + i % 3, (80, 90, 120), -1, cv2.LINE_AA)
    return im


def draw_object(im, t, scale=1):
    h, w = im.shape[:2]
    cx, cy = w//2, h//2
    ang = t*2.1
    r = int(min(w,h)*.28)
    pts=[]
    for i in range(7):
        a=ang+i*2*np.pi/7
        rr=r*(1.0 if i%2==0 else .58)
        pts.append((int(cx+rr*np.cos(a)), int(cy+rr*np.sin(a))))
    pts=np.array(pts,np.int32)
    glow=np.zeros_like(im)
    cv2.polylines(glow,[pts],True,(255,160,55),max(2,10*scale),cv2.LINE_AA)
    glow=cv2.GaussianBlur(glow,(0,0),8*scale)
    im[:]=cv2.addWeighted(im,1.0,glow,.45,0)
    cv2.polylines(im,[pts],True,(255,210,90),max(1,3*scale),cv2.LINE_AA)
    for p in pts:
        cv2.circle(im,tuple(p),max(2,6*scale),(245,248,255),-1,cv2.LINE_AA)
    return im


def native_frame(t):
    im=scene_base(t)
    x1,y1,x2,y2=ROI
    roi=im[y1:y2,x1:x2].copy()
    draw_object(roi,t,1)
    im[y1:y2,x1:x2]=roi
    return im


def supersampled_frame(t):
    im=scene_base(t)
    x1,y1,x2,y2=ROI
    roi=im[y1:y2,x1:x2]
    hi=cv2.resize(roi,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
    draw_object(hi,t,2)
    lo=cv2.resize(hi,(x2-x1,y2-y1),interpolation=cv2.INTER_AREA)
    im[y1:y2,x1:x2]=lo
    return im


def edge_metric(im):
    x1,y1,x2,y2=ROI
    gray=cv2.cvtColor(im[y1:y2,x1:x2],cv2.COLOR_BGR2GRAY)
    lap=cv2.Laplacian(gray,cv2.CV_32F)
    return float(np.mean(np.abs(lap)))


def main():
    fourcc=cv2.VideoWriter_fourcc(*"mp4v")
    writer=cv2.VideoWriter(str(OUT/"before_after.mp4"),fourcc,FPS,(W*2,H))
    assert writer.isOpened(), "VideoWriter failed"
    native_ms=[]; ss_ms=[]; deltas=[]
    for i in range(FRAMES):
        t=i/FPS
        s=time.perf_counter(); a=native_frame(t); native_ms.append((time.perf_counter()-s)*1000)
        s=time.perf_counter(); b=supersampled_frame(t); ss_ms.append((time.perf_counter()-s)*1000)
        assert a.shape==(H,W,3) and b.shape==(H,W,3)
        deltas.append(float(np.mean(cv2.absdiff(a,b))))
        combo=np.concatenate([a,b],axis=1)
        cv2.putText(combo,"NATIVE",(22,55),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2,cv2.LINE_AA)
        cv2.putText(combo,"ROI 2X + AREA",(W+22,55),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2,cv2.LINE_AA)
        writer.write(combo)
    writer.release()
    assert (OUT/"before_after.mp4").stat().st_size > 10000
    assert np.mean(deltas) > 0.05, "Supersampling produced no measurable visual change"
    a=native_frame(.73); b=supersampled_frame(.73)
    cv2.imwrite(str(OUT/"before.png"),a); cv2.imwrite(str(OUT/"after.png"),b)
    print(f"native_ms_mean={np.mean(native_ms):.2f}")
    print(f"supersampled_ms_mean={np.mean(ss_ms):.2f}")
    print(f"overhead_ms_mean={np.mean(ss_ms)-np.mean(native_ms):.2f}")
    print(f"pixel_delta_mean={np.mean(deltas):.3f}")
    print(f"edge_metric_native={edge_metric(a):.3f}")
    print(f"edge_metric_supersampled={edge_metric(b):.3f}")
    print(OUT/"before_after.mp4")

if __name__ == "__main__":
    main()
