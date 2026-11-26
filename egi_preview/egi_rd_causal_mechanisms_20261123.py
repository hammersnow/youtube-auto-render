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
RED=(255,91,109)
MUTED=(115,161,185)
def panel(d,box,color=CYAN):
 x,y,x2,y2=box
 d.rounded_rectangle((x+10,y+12,x2+10,y2+12),radius=25,fill=(5,12,22))
 d.rounded_rectangle(box,radius=25,fill=(19,40,57),outline=color,width=3)
 wire(d,[(x+22,y+12),(x2-22,y+12)],(71,107,128),3)
def chip(d,x,y,w,h,label,color,detail=None):
 panel(d,(x,y,x+w,y+h),color)
 text(d,(x+w/2,y+h*.35),label,31,color,True)
 if detail:text(d,(x+w/2,y+h*.72),detail,24)
def packet(d,x,y,label,color,scale=1):
 w=68*scale;h=35*scale
 d.rounded_rectangle((x-w,y-h,x+w,y+h),radius=9,fill=(20,44,63),outline=color,width=4)
 text(d,(x,y),label,int(24*scale),color,True)
def focus(d,t,rect,color):
 # restrained stage-specific outline, leaving every persistent object visible
 x,y,x2,y2=rect
 a=.5+.5*math.sin(t*3)
 c=tuple(int(45+(v-45)*(.45+.55*a)) for v in color)
 for px,py,dx,dy in [(x,y,1,1),(x2,y,-1,1),(x,y2,1,-1),(x2,y2,-1,-1)]:
  wire(d,[(px+dx*35,py),(px,py),(px,py+dy*35)],c,5)
def branch(t):
 im,d=base("WHY CPUs GUESS AHEAD")
 red=RED
 # Persistent instruction stream, predictor and execution/retirement queue.
 text(d,(540,363),"INSTRUCTION STREAM",26,MUTED,True)
 for i,s in enumerate(("LOAD","CMP","JNZ B","ADD","XOR")):
  x=86+i*184
  col=GOLD if i==2 else CYAN
  packet(d,x+85,430,s,col,.98)
 chip(d,90,520,420,138,"FETCH / DECODE",CYAN,"PC 0x104")
 chip(d,570,520,420,138,"PREDICTOR",GOLD,"Predict A" if t<15 else "Actual B")
 wire(d,[(510,589),(570,589)],GOLD,7)
 if t<5:packet(d,540,589,"JNZ",GOLD,.70)
 text(d,(540,715),"SPECULATIVE EXECUTION",27,MUTED,True)
 for i,(label,x,col) in enumerate((("PATH A",90,CYAN),("PATH B",565,GOLD))):
  panel(d,(x,760,x+420,1050),col)
  text(d,(x+210,795),label,33,col,True)
  for k,op in enumerate(("LOAD","ADD","XOR") if i==0 else ("LOAD","SUB","AND")):
   y=855+k*68
   active=(5+k*1.2<=t<15+k*.20) if i==0 else (20+k*.85<=t)
   invalid=i==0 and t>=15+k*.20
   cc=red if invalid else col if active else MUTED
   d.rounded_rectangle((x+23,y-22,x+397,y+25),radius=8,outline=cc,fill=(25,48,63),width=2)
   text(d,(x+100,y),op,24,cc,True)
   text(d,(x+292,y),"SQUASH" if invalid else "RESULT" if active else "WAIT",22,cc)
   if active:
    q=ease((t-(5 if i==0 else 20)-k*.85)/.8)
    wire(d,[(x+31,y+20),(x+31+356*q,y+20)],cc,3)
   if invalid:
    q=ease((t-15-k*.2)/.4)
    wire(d,[(x+30,y),(x+30+360*q,y)],red,4)
 wire(d,[(300,658),(300,760)],CYAN,7)
 wire(d,[(780,658),(780,760)],GOLD,7)
 if 5<=t<15:packet(d,300,660+90*((t-5)*.8%1),"uOP",CYAN,.65)
 if t>=20:packet(d,780,660+90*((t-20)*.9%1),"uOP",GOLD,.65)
 text(d,(540,1110),"REORDER BUFFER  /  IN-ORDER RETIREMENT",26,MUTED,True)
 for k in range(4):
  x=90+k*230
  valid= t>=20+k*.8
  speculative=5+k*.8<=t<15
  killed=15<=t<20
  col=GREEN if valid else RED if killed else CYAN if speculative else MUTED
  panel(d,(x,1150,x+210,1290),col)
  text(d,(x+105,1185),"B"+str(k+1) if valid else "A"+str(k+1) if speculative or killed else "EMPTY",28,col,True)
  text(d,(x+105,1247),"READY" if valid else "INVALID" if killed else "HOLD" if speculative else "WAIT",24,col)
 wire(d,[(540,1290),(540,1340)],GREEN if t>=23 else MUTED,8)
 chip(d,285,1340,510,120,"ARCHITECTURAL STATE",GREEN if t>=23 else MUTED,"B committed" if t>=23 else "No speculative commit")
 target=(65,500,1010,680) if t<5 else (68,741,531,1070) if t<15 else (68,1130,1010,1310) if t<20 else (550,740,1010,1070) if t<23 else (265,1320,815,1480)
 focus(d,t,target,GOLD if t<20 else GREEN)
 transient(d,t,[(0,5,"Decode a conditional branch"),(5,10.2,"Predict A: execute ahead"),(10.2,15,"Hold speculative results"),(15,20,"Wrong guess: squash A"),(20,27.9,"Redirect to B and retire")])
 return im
def regen(t):
 im,d=base("HOW BRAKING RECHARGES")
 # Shared shaft, rotor/stator cutaway, phase-current paths and pack cells.
 t0=max(0.,t-5)
 speed=1-.68*ease(t0/23)
 angle=2.9*(min(t,5)+t0-.34*t0*t0/23)
 text(d,(540,352),"MOTION  →  ELECTRICITY",29,GOLD,True)
 text(d,(270,414),"WHEEL SPEED",24,MUTED,True)
 text(d,(270,455),f"{int(speed*100)}%",37,CYAN,True)
 text(d,(790,414),"BRAKE REQUEST",24,MUTED,True)
 text(d,(790,455),"ACTIVE" if t>=5 else "COAST",31,GOLD if t>=5 else MUTED,True)
 # wheel cutaway and coupled shaft
 circle(d,238,720,173,(29,39,52))
 circle(d,238,720,158,(100,140,156),16)
 for i in range(20):
  a=angle+i*math.tau/20
  wire(d,[(238+158*math.cos(a),720+158*math.sin(a)),(238+171*math.cos(a+.04),720+171*math.sin(a+.04))],MUTED,5)
 circle(d,238,720,112,(13,29,44))
 for i in range(6):
  a=angle+i*math.tau/6
  wire(d,[(238+30*math.cos(a),720+30*math.sin(a)),(238+104*math.cos(a),720+104*math.sin(a))],(162,191,205),14)
 circle(d,238,720,35,(155,186,199))
 wire(d,[(273,720),(700,720)],(90,128,147),33)
 for j in range(8):
  x=340+j*45
  y=720+8*math.sin(angle*2+j*.5)
  wire(d,[(x-9,y-11),(x+9,y+11)],(194,213,221),3)
 # stator / rotor with fixed coils and rotating magnets
 circle(d,737,720,180,(38,58,71))
 circle(d,737,720,166,(128,163,176),6)
 circle(d,737,720,123,(9,24,39))
 for i in range(6):
  a=i*math.tau/6
  x=737+145*math.cos(a);y=720+145*math.sin(a)
  c=GOLD if t>=10 and math.sin(angle+a)>.0 else (151,97,56)
  for k in range(3):circle(d,x+(k-1)*8,y,19,c,3)
 for i in range(4):
  a=angle+i*math.tau/4
  x=737+80*math.cos(a);y=720+80*math.sin(a)
  circle(d,x,y,34,CYAN if i%2==0 else RED)
  text(d,(x,y),"N" if i%2==0 else "S",24,(10,21,33),True)
 circle(d,737,720,30,(157,188,202))
 if t>=5:
  a=-angle
  d.arc((185,667,291,773),start=math.degrees(a)%360,end=math.degrees(a)%360+230,fill=GOLD,width=6)
  text(d,(238,933),"COUNTER-TORQUE",24,GOLD,True)
 text(d,(737,933),"ROTOR + STATOR",29,GOLD,True)
 # all 3 phase wires visibly connected to power electronics
 cols=[GOLD,CYAN,(190,138,255)]
 for i,c in enumerate(cols):
  x=687+i*50
  wire(d,[(x,882),(x,1003),(340+i*35,1003),(340+i*35,1090)],c if t>=10 else MUTED,6)
  if t>=10:
   p=((t-10)*.7+i/3)%1
   circle(d, x,882+121*p,9,c)
 panel(d,(90,1090,520,1355),CYAN)
 text(d,(305,1130),"INVERTER",33,CYAN,True)
 # schematic phase waveform and DC bus; never show physical electrons as moving slugs
 for i,c in enumerate(cols):
  pts=[(119+j*2,1200+24*math.sin(j*.09-angle+i*math.tau/3)) for j in range(107)]
  wire(d,pts,c if t>=10 else MUTED,3)
 wire(d,[(343,1190),(480,1190)],GREEN if t>=15 else MUTED,5)
 wire(d,[(343,1221),(480,1221)],GREEN if t>=15 else MUTED,5)
 text(d,(305,1305),"3-phase AC to DC",26,GREEN if t>=15 else MUTED)
 wire(d,[(520,1175),(595,1175)],GREEN if t>=15 else MUTED,9)
 wire(d,[(520,1275),(595,1275)],GREEN if t>=15 else MUTED,9)
 panel(d,(595,1090,990,1355),GREEN)
 text(d,(792,1130),"BATTERY PACK",30,GREEN,True)
 charge=ease((t-20)/8)
 for k in range(5):
  x=630+k*65
  d.rounded_rectangle((x,1185,x+55,1300),radius=7,outline=MUTED,width=3,fill=(19,43,56))
  height=18+74*charge
  d.rounded_rectangle((x+6,1294-height,x+49,1294),radius=4,fill=GREEN)
  wire(d,[(x+20,1178),(x+35,1178)],MUTED,4)
 if t>=20:
  for i in range(3):
   p=((t-20)*.65+i/3)%1
   circle(d,520+75*p,1175,7,GREEN)
 text(d,(540,1430),"Energy recovered < kinetic energy lost",28,MUTED)
 target=(50,515,424,916) if t<5 else (50,515,424,960) if t<10 else (550,515,940,960) if t<15 else (70,1070,540,1370) if t<20 else (575,1070,1010,1370)
 focus(d,t,target,GOLD if t<15 else GREEN)
 transient(d,t,[(0,5,"Wheels drive the shaft"),(5,10,"Generator torque slows the wheel"),(10,15,"Rotating field induces AC"),(15,20,"Power electronics feed the DC bus"),(20,27.9,"Store part of the energy")])
 return im
NARRATION={
 "branch":[(.25,5,"The processor guesses the next instruction before the branch resolves."),(5,10.2,"It predicts path A and starts work before it knows the answer."),(10.2,15,"Speculative results wait. They cannot retire yet."),(15,20,"The branch resolves to B. Wrong path entries are flushed."),(20,27.8,"Fetch redirects to B. Correct results can now retire in order.")],
 "regen":[(.25,5,"When you brake, the wheels can drive the electric motor."),(5,10,"Generator torque opposes rotation. The car slows down."),(10,15,"The rotating magnetic field induces alternating current in the coils."),(15,20,"Power electronics convert this energy to direct current."),(20,27.8,"The battery stores some energy. The rest is lost as heat.")]
}
def audio(path,kind):
 sr=24000;signal=np.zeros(sr*DURATION,dtype=np.float32)
 with tempfile.TemporaryDirectory() as tmp:
  for i,(start,end,line) in enumerate(NARRATION[kind]):
   script=os.path.join(tmp,"speech.txt")
   with open(script,"w",encoding="ascii") as f:f.write(line)
   raw=subprocess.check_output(["ffmpeg","-v","error","-f","lavfi","-i","flite=textfile="+script+":voice=slt","-ar",str(sr),"-ac","1","-f","s16le","-"])
   voice=np.frombuffer(raw,dtype="<i2").astype(np.float32)/32768
   assert len(voice)<=round((end-start)*sr),(kind,line,len(voice)/sr)
   pos=round(start*sr)
   peak=max(float(np.max(np.abs(voice))),.01)
   signal[pos:pos+len(voice)]+=voice*(.55/peak)
   u=np.arange(int(.14*sr))/sr
   signal[pos:pos+len(u)]+=.055*np.exp(-u*23)*np.sin(2*np.pi*(400+i*95)*u)
 # Regression gate: speech must occupy materially more than the prior isolated tones.
 active=np.mean(np.abs(signal)>.01)
 assert active>.08,(kind,active)
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
