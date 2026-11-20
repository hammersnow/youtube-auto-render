#!/usr/bin/env python3
"""EGI V16 isolated R&D: two original cause/effect educational Shorts.
CPU-only Pillow + Python wave + FFmpeg. No publisher/catalog imports.
"""
import argparse, math, os, subprocess, wave, struct, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W,H,FPS,DURATION=1080,1920,24,26
BG=(10,19,34); WHITE=(234,244,250); MUTED=(142,169,193)
CYAN=(66,221,244); GOLD=(255,185,79); GREEN=(90,232,170)
FONT_PATH="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD_PATH="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(n,bold=False):
    return ImageFont.truetype(BOLD_PATH if bold else FONT_PATH,n)
def ease(x):
    x=max(0,min(1,x)); return x*x*(3-2*x)
def lerp(a,b,x): return a+(b-a)*x
def text(d,xy,s,size=36,color=WHITE,bold=False):
    f=font(size,bold)
    assert d.textbbox((0,0),s,font=f)[2] <= 920, ('TEXT_OVERFLOW',s)
    d.text(xy,s,font=f,fill=color)
def line(d,points,color,width=8): d.line(points,fill=color,width=width,joint="curve")
def circle(d,x,y,r,color): d.ellipse((int(x-r),int(y-r),int(x+r),int(y+r)),fill=color)
def base(title,subtitle):
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    text(d,(78,112),"EGI  /  CURIOSITY IN MOTION",29,CYAN,True)
    text(d,(78,216),title,53,WHITE,True)
    text(d,(78,298),subtitle,29,MUTED)
    line(d,[(78,374),(1000,374)],(38,65,85),3)
    text(d,(78,1740),"EKREM GOKBERK ISCAN  /  EGI",25,MUTED)
    text(d,(78,1790),"Original schematic  •  not to scale",22,MUTED)
    return im,d
def callout(d,t,events):
    # Exactly one transient explanation, persistent diagram state separate.
    active=[(a,b,s) for a,b,s in events if a<=t<b]
    assert len(active)<=1,active
    if active:
        a,b,s=active[0]; alpha=ease(min((t-a)/.35,(b-t)/.35,1))
        d.rounded_rectangle((85,1450,995,1570),radius=25,fill=(20,51,70))
        text(d,(116,1480),s,33,tuple(round(lerp(BG[i],WHITE[i],alpha)) for i in range(3)),True)
def network(t):
    im,d=base("WHY TCP SLOWS DOWN","Congestion control, in one connection")
    left=(245,750); right=(825,750)
    for x,label in ((left[0],"SENDER"),(right[0],"RECEIVER")):
        d.rounded_rectangle((x-135,610,x+135,875),radius=28,outline=CYAN,width=7)
        text(d,(x-105,675),label,28,CYAN,True)
    line(d,[(385,710),(680,710)],(59,105,130),6)
    line(d,[(680,825),(385,825)],(59,105,130),6)
    # Simplified congestion window progression: increase, then loss halves it.
    # This is an illustrative AIMD trace, not a real packet-level TCP simulator.
    cwnd=2 if t<4 else (2+int((t-4)//2)) if t<14 else max(2,5+int((t-14)//3))
    if t>=14: cwnd=3+int((t-14)//3)
    cwnd=min(7,cwnd)
    text(d,(85,450),"IN-FLIGHT WINDOW",34,WHITE,True)
    for i in range(7):
        x=105+i*132
        d.rounded_rectangle((x,510,x+102,566),radius=12,fill=GREEN if i<cwnd else (39,66,82))
    text(d,(85,975),"PACKETS  →",32,CYAN,True)
    text(d,(85,1080),"ACKS  ←",32,GREEN,True)
    # Packet and ACK motion tied to continuous timeline.
    for i in range(cwnd):
        phase=((t*0.42+i/max(cwnd,1))%1)
        x=lerp(385,680,phase)
        circle(d,x,710,12,GOLD)
        ax=lerp(680,385,(phase+.47)%1)
        circle(d,ax,825,8,GREEN)
    # One congestion event is visibly causal: loss -> fewer in flight -> regrowth.
    if 13.5<=t<16.2:
        line(d,[(516,650),(556,694)],(255,92,100),9)
        line(d,[(556,650),(516,694)],(255,92,100),9)
        text(d,(420,1190),"LOSS DETECTED",34,(255,118,121),True)
    events=[(0,4,"Send a small burst first."),(4,9,"ACKs allow the window to grow."),
            (9,14,"More data can be in flight."),(14,18,"Loss: reduce the send window."),
            (18,23,"ACKs return; increase carefully."),(23,26,"Control adapts to feedback.")]
    callout(d,t,events)
    text(d,(85,1320),"ACK feedback controls sending rate.",28,MUTED)
    return im
def hydraulic(t):
    im,d=base("HOW HYDRAULIC BRAKES WORK","Force in → pressure → clamping force")
    # pedal and master cylinder, pressure line, caliper and rotating disc
    p=ease((t-3)/3)*(1-ease((t-20)/4))
    text(d,(92,490),"PEDAL",32,GOLD,True)
    line(d,[(180,660),(270+42*p,835)],GOLD,19)
    d.rounded_rectangle((265,860,540,1010),radius=24,outline=CYAN,width=7)
    text(d,(280,1030),"MASTER CYLINDER",27,MUTED)
    # piston moves, liquid is represented by continuous filled chamber
    d.rectangle((295+95*p,881,515,987),fill=(35,115+int(70*p),174+int(40*p)))
    d.rectangle((289+95*p,874,306+95*p,995),fill=GOLD)
    line(d,[(540,925),(805,925),(805,1060)],CYAN,15)
    # traveling pressure pulse is a visual metaphor; fluid itself doesn't need to traverse the line
    if p>0:
        s=(t*0.75)%1
        x=lerp(545,805,s)
        circle(d,x,925,10,WHITE)
    cx,cy=805,1220
    d.ellipse((cx-133,cy-133,cx+133,cy+133),outline=(105,134,153),width=20)
    # spinning disc is illustrated by spokes; brakes slow rotation as clamp rises
    angle=t*(3.4-2.7*p)
    for k in range(6):
        a=angle+k*math.pi/3
        line(d,[(cx,cy),(cx+95*math.cos(a),cy+95*math.sin(a))],(92,120,145),8)
    # opposing pads close toward rotor as hydraulic pressure increases
    for side in (-1,1):
        x=cx+side*(190-43*p)
        d.rounded_rectangle((x-25,cy-76,x+25,cy+76),radius=12,fill=GOLD)
    text(d,(600,1440),"CALIPER + DISC",28,MUTED)
    events=[(0,3,"The pedal applies input force."),(3,7,"Piston pressurizes brake fluid."),
            (7,12,"Pressure acts throughout the line."),(12,17,"Caliper pistons push both pads."),
            (17,22,"Friction converts motion to heat."),(22,26,"Release: pressure falls; pads relax.")]
    callout(d,t,events)
    text(d,(85,1595),"Pressure transfers force; fluid is nearly incompressible.",24,MUTED)
    return im
def audio(path,kind):
    rate=16000; n=rate*DURATION
    starts=([0,4,9,14,18,23] if kind=="tcp" else [0,3,7,12,17,22])
    with wave.open(str(path),"wb") as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(rate)
        chunk=bytearray()
        for i in range(n):
            t=i/rate
            v=0.
            for st in starts:
                dt=t-st
                if 0<=dt<.12:
                    v+=.13*math.sin(2*math.pi*(660 if kind=="tcp" else 330)*dt)*math.exp(-33*dt)
            chunk.extend(struct.pack("<h",int(max(-1,min(1,v))*32767)))
            if len(chunk)>64000: wf.writeframesraw(chunk);chunk.clear()
        wf.writeframes(chunk)
def render(kind,out,seconds=DURATION):
    assert kind in ("tcp","brake") and 0<seconds<=DURATION
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    wav=out.with_suffix(".wav");audio(wav,kind)
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24",
         "-s",f"{W}x{H}","-r",str(FPS),"-i","pipe:0","-i",str(wav),
         "-t",str(seconds),"-c:v","libx264","-preset","veryfast","-crf","22",
         "-pix_fmt","yuv420p","-c:a","aac","-b:a","96k","-movflags","+faststart",str(out)]
    started=time.monotonic();proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for n in range(round(seconds*FPS)):
            frame=(network if kind=="tcp" else hydraulic)(n/FPS)
            proc.stdin.write(frame.tobytes())
    except BrokenPipeError:
        raise RuntimeError("ffmpeg stopped early")
    finally:
        proc.stdin.close()
    assert proc.wait()==0,"FFmpeg encode failed"
    assert out.stat().st_size>20000,"empty output"
    print("RENDER_OK",kind,seconds,"elapsed_s",round(time.monotonic()-started,2),out)
def smoke():
    for kind,fn in (("tcp",network),("brake",hydraulic)):
        frames=[fn(t) for t in (0,5,15,24)]
        assert all(f.size==(W,H) and f.getbbox() for f in frames)
        assert len({f.tobytes()[::1200] for f in frames})>=3,"static animation"
        print("FRAME_SMOKE_OK",kind)
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--kind",choices=["tcp","brake"],default="tcp")
    ap.add_argument("--out",default="outputs/egi_rd/preview.mp4")
    ap.add_argument("--seconds",type=float,default=DURATION)
    ap.add_argument("--smoke",action="store_true")
    a=ap.parse_args()
    if a.smoke:smoke()
    else:render(a.kind,a.out,a.seconds)
