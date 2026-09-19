#!/usr/bin/env python3
from pathlib import Path
import cv2,numpy as np,math,wave,subprocess,json,hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
OUT=Path("outputs/latest");OUT.mkdir(parents=True,exist_ok=True)
W,H,FPS,D=1080,1920,30,8
DAY=datetime.now(ZoneInfo("Europe/Istanbul"));SEED=int(DAY.strftime("%Y%m%d"))
def txt(im,s,y,sc=1.6,col=(245,245,245),th=3):
 (w,_),_=cv2.getTextSize(s,cv2.FONT_HERSHEY_SIMPLEX,sc,th);cv2.putText(im,s,((W-w)//2,y),cv2.FONT_HERSHEY_SIMPLEX,sc,col,th,cv2.LINE_AA)
def bg(t,pal):
 im=np.zeros((H,W,3),np.uint8); yy=np.linspace(0,1,H)[:,None]; pulse=.5+.5*math.sin(2*math.pi*t/D)
 a=np.array(pal[0],float);b=np.array(pal[1],float)
 im[:]=((a[None,None,:]*(1-yy[:,:,None])+b[None,None,:]*yy[:,:,None])*(.88+.08*pulse)).clip(0,255).astype(np.uint8)
 for k in range(34):
  x=int((k*173+SEED%251+18*t)%W);y=int((k*277+SEED%337+10*t)%H);cv2.circle(im,(x,y),2+(k%3),(110,120,150),-1)
 return im
def timer(im,t):
 if 1<=t<6:
  p=(t-1)/5; c=(540,1590);r=90
  cv2.circle(im,c,r,(65,70,90),12,cv2.LINE_AA);cv2.ellipse(im,c,(r,r),-90,-90+360*(1-p),(40,220,245),12,cv2.LINE_AA)
def reveal(im,x,y,t):
 if 6<=t<7.5:
  q=(t-6)/1.5;r=int(60+25*math.sin(q*math.pi*2)**2)
  for z in (r+35,r+20,r):cv2.circle(im,(x,y),z,(65,235,110),max(3,(r+40-z)//4),cv2.LINE_AA)
def odd(t,seed):
 im=bg(t,((12,15,28),(38,18,58))); rows=10;cols=10;idx=seed%(rows*cols); rr,cc=divmod(idx,cols)
 for r in range(rows):
  for c in range(cols):
   x=135+c*90;y=440+r*90;ang=math.radians(8 if (r,c)==(rr,cc) else 0)
   pts=np.array([[x+27*math.cos(ang+q),y+27*math.sin(ang+q)] for q in (0,2.2,4.1)],np.int32);cv2.fillPoly(im,[pts],(55,205,245))
 txt(im,"FIND THE ODD ONE",210);txt(im,"99% FAIL",285,1.05,(70,230,255),2);timer(im,t);reveal(im,135+cc*90,440+rr*90,t);return im
def hidden(t,seed):
 im=bg(t,((8,22,55),(52,12,65))); txt(im,"CAN YOU SEE 8?",210);txt(im,"5 SECONDS",285,1.05,(235,90,225),2)
 # dense field; target 8 differs only slightly in luminance until reveal
 rng=np.random.default_rng(seed)
 for i in range(120):
  x=int(rng.integers(90,990));y=int(rng.integers(420,1390));cv2.circle(im,(x,y),int(rng.integers(8,20)),(115,85,145),-1)
 col=(145,105,170) if t<6 else (80,245,245);txt(im,"8",1030,7.0,col,15);timer(im,t);reveal(im,540,980,t);return im
def rotation(t,seed):
 im=bg(t,((10,24,45),(22,40,68)));rows=8;cols=12;idx=seed%(rows*cols);rr,cc=divmod(idx,cols)
 txt(im,"WHICH ONE IS WRONG?",210,1.45);txt(im,"LEVEL 3",285,1.05,(80,190,250),2)
 for r in range(rows):
  for c in range(cols):
   x=100+c*80;y=500+r*105;a=math.radians(11 if (r,c)==(rr,cc) else 0)
   p=np.array([[x+30*math.cos(a),y+30*math.sin(a)],[x+30*math.cos(a+2.5),y+30*math.sin(a+2.5)],[x+30*math.cos(a-2.5),y+30*math.sin(a-2.5)]],np.int32);cv2.fillPoly(im,[p],(60,175,235))
 timer(im,t);reveal(im,100+cc*80,500+rr*105,t);return im
def audio(p,f):
 sr=24000;t=np.arange(sr*D)/sr;s=.035*np.sin(2*np.pi*f*t)+.012*np.sin(2*np.pi*f*2*t)
 with wave.open(str(p),"wb") as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((s*32767).astype("<i2").tobytes())
def encode(name,fn,f,seed):
 raw=OUT/(name+"_raw.mp4");wav=OUT/(name+".wav");fin=OUT/(name+".mp4");v=cv2.VideoWriter(str(raw),cv2.VideoWriter_fourcc(*"mp4v"),FPS,(W,H))
 for i in range(FPS*D):v.write(fn(i/FPS,seed))
 v.release();audio(wav,f);subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(raw),"-i",str(wav),"-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p","-c:a","aac","-b:a","96k","-shortest","-movflags","+faststart",str(fin)],check=True);raw.unlink();wav.unlink()
 return hashlib.sha256(fin.read_bytes()).hexdigest()
families=[("odd_object",odd,"Find the Odd One Before Time Runs Out 👀 #Shorts","99% FAIL"),("hidden_number",hidden,"Can You See the Hidden 8? 🔎 #Shorts","5 SECONDS"),("rotation_puzzle",rotation,"Which One Is Wrong? 🧠 #Shorts","LEVEL 3")]
items=[]
# Five uploads, cycling three retention families with independent seeds/targets.
for i in range(5):
 fam,fn,title,label=families[(SEED+i)%3]; name=["short_1_mesmerizing","short_2_optical","short_3_rain","short_4_loop","short_5_experiment"][i]; local=SEED+i*7919
 h=encode(name,fn,175+i*18,local)
 items.append({"file":name+".mp4","title":title,"family":fam,"difficulty_label":label,"variant":local,"sha256":h,"description":"Solve it before the timer ends. Watch again if you missed it. #visualpuzzle #brainteaser #shorts","tags":["visual puzzle","brain teaser",fam.replace("_"," "),"shorts"]})
m={"date":DAY.strftime("%Y-%m-%d"),"strategy":"retention-loop-v4","resolution":"1080x1920","fps":30,"duration_sec":8,"shorts":items}
json.dump(m,open(OUT/"manifest.json","w"),ensure_ascii=False,indent=2)
print("Retention V4 rendered:",[(x["family"],x["sha256"][:10]) for x in items])
