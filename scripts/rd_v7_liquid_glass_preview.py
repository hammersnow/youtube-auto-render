#!/usr/bin/env python3
"""Non-production V7 R&D preview: CPU-only liquid-glass lens/refraction.
Uses only NumPy + OpenCV already present in the render stack.
"""
from pathlib import Path
import cv2
import numpy as np

W,H=540,960
OUT=Path("outputs/rd-v7-liquid-glass")
OUT.mkdir(parents=True,exist_ok=True)

def background():
    y,x=np.mgrid[0:H,0:W].astype(np.float32)
    a=np.array([18,8,42],np.float32); b=np.array([70,30,8],np.float32)
    q=(y/H)[...,None]
    im=a*(1-q)+b*q
    for cx,cy,c in [(150,330,(240,80,255)),(410,610,(255,210,55))]:
        d=np.exp(-((x-cx)**2+(y-cy)**2)/(2*150**2))[...,None]
        im += d*np.array(c,np.float32)*.30
    return np.clip(im,0,255).astype(np.uint8)

def liquid_glass(im,cx,cy,rx,ry):
    y,x=np.mgrid[0:H,0:W].astype(np.float32)
    nx=(x-cx)/rx; ny=(y-cy)/ry; r2=nx*nx+ny*ny
    mask=np.clip(1-r2,0,1)
    # convex-lens style displacement; remap is CPU/GHA safe
    strength=24.0*mask*mask
    mx=(x-nx*strength).astype(np.float32)
    my=(y-ny*strength).astype(np.float32)
    refr=cv2.remap(im,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)
    soft=cv2.GaussianBlur(mask,(0,0),1.4)[...,None]
    out=(im.astype(np.float32)*(1-soft*.82)+refr.astype(np.float32)*(soft*.82))
    # subtle frosted interior + specular rim
    blur=cv2.GaussianBlur(refr,(0,0),3.0)
    out=out*(1-soft*.10)+blur.astype(np.float32)*(soft*.10)
    rim=np.clip((mask>0).astype(np.float32)-cv2.erode((mask>0).astype(np.float32),np.ones((7,7),np.uint8)),0,1)[...,None]
    out += rim*70
    hi=np.exp(-(((nx+.35)/.45)**2+((ny+.35)/.22)**2)*3.0)[...,None]*soft
    out += hi*55
    return np.clip(out,0,255).astype(np.uint8)

im=background()
im=liquid_glass(im,W//2,H//2,205,285)
cv2.putText(im,"V7 LIQUID GLASS R&D",(48,110),cv2.FONT_HERSHEY_SIMPLEX,.82,(245,245,255),2,cv2.LINE_AA)
cv2.putText(im,"CPU-only / OpenCV remap",(72,845),cv2.FONT_HERSHEY_SIMPLEX,.58,(220,225,245),1,cv2.LINE_AA)
out=OUT/"preview.png"
assert cv2.imwrite(str(out),im)
assert im.shape==(H,W,3) and im.dtype==np.uint8
print(out)
