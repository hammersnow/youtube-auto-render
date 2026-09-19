#!/usr/bin/env python3
from pathlib import Path
import cv2, numpy as np, math, wave, subprocess, json
from datetime import datetime
from zoneinfo import ZoneInfo

OUT=Path('outputs/latest'); OUT.mkdir(parents=True,exist_ok=True)
W,H,FPS,D=540,960,18,8
DAY=datetime.now(ZoneInfo('Europe/Istanbul'))
SEED=int(DAY.strftime('%Y%m%d'))
rng=np.random.default_rng(SEED)

def audio(p,f):
    sr=16000;t=np.arange(sr*D)/sr;s=.04*np.sin(2*np.pi*f*t)+.012*np.sin(2*np.pi*f*1.5*t)
    with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((s*32767).astype('<i2').tobytes())
def txt(im,s,y,sc=.7,col=(245,245,245),th=2):
    (tw,_),_=cv2.getTextSize(s,cv2.FONT_HERSHEY_SIMPLEX,sc,th);cv2.putText(im,s,((W-tw)//2,y),cv2.FONT_HERSHEY_SIMPLEX,sc,col,th,cv2.LINE_AA)
def encode(name,fn,f):
    raw=OUT/(name+'_raw.mp4');wav=OUT/(name+'.wav');fin=OUT/(name+'.mp4');v=cv2.VideoWriter(str(raw),cv2.VideoWriter_fourcc(*'mp4v'),FPS,(W,H))
    for i in range(FPS*D):v.write(fn(i/FPS))
    v.release();audio(wav,f);subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(raw),'-i',str(wav),'-c:v','libx264','-preset','ultrafast','-crf','28','-pix_fmt','yuv420p','-c:a','aac','-b:a','64k','-shortest','-movflags','+faststart',str(fin)],check=True);raw.unlink(missing_ok=True);wav.unlink(missing_ok=True)

variant=SEED%7
# Same niche (visual puzzles), genuinely different daily puzzle mechanics.
def missing(t):
    im=np.full((H,W,3),28,np.uint8); n=6; miss=(SEED//3)%(n*n)
    for k in range(n*n):
        if k==miss:continue
        r,c=divmod(k,n);cv2.circle(im,(70+c*80,285+r*80),19,(80,180,235),-1,cv2.LINE_AA)
    txt(im,'WHICH SPOT IS MISSING?',170,.67)
    if t>6: r,c=divmod(miss,n);cv2.circle(im,(70+c*80,285+r*80),28,(70,230,120),4)
    txt(im,'Find it before the reveal.',850,.52,(220,220,220),1);return im
def count(t):
    im=np.full((H,W,3),242,np.uint8); target=3+variant
    for i in range(34):
        x=int(rng.integers(45,495));y=int(rng.integers(260,700));r=int(rng.integers(9,20));cv2.circle(im,(x,y),r,(65,110,220) if i%target else (225,90,75),-1)
    txt(im,'HOW MANY RED CIRCLES?',170,.67,(30,30,40));txt(im,'Count fast.',820,.58,(55,55,65),1);return im
def rotate(t):
    im=np.full((H,W,3),22,np.uint8);odd=SEED%12
    for i in range(12):
        a=2*math.pi*i/12;x=int(270+170*math.cos(a));y=int(470+170*math.sin(a));ang=a+(math.pi if i==odd else 0)
        p=np.array([[x+28*math.cos(ang),y+28*math.sin(ang)],[x+28*math.cos(ang+2.5),y+28*math.sin(ang+2.5)],[x+28*math.cos(ang-2.5),y+28*math.sin(ang-2.5)]],np.int32);cv2.fillPoly(im,[p],(235,175,70))
    txt(im,'WHICH ARROW IS WRONG?',180,.66); 
    if t>6: a=2*math.pi*odd/12;cv2.circle(im,(int(270+170*math.cos(a)),int(470+170*math.sin(a))),42,(70,220,120),4)
    return im
def match(t):
    im=np.full((H,W,3),240,np.uint8);shift=18+variant*3
    for y in range(300,650,70):
        for x in range(90,470,75):cv2.rectangle(im,(x,y),(x+35,y+35),(70,130,220),-1)
    cv2.rectangle(im,(90+shift,510),(125+shift,545),(225,80,80),-1)
    txt(im,'FIND THE ODD SQUARE',180,.68,(30,30,40));txt(im,'You have 6 seconds.',820,.55,(60,60,70),1);return im
def path(t):
    im=np.full((H,W,3),25,np.uint8);start=(70,480);end=(470,480);cv2.circle(im,start,22,(70,220,120),-1);cv2.circle(im,end,22,(80,100,235),-1)
    ys=[350,430,510,590];off=(variant-3)*8
    for j,y in enumerate(ys):cv2.line(im,(110,y),(430,y+off*((j%2)*2-1)),(210,210,220),7,cv2.LINE_AA)
    txt(im,'WHICH PATH REACHES BLUE?',180,.62);txt(im,'A  B  C  or  D?',820,.6,(220,220,225),1);return im

items=[('short_1_mesmerizing',missing,165,'Which Spot Is Missing? 👀 #Shorts'),('short_2_optical',count,205,'How Many Red Circles? 🔴 #Shorts'),('short_3_rain',rotate,185,'Which Arrow Is Wrong? 🧠 #Shorts'),('short_4_loop',match,220,'Find the Odd Square 👀 #Shorts'),('short_5_experiment',path,245,'Which Path Reaches Blue? #Shorts')]
for n,fn,f,_ in items:encode(n,fn,f)
# Update manifest after final renderer so publisher metadata matches actual videos.
mp=OUT/'manifest.json'
m=json.load(open(mp)) if mp.exists() else {}
m['date']=DAY.strftime('%Y-%m-%d');m['strategy']='daily-varied-visual-puzzles-v3'
m['shorts']=[{'file':n+'.mp4','title':title,'variant':variant} for n,_,_,title in items]
json.dump(m,open(mp,'w'),ensure_ascii=False,indent=2)
print('Five varied visual-puzzle Shorts rendered; variant',variant)
