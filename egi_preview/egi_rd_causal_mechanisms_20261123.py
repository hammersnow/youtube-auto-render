#!/usr/bin/env python3
"""Isolated EGI mechanism prototypes: causal geometry, not publication assets."""
import argparse, math, subprocess, tempfile, wave, os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

W,H,FPS,DURATION=1080,1920,24,28
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
INK=(9,20,35); CYAN=(65,224,241); GOLD=(255,190,91); GREEN=(84,238,168)
def clamp(v): return max(0.,min(1.,v))
def ease(v): v=clamp(v);return v*v*(3-2*v)
def text(d,p,s,size=32,color=(235,248,255),bold=False):
 f=ImageFont.truetype(BOLD if bold else FONT,size)
 bb=d.textbbox((0,0),s,font=f)
 assert bb[2]-bb[0] < 920,(s,bb)
 d.text(p,s,font=f,fill=color,anchor="mm")
def circle(d,x,y,r,color,width=0):
 d.ellipse((int(x-r),int(y-r),int(x+r),int(y+r)),fill=color if not width else None,outline=color if width else None,width=width)
def wire(d,pts,color=CYAN,width=9):d.line([(int(x),int(y)) for x,y in pts],fill=color,width=width,joint="curve")
def arrow(d,x,y,angle,color):
 wire(d,[(x-22*math.cos(angle-.5),y-22*math.sin(angle-.5)),(x,y),(x-22*math.cos(angle+.5),y-22*math.sin(angle+.5))],color,6)
def base(title):
 im=Image.new("RGB",(W,H),INK);d=ImageDraw.Draw(im)
 for y in range(280,1550,72):wire(d,[(70,y),(1010,y)],(18,38,54),2)
 text(d,(540,102),"EGI",70,CYAN,True);text(d,(540,169),"CURIOSITY IN MOTION",24,(145,183,199))
 text(d,(540,253),title,43,bold=True)
 text(d,(540,1852),"Ekrem Gökberk ISCAN",25,(150,186,201))
 return im,d
def transient(d,t,events):
 active=[(a,b,s) for a,b,s in events if a<=t<b]
 assert len(active)<=1
 if active:
  a,b,s=active[0]; opacity=ease((t-a)/.35)*(1-ease((t-(b-.4))/.4))
  if opacity>.02:
   text(d,(540,1630),s,33,(int(150+85*opacity),int(170+65*opacity),255),True)
def branch(t):
 im,d=base("WHY CPUs GUESS AHEAD")
 # Connected fetch -> branch -> speculative lanes -> flush -> correct commit.
 wire(d,[(155,660),(510,660),(510,810)],(64,112,143),15)
 wire(d,[(510,810),(305,1020),(305,1280)],CYAN,12)
 wire(d,[(510,810),(785,1020),(785,1280)],GOLD,12)
 for x,y,label in [(155,660,"FETCH"),(510,810,"BRANCH"),(305,1300,"PATH A"),(785,1300,"PATH B")]:
  circle(d,x,y,64,(27,65,84));circle(d,x,y,64,CYAN if x!=785 else GOLD,4);text(d,(x,y),label,22)
 progress=ease(t/3)
 circle(d,155+355*progress,660,18,GREEN)
 prediction=t>=4; resolved=t>=15; commit=t>=21
 if prediction:
  text(d,(540,465),"PREDICT A",37,CYAN,True)
  for i in range(5):
   p=clamp((t-4-i*.55)/5)
   if p:
    circle(d,510-205*ease(p),810+470*ease(p),12,CYAN)
 if resolved:
  text(d,(540,530),"ACTUAL: B",36,GOLD,True)
  if t<21:
   for j in range(4):
    p=ease((t-15-j*.18)/2)
    if p:wire(d,[(305-40*p,1020+65*j),(305+40*p,1020+65*j)],(255,91,109),7)
  for j in range(5):
   p=ease((t-17-j*.48)/5)
   if p:circle(d,510+275*p,810+470*p,12,GOLD)
 if commit:
  circle(d,785,1350,40,GREEN,5);text(d,(785,1415),"COMMIT B",27,GREEN,True)
 transient(d,t,[(0,3,"The CPU fetches a branch"),(4,7,"Prediction starts speculative work"),(15,18,"Wrong path: discard its results"),(21,25,"Correct path can retire")])
 return im
def regen(t):
 im,d=base("HOW BRAKING RECHARGES")
 # Wheel -> shaft -> motor generator -> inverter -> battery, persistent charge.
 circle(d,250,740,175,(26,54,72));circle(d,250,740,140,CYAN,12)
 angle=t*1.8
 for i in range(8):
  a=angle+i*math.pi/4
  wire(d,[(250,740),(250+130*math.cos(a),740+130*math.sin(a))],(100,156,177),8)
 wire(d,[(390,740),(650,740)],(130,172,188),26)
 circle(d,700,740,118,(34,65,82));circle(d,700,740,112,GOLD,8)
 for i in range(6):
  a=angle*.6+i*math.pi/3
  circle(d,700+72*math.cos(a),740+72*math.sin(a),13,GOLD)
 text(d,(700,925),"MOTOR / GENERATOR",29,GOLD,True)
 wire(d,[(700,858),(700,1060),(440,1060),(440,1220)],(68,125,145),13)
 d.rounded_rectangle((290,1200,590,1380),radius=22,fill=(22,58,72),outline=CYAN,width=6)
 text(d,(440,1252),"INVERTER",29,CYAN,True)
 d.rounded_rectangle((640,1200,955,1400),radius=24,fill=(27,63,75),outline=GREEN,width=6)
 text(d,(795,1252),"BATTERY",29,GREEN,True)
 wire(d,[(590,1300),(640,1300)],GREEN,10)
 if t>=5:
  for i in range(4):
   p=((t-5)*.5+i*.25)%1
   circle(d,700,858+202*p,11,GOLD)
 if t>=12:
  for i in range(3):
   p=((t-12)*.45+i/3)%1
   circle(d,440,1060+140*p,10,CYAN)
 if t>=18:
  for i in range(3):
   p=((t-18)*.55+i/3)%1
   circle(d,590+50*p,1300,11,GREEN)
  level=clamp((t-18)/9)
  d.rounded_rectangle((675,1320,675+240*level,1355),radius=8,fill=GREEN)
 text(d,(540,465),"KINETIC ENERGY  →  ELECTRICAL ENERGY",30,GOLD,True)
 transient(d,t,[(0,3,"The moving wheel drives the shaft"),(5,8,"Rotor motion induces electrical output"),(12,15,"Power electronics condition the current"),(18,22,"Energy enters the battery")])
 return im
def audio(path,kind):
 sr=24000;n=sr*DURATION;signal=np.zeros(n,dtype=np.float32)
 events=[0.8,4,15,21] if kind=="branch" else [1,5,12,18]
 for k,t in enumerate(events):
  start=int(t*sr);length=int(.18*sr);u=np.arange(length)/sr
  env=np.exp(-u*25)
  signal[start:start+length]+=.12*env*np.sin(2*np.pi*(360+k*115)*u)
 with wave.open(path,"wb") as f:
  f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
  f.writeframes((np.clip(signal,-1,1)*32767).astype("<i2").tobytes())
def main():
 p=argparse.ArgumentParser();p.add_argument("--kind",choices=["branch","regen"],required=True)
 p.add_argument("--output",required=True);p.add_argument("--smoke",action="store_true");a=p.parse_args()
 fn=branch if a.kind=="branch" else regen
 if a.smoke:
  for t in [0,1,3,5,12,16,22,27.9]:
   im=fn(t);assert im.size==(W,H)
   assert np.asarray(im).std()>12
  print("SMOKE_OK",a.kind);return
 with tempfile.TemporaryDirectory() as tmp:
  wav=os.path.join(tmp,"cue.wav");audio(wav,a.kind)
  cmd=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",wav,"-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-shortest",a.output]
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
  try:
   for frame in range(FPS*DURATION):proc.stdin.write(fn(frame/FPS).tobytes())
  finally:proc.stdin.close()
  if proc.wait():raise RuntimeError("ffmpeg failed")
if __name__=="__main__":main()
