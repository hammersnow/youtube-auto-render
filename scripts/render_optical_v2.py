#!/usr/bin/env python3
from pathlib import Path
import cv2, numpy as np, math, wave, subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

OUT=Path('outputs/latest'); OUT.mkdir(parents=True,exist_ok=True)
W,H,FPS,D=540,960,18,8
SEED=int(datetime.now(ZoneInfo('Europe/Istanbul')).strftime('%Y%m%d'))
phase=(SEED%360)*math.pi/180

def audio(p,f):
    sr=16000; t=np.arange(sr*D)/sr
    s=.045*np.sin(2*np.pi*f*t)+.014*np.sin(2*np.pi*f*1.5*t)
    with wave.open(str(p),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((s*32767).astype('<i2').tobytes())

def text(im,s,y,scale=.72,col=(25,25,35),th=2):
    (tw,_),_=cv2.getTextSize(s,cv2.FONT_HERSHEY_SIMPLEX,scale,th)
    cv2.putText(im,s,((W-tw)//2,y),cv2.FONT_HERSHEY_SIMPLEX,scale,col,th,cv2.LINE_AA)

def encode(name,fn,freq):
    raw=OUT/(name+'_raw.mp4'); wav=OUT/(name+'.wav'); fin=OUT/(name+'.mp4')
    v=cv2.VideoWriter(str(raw),cv2.VideoWriter_fourcc(*'mp4v'),FPS,(W,H))
    for i in range(FPS*D): v.write(fn(i/FPS))
    v.release(); audio(wav,freq)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(raw),'-i',str(wav),'-c:v','libx264','-preset','ultrafast','-crf','28','-pix_fmt','yuv420p','-c:a','aac','-b:a','64k','-shortest','-movflags','+faststart',str(fin)],check=True)
    raw.unlink(missing_ok=True); wav.unlink(missing_ok=True)

def circles(t):
    im=np.full((H,W,3),240,np.uint8)
    for idx,(cx,cy) in enumerate([(165,430),(375,430)]):
        rr=42 if idx==0 else 18
        for k in range(8):
            a=2*math.pi*k/8+.08*math.sin(t+phase); x=int(cx+92*math.cos(a)); y=int(cy+92*math.sin(a)); cv2.circle(im,(x,y),rr,(55,65,85),-1,cv2.LINE_AA)
        cv2.circle(im,(cx,cy),34,(85,145,225),-1,cv2.LINE_AA)
    text(im,'WHICH CENTER IS BIGGER?',760,.70); text(im,'A or B?',820,.62,(70,70,80),2); return im

def parallel(t):
    im=np.full((H,W,3),238,np.uint8); w=int(14*math.sin(t*2+phase))
    for y in range(250,670,45): cv2.line(im,(55,y),(485,y),(55,55,65),2)
    cv2.line(im,(170+w,270),(170-w,650),(220,70,75),9,cv2.LINE_AA); cv2.line(im,(370-w,270),(370+w,650),(65,110,225),9,cv2.LINE_AA)
    text(im,'ARE THESE LINES PARALLEL?',775,.66); text(im,'Look again.',830,.55,(70,70,80),1); return im

def length(t):
    im=np.full((H,W,3),245,np.uint8); x1,x2=130,410; d=48
    for y in [390,555]: cv2.line(im,(x1,y),(x2,y),(40,40,50),8,cv2.LINE_AA)
    for x,y,s in [(x1,390,1),(x2,390,-1),(x1,555,-1),(x2,555,1)]:
        cv2.line(im,(x,y),(x+s*d,y-d),(70,120,220),7,cv2.LINE_AA); cv2.line(im,(x,y),(x+s*d,y+d),(70,120,220),7,cv2.LINE_AA)
    text(im,'WHICH LINE IS LONGER?',760,.72); text(im,'Top or bottom?',820,.55,(70,70,80),1); return im

def bright(t):
    im=np.full((H,W,3),230,np.uint8); cv2.rectangle(im,(45,260),(255,650),(45,45,55),-1); cv2.rectangle(im,(285,260),(495,650),(220,220,225),-1)
    r=58+int(2*math.sin(t*2+phase)); cv2.circle(im,(150,455),r,(130,130,140),-1,cv2.LINE_AA); cv2.circle(im,(390,455),r,(130,130,140),-1,cv2.LINE_AA)
    text(im,'WHICH CIRCLE IS BRIGHTER?',760,.66); text(im,'Left or right?',820,.55,(60,60,70),1); return im

def odd(t):
    im=np.full((H,W,3),24,np.uint8); rows,cols=5,4; ox,oy=105,280; dx,dy=110,105; rr=SEED%rows; cc=(SEED//7)%cols
    for r in range(rows):
        for c in range(cols):
            col=(85,185,230) if (r,c)==(rr,cc) else (85,155,230); cv2.circle(im,(ox+c*dx,oy+r*dy),28,col,-1,cv2.LINE_AA)
    text(im,'FIND THE DIFFERENT ONE',185,.72,(245,245,245),2)
    if t>6.2: cv2.circle(im,(ox+cc*dx,oy+rr*dy),42,(80,225,120),4,cv2.LINE_AA)
    text(im,'Before time runs out.',850,.52,(220,220,225),1); return im

encode('short_1_mesmerizing',circles,165)
encode('short_2_optical',parallel,205)
encode('short_3_rain',length,185)
encode('short_4_loop',bright,220)
encode('short_5_experiment',odd,245)
print('Optical illusion winner-family Shorts rendered.')

# Daily render trigger: 2026-09-16 Europe/Istanbul
