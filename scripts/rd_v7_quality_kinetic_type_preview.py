#!/usr/bin/env python3
from pathlib import Path
import time
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = Path("outputs/rd_v7_quality_kinetic_type")
OUT.mkdir(parents=True, exist_ok=True)
W,H,FPS,FRAMES = 540,960,24,72
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TITLE = "WHICH ONE BREAKS?"


def ease_out_back(x):
    x=np.clip(x,0.0,1.0); c1=1.70158; c3=c1+1
    return 1+c3*(x-1)**3+c1*(x-1)**2


def base():
    y=np.linspace(0,1,H,dtype=np.float32)[:,None,None]
    a=np.array((20,7,34),np.float32)[None,None,:]
    b=np.array((8,38,50),np.float32)[None,None,:]
    return (a*(1-y)+b*y+np.zeros((1,W,1),np.float32)).astype(np.uint8)


def text_layer(scale=1.0):
    canvas=Image.new("RGBA",(W,180),(0,0,0,0)); d=ImageDraw.Draw(canvas)
    f=ImageFont.truetype(FONT,max(20,int(39*scale)))
    box=d.textbbox((0,0),TITLE,font=f,stroke_width=2)
    tw=box[2]-box[0]; th=box[3]-box[1]
    d.text((W//2-tw//2,90-th//2),TITLE,font=f,fill=(246,249,255,255),stroke_width=2,stroke_fill=(8,10,20,255))
    return cv2.cvtColor(np.asarray(canvas),cv2.COLOR_RGBA2BGRA)


def composite(im,layer,y,alpha=1.0):
    h,w=layer.shape[:2]; y=int(y); x=0
    y1=max(0,y); y2=min(H,y+h)
    if y2<=y1:return im
    sy=y1-y; sy2=sy+(y2-y1)
    src=layer[sy:sy2].astype(np.float32)
    a=(src[:,:,3:4]/255.0)*alpha
    dst=im[y1:y2,x:x+w].astype(np.float32)
    im[y1:y2,x:x+w]=np.clip(src[:,:,:3]*a+dst*(1-a),0,255).astype(np.uint8)
    return im


def static_frame(t):
    im=base(); return composite(im,text_layer(1.0),35,1.0)


def kinetic_frame(t):
    im=base(); p=ease_out_back(min(1.0,t/0.42)); scale=.88+.12*p
    layer=text_layer(scale); y=35+(1-p)*22
    im=composite(im,layer,y,p)
    # restrained underline sweep: semantic emphasis, not decorative noise
    q=np.clip((t-.12)/.42,0,1); x1=105; x2=int(x1+330*q)
    if x2>x1:
        cv2.line(im,(x1,154),(x2,154),(242,104,255),3,cv2.LINE_AA)
    return im


def main():
    writer=cv2.VideoWriter(str(OUT/"before_after.mp4"),cv2.VideoWriter_fourcc(*"mp4v"),FPS,(W*2,H))
    assert writer.isOpened()
    a_ms=[]; b_ms=[]; deltas=[]
    for i in range(FRAMES):
        t=i/FPS
        s=time.perf_counter(); a=static_frame(t); a_ms.append((time.perf_counter()-s)*1000)
        s=time.perf_counter(); b=kinetic_frame(t); b_ms.append((time.perf_counter()-s)*1000)
        assert a.shape==(H,W,3) and b.shape==(H,W,3)
        deltas.append(float(np.mean(cv2.absdiff(a,b))))
        combo=np.concatenate([a,b],axis=1)
        cv2.putText(combo,"STATIC",(18,925),cv2.FONT_HERSHEY_SIMPLEX,.7,(220,225,235),2,cv2.LINE_AA)
        cv2.putText(combo,"KINETIC",(W+18,925),cv2.FONT_HERSHEY_SIMPLEX,.7,(220,225,235),2,cv2.LINE_AA)
        writer.write(combo)
    writer.release()
    cap=cv2.VideoCapture(str(OUT/"before_after.mp4")); n=0
    while True:
        ok,_=cap.read()
        if not ok: break
        n+=1
    cap.release()
    assert n==FRAMES
    assert (OUT/"before_after.mp4").stat().st_size>10000
    assert np.mean(deltas)>0.02
    cv2.imwrite(str(OUT/"before.png"),static_frame(.20)); cv2.imwrite(str(OUT/"after.png"),kinetic_frame(.20))
    print(f"static_ms_mean={np.mean(a_ms):.2f}")
    print(f"kinetic_ms_mean={np.mean(b_ms):.2f}")
    print(f"overhead_ms_mean={np.mean(b_ms)-np.mean(a_ms):.2f}")
    print(f"pixel_delta_mean={np.mean(deltas):.3f}")
    print(OUT/"before_after.mp4")

if __name__ == "__main__": main()
