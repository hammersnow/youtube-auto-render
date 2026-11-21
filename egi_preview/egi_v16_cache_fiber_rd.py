#!/usr/bin/env python3
"""Two original EGI V16 educational schematics. CPU-only Pillow + stdlib + FFmpeg."""
import argparse, math, os, struct, subprocess, tempfile, time, wave
from PIL import Image, ImageDraw, ImageFont
W,H,FPS,DURATION=1080,1920,24,26
NAVY=(9,17,34); CYAN=(67,223,238); AMBER=(255,183,82); GREEN=(99,236,178); WHITE=(239,246,255)
EVENTS={
 "cache":[(0,4,"CPU REQUEST"),(4,9,"CACHE HIT"),(9,14,"CACHE MISS"),(14,20,"RAM FETCH"),(20,26,"CACHE FILLED")],
 "fiber":[(0,5,"LIGHT ENTERS"),(5,11,"CORE / CLADDING"),(11,17,"GUIDED PATH"),(17,22,"BEND LOSS"),(22,26,"RECEIVER")]
}
def font(n):
 for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
  if os.path.exists(path): return ImageFont.truetype(path,n)
 return ImageFont.load_default()
F={s:font(s) for s in (24,32,42,54,70)}
def text(d,xy,msg,size=32,color=WHITE):
 assert len(msg)<48
 d.text(xy,msg,font=F[size],fill=color)
def ease(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def pulse(d,a,b,phase,color=CYAN,r=12):
 x=a[0]+(b[0]-a[0])*phase;y=a[1]+(b[1]-a[1])*phase
 d.ellipse((x-r,y-r,x+r,y+r),fill=color)
def panel(d,box,name,color):
 d.rounded_rectangle(box,radius=26,outline=color,width=5,fill=(18,34,54))
 text(d,(box[0]+22,box[1]+24),name,32,color)
def arrow(d,a,b,color=CYAN,width=8):
 d.line((a,b),fill=color,width=width)
 ang=math.atan2(b[1]-a[1],b[0]-a[0])
 for off in (-.55,.55):
  end=(b[0]-23*math.cos(ang+off),b[1]-23*math.sin(ang+off))
  d.line((b,end),fill=color,width=width)
def cache(d,t):
 panel(d,(100,420,980,700),"CPU",CYAN)
 panel(d,(100,830,980,1110),"L1 CACHE",GREEN)
 panel(d,(100,1250,980,1530),"MAIN MEMORY",AMBER)
 for i in range(5):
  x=185+i*155
  d.rounded_rectangle((x,950,x+104,1012),radius=12,fill=GREEN if i==2 and t>=20 else (38,76,92),outline=GREEN,width=3)
  text(d,(x+34,960),str(i),32)
 arrow(d,(540,700),(540,830),CYAN)
 arrow(d,(590,1250),(590,1110),AMBER)
 if t<4: pulse(d,(540,700),(540,830),ease(t/4),CYAN)
 elif t<9:
  pulse(d,(540,830),(540,700),ease((t-4)/5),GREEN)
  text(d,(180,1138),"Requested data already cached",32,GREEN)
 elif t<14:
  pulse(d,(540,1000),(540,1250),ease((t-9)/5),AMBER)
  text(d,(180,1138),"Not found: request lower memory",32,AMBER)
 elif t<20:
  pulse(d,(540,1410),(540,1020),ease((t-14)/6),AMBER)
  text(d,(180,1138),"Fetch block, update cache",32,AMBER)
 else:
  pulse(d,(540,830),(540,700),ease((t-20)/6),GREEN)
  text(d,(180,1138),"Next access can be faster",32,GREEN)
def fiber(d,t):
 panel(d,(100,450,980,690),"LIGHT SOURCE",AMBER)
 panel(d,(100,1280,980,1510),"RECEIVER",GREEN)
 # Schematic: ray guided by total internal reflection only above critical angle.
 d.rounded_rectangle((210,755,870,1205),radius=40,fill=(24,59,84),outline=(81,127,162),width=20)
 d.rounded_rectangle((250,815,830,1145),radius=24,fill=(11,33,59),outline=CYAN,width=5)
 text(d,(265,760),"CLADDING",32,WHITE)
 text(d,(300,1050),"HIGHER-INDEX CORE",32,CYAN)
 path=[(270,920),(390,850),(510,1090),(630,850),(750,1090),(820,970)]
 for i in range(len(path)-1):
  d.line((path[i],path[i+1]),fill=(44,95,118),width=9)
 progress=ease((t-5)/16)
 segments=progress*(len(path)-1)
 for i in range(len(path)-1):
  if segments>=i:
   q=min(1,segments-i);p=path[i];v=path[i+1]
   d.line((p,(p[0]+(v[0]-p[0])*q,p[1]+(v[1]-p[1])*q)),fill=AMBER,width=12)
 if t>=17:
  # bend-loss illustration is intentionally labeled as an exaggerated schematic
  d.arc((730,1070,1030,1370),180,290,fill=AMBER,width=9)
  text(d,(190,1560),"Tight bends can increase loss",32,AMBER)
 elif t>=11:text(d,(190,1560),"Guidance needs index contrast",32,CYAN)
 else:text(d,(190,1560),"Core index > cladding index",32,CYAN)
def frame(mode,t):
 im=Image.new("RGB",(W,H),NAVY);d=ImageDraw.Draw(im)
 text(d,(95,120),"EGI  /  CURIOSITY IN MOTION",32,CYAN)
 title="WHY CPU CACHES MATTER" if mode=="cache" else "HOW OPTICAL FIBER GUIDES LIGHT"
 text(d,(95,220),title,42)
 for a,b,name in EVENTS[mode]:
  if a<=t<b:
   # One transient caption at any instant, separate from persistent apparatus.
   d.rounded_rectangle((100,1640,980,1735),radius=22,fill=(25,52,78))
   text(d,(140,1660),name,42,AMBER);break
 (cache if mode=="cache" else fiber)(d,t)
 text(d,(95,1810),"EGI  •  Original educational schematic",24,(125,153,174))
 return im
def audio(path,mode):
 sr=24000;total=DURATION*sr
 cues=[x[0] for x in EVENTS[mode]][1:]
 with wave.open(path,"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr)
  buf=bytearray()
  for i in range(total):
   t=i/sr;v=0.
   for j,c in enumerate(cues):
    dt=t-c
    if 0<=dt<.13:
     env=(1-dt/.13)**2
     v+=.12*env*math.sin(2*math.pi*(480+120*j)*dt)
   buf.extend(struct.pack("<h",int(max(-1,min(1,v))*32767)))
  w.writeframes(buf)
def render(mode,out):
 start=time.monotonic()
 with tempfile.TemporaryDirectory() as tmp:
  wav=os.path.join(tmp,"audio.wav");audio(wav,mode)
  cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","pipe:0","-i",wav,"-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p","-c:a","aac","-b:a","96k","-t",str(DURATION),"-movflags","+faststart",out]
  p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
  try:
   for i in range(DURATION*FPS):p.stdin.write(frame(mode,i/FPS).tobytes())
  finally:p.stdin.close()
  if p.wait():raise RuntimeError("ffmpeg render failed")
 print("RENDER_SECONDS",mode,round(time.monotonic()-start,2))
def smoke():
 for mode in EVENTS:
  assert len(EVENTS[mode])==5
  assert EVENTS[mode][0][0]==0 and EVENTS[mode][-1][1]==DURATION
  for i,(a,b,name) in enumerate(EVENTS[mode]):
   assert b>a and (i==0 or EVENTS[mode][i-1][1]==a)
  for t in (0,5,13,21,25.9):
   f=frame(mode,t)
   assert f.size==(W,H) and f.getbbox() is not None
   assert len(set(f.resize((54,96)).getdata()))>25,"blank frame"
 print("EGI_ORIGINAL_EPISODES_SMOKE_OK")
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("--mode",choices=["cache","fiber"]);ap.add_argument("--output");ap.add_argument("--smoke",action="store_true")
 args=ap.parse_args()
 if args.smoke:smoke()
 else:
  assert args.mode and args.output
  render(args.mode,args.output)
