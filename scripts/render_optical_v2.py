#!/usr/bin/env python3
from pathlib import Path
import cv2,numpy as np,math,wave,subprocess,json,hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
OUT=Path("outputs/latest"); OUT.mkdir(parents=True,exist_ok=True)
W,H,FPS,D=1080,1920,30,8
DAY=datetime.now(ZoneInfo("Europe/Istanbul")); SEED=int(DAY.strftime("%Y%m%d"))
FONT=cv2.FONT_HERSHEY_SIMPLEX

def text(im,s,y,sc=1.45,col=(245,245,245),th=3):
    (w,_),_=cv2.getTextSize(s,FONT,sc,th); cv2.putText(im,s,((W-w)//2,y),FONT,sc,col,th,cv2.LINE_AA)
def gradient(a,b):
    yy=np.linspace(0,1,H)[:,None,None]; A=np.array(a,float)[None,None,:]; B=np.array(b,float)[None,None,:]
    return (A*(1-yy)+B*yy+np.zeros((1,W,1))).clip(0,255).astype(np.uint8)
def timer_bar(im,t,col=(80,220,250)):
    if 1<=t<6:
        p=(t-1)/5; cv2.rectangle(im,(130,1630),(950,1650),(55,60,75),-1); cv2.rectangle(im,(130,1630),(130+int(820*(1-p)),1650),col,-1)
def ring(im,x,y,t):
    if 6<=t<7.5:
        r=65+int(12*math.sin((t-6)*10)); cv2.circle(im,(x,y),r,(70,245,120),10,cv2.LINE_AA)

def missing_dot(t,seed):
    im=gradient((14,18,34),(22,62,68)); text(im,"WHICH DOT IS MISSING?",210,1.25)
    rng=np.random.default_rng(seed); rows,cols=7,6; miss=seed%(rows*cols); mr,mc=divmod(miss,cols)
    for r in range(rows):
      for c in range(cols):
        if r*cols+c==miss: continue
        x=220+c*130; y=480+r*135; cv2.circle(im,(x,y),30,(235,205,80),-1,cv2.LINE_AA)
    if t>=6: cv2.circle(im,(220+mc*130,480+mr*135),30,(70,245,120),-1,cv2.LINE_AA)
    timer_bar(im,t,(90,235,180)); ring(im,220+mc*130,480+mr*135,t); return im

def count_shapes(t,seed):
    im=gradient((38,12,28),(15,36,62)); text(im,"HOW MANY BLUE CIRCLES?",205,1.12)
    rng=np.random.default_rng(seed); n=7+seed%6; pts=[]
    for i in range(34):
      x=int(rng.integers(100,980)); y=int(rng.integers(390,1450)); rad=int(rng.integers(22,38))
      if i<n: col=(245,155,55); pts.append((x,y))
      else: col=(80,105,235) if i%2 else (100,220,130)
      cv2.circle(im,(x,y),rad,col,-1,cv2.LINE_AA)
    timer_bar(im,t,(245,155,55))
    if t>=6: text(im,"ANSWER: %d"%n,1530,1.7,(80,245,120),4)
    return im

def path_choice(t,seed):
    im=gradient((8,28,28),(15,18,45)); text(im,"WHICH PATH REACHES GREEN?",205,1.05)
    ys=[570,780,990,1200]; good=seed%4
    for i,y in enumerate(ys):
      pts=np.array([[130,y],[340,y+(-70 if i%2 else 65)],[570,y+(50 if i%3 else -45)],[820,ys[good] if i==good else y+120]],np.int32)
      cv2.polylines(im,[pts],False,(220,225,235),10,cv2.LINE_AA); cv2.putText(im,chr(65+i),(80,y+15),FONT,1.1,(245,245,245),3,cv2.LINE_AA)
    cv2.circle(im,(900,ys[good]),42,(70,235,100),-1); timer_bar(im,t,(70,235,100))
    if t>=6: text(im,"PATH %s"%chr(65+good),1510,1.7,(70,245,120),4)
    return im

def hidden_digit(t,seed):
    im=gradient((24,16,42),(10,50,60)); target=str(2+seed%7); text(im,"FIND THE HIDDEN %s"%target,205,1.35)
    rng=np.random.default_rng(seed); rows,cols=9,7; idx=seed%(rows*cols); rr,cc=divmod(idx,cols)
    chars=["3","5","6","8","9"]; base=chars[seed%len(chars)]
    if base==target: base="3"
    for r in range(rows):
      for c in range(cols):
        s=target if (r,c)==(rr,cc) else base
        col=(130,150,165) if (r,c)!=(rr,cc) or t<6 else (70,245,120)
        cv2.putText(im,s,(145+c*120,430+r*115),FONT,1.45,col,3,cv2.LINE_AA)
    timer_bar(im,t,(180,110,245)); ring(im,170+cc*120,405+rr*115,t); return im

def symmetry(t,seed):
    im=gradient((42,25,8),(25,12,38)); text(im,"FIND THE BROKEN SYMMETRY",205,1.05)
    cx=540; rng=np.random.default_rng(seed); bad=seed%6
    for r in range(6):
      y=500+r*145; dx=120+(r%3)*70
      cv2.rectangle(im,(cx-dx-32,y-32),(cx-dx+32,y+32),(80,195,240),-1)
      off=35 if r==bad else 0
      cv2.rectangle(im,(cx+dx-32+off,y-32),(cx+dx+32+off,y+32),(80,195,240),-1)
    timer_bar(im,t,(240,180,70)); ring(im,cx+(120+(bad%3)*70)+35,500+bad*145,t); return im

def audio(p,f):
    sr=24000; tt=np.arange(sr*D)/sr; s=.028*np.sin(2*np.pi*f*tt)+.009*np.sin(2*np.pi*f*2*tt)
    with wave.open(str(p),"wb") as w: w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((s*32767).astype("<i2").tobytes())
def encode(name,fn,f,seed):
    raw=OUT/(name+"_raw.mp4"); wav=OUT/(name+".wav"); fin=OUT/(name+".mp4")
    v=cv2.VideoWriter(str(raw),cv2.VideoWriter_fourcc(*"mp4v"),FPS,(W,H))
    for i in range(FPS*D): v.write(fn(i/FPS,seed))
    v.release(); audio(wav,f)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(raw),"-i",str(wav),"-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p","-c:a","aac","-b:a","96k","-shortest","-movflags","+faststart",str(fin)],check=True)
    raw.unlink();wav.unlink(); return hashlib.sha256(fin.read_bytes()).hexdigest()

families=[
 ("missing_dot",missing_dot,"Which Dot Is Missing? 👀 #Shorts"),
 ("count_shapes",count_shapes,"How Many Blue Circles? 🔵 #Shorts"),
 ("path_choice",path_choice,"Which Path Reaches Green? 🧠 #Shorts"),
 ("hidden_digit",hidden_digit,"Can You Find the Hidden Number? 🔎 #Shorts"),
 ("symmetry",symmetry,"Find the Broken Symmetry 👀 #Shorts")]
names=["short_1_mesmerizing","short_2_optical","short_3_rain","short_4_loop","short_5_experiment"]
items=[]
for i,(fam,fn,title) in enumerate(families):
    local=SEED+i*7919; h=encode(names[i],fn,170+i*19,local)
    items.append({"file":names[i]+".mp4","title":title,"family":fam,"variant":"v5-%s"%local,"sha256":h,
      "description":"Solve the puzzle before the reveal. Comment your answer before time runs out. #visualpuzzle #brainteaser #shorts",
      "tags":["visual puzzle","brain teaser",fam.replace("_"," "),"shorts"]})
m={"date":DAY.strftime("%Y-%m-%d"),"strategy":"diversity-v5","resolution":"1080x1920","fps":30,"duration_sec":8,"shorts":items}
json.dump(m,open(OUT/"manifest.json","w"),ensure_ascii=False,indent=2)
print("Diversity V5 rendered:",[(x["family"],x["sha256"][:10]) for x in items])
