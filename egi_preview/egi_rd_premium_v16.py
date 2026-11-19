#!/usr/bin/env python3
"""EGI original 32s causal explainers; isolated R&D, no uploader or catalog changes."""
import argparse
import hashlib
import json
import math
import os
import subprocess
import time
import wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 32
BG = "#081424"
CYAN = "#54dbf4"
AMBER = "#ffc06e"
GREEN = "#55e4c9"
WHITE = "#e9f7ff"
MUTED = "#83a6bc"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ease(x):
    x = clamp(x)
    return x*x*(3-2*x)

def mix(a,b,t):
    return a+(b-a)*t

def font(n, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, n)

def txt(d, x, y, s, size=30, color=WHITE, bold=False, anchor="mm"):
    d.text((int(x),int(y)), s, font=font(size,bold), fill=color, anchor=anchor)

def box(d, rect, fill="#102b40", edge="#385f77", r=20, w=3):
    d.rounded_rectangle(tuple(map(int,rect)),radius=r,fill=fill,outline=edge,width=w)

def dot(d,x,y,r,col):
    d.ellipse((int(x-r),int(y-r),int(x+r),int(y+r)),fill=col)

def ring(d,x,y,r,col,w=4):
    d.ellipse((int(x-r),int(y-r),int(x+r),int(y+r)),outline=col,width=w)

def line(d, pts, col, w=5, joint="curve"):
    d.line(pts, fill=col, width=w, joint=joint)

def arrow(d, x1,y1,x2,y2,col,w=8):
    line(d,[(int(x1),int(y1)),(int(x2),int(y2))],col,w)
    a=math.atan2(y2-y1,x2-x1)
    p1=(x2-23*math.cos(a)+13*math.sin(a),y2-23*math.sin(a)-13*math.cos(a))
    p2=(x2-23*math.cos(a)-13*math.sin(a),y2-23*math.sin(a)+13*math.cos(a))
    d.polygon([(x2,y2),p1,p2],fill=col)

def bar(d,x1,y,x2,fill,progress):
    box(d,(x1,y,x2,y+11),"#214158","#214158",6,1)
    width=int((x2-x1)*clamp(progress))
    if width:
        box(d,(x1,y,x1+width,y+11),fill,fill,min(5,width//2),1)

def make_back(kind):
    im=Image.new("RGB",(W,H),BG)
    d=ImageDraw.Draw(im)
    for y in range(0,H,12):
        k=y/H
        d.rectangle((0,y,W,y+11),fill=(7,17+int(15*k),31+int(14*k)))
    for x in range(75,1010,80):
        line(d,[(x,355),(x,1320)],"#11283b",2)
    for y in range(370,1340,80):
        line(d,[(70,y),(1010,y)],"#11283b",2)
    txt(d,540,92,"EGI",69,CYAN,True)
    txt(d,540,155,"CURIOSITY IN MOTION",24,MUTED,True)
    title="WHY YOUR SSD MOVES DATA" if kind=="ssd" else "HOW A HEAT PIPE MOVES HEAT"
    txt(d,540,230,title,44,WHITE,True)
    txt(d,540,292,"STORAGE  /  CONTROLLER" if kind=="ssd" else "THERMAL ENGINEERING  /  PHASE CHANGE",25,MUTED)
    box(d,(65,352,1015,1375),"#102538","#294b63",29,3)
    txt(d,540,1815,"ORIGINAL PROCEDURAL ENGINEERING VISUALIZATION",23,"#7b9aad")
    txt(d,540,1870,"Ekrem Gökberk ISCAN",29,"#a3cadd")
    return im

PHASES={
"ssd":[
(0,4,"A FILE IS SAVED","One logical address, many physical locations","LOGICAL FILE A"),
(4,10,"HOST SENDS WRITE REQUESTS","The controller receives a queue of data","WRITE QUEUE"),
(10,16,"FLASH BLOCKS EXPERIENCE WEAR","Repeated program/erase cycles are tracked","ERASE COUNTERS"),
(16,23,"THE CONTROLLER UPDATES ITS MAP","Logical address A is redirected to block P07","ADDRESS MAPPING"),
(23,28,"WRITES ARE DISTRIBUTED","Different physical blocks receive new writes","WEAR DISTRIBUTION"),
(28,32,"SAME FILE, DIFFERENT PHYSICAL BLOCK","Logical identity remains constant after remapping","STATE PERSISTS")],
"heat":[
(0,5,"HEAT ENTERS THE EVAPORATOR","The chip warms liquid inside a sealed pipe","THERMAL INPUT"),
(5,10,"LIQUID ABSORBS HEAT","Evaporation converts liquid into vapor","PHASE CHANGE"),
(10,16,"VAPOR MOVES TO THE COOL END","Pressure difference moves vapor to condenser","VAPOR FLOW"),
(16,22,"HEAT LEAVES THROUGH THE FINS","Vapor condenses and releases latent heat","CONDENSATION"),
(22,28,"THE WICK RETURNS LIQUID","Capillary action returns fluid to the hot end","LIQUID RETURN"),
(28,32,"THE CYCLE CONTINUES","Evaporate, condense and wick back","CLOSED CYCLE")]
}

def phase(kind,t):
    for i,(start,end,head,desc,flag) in enumerate(PHASES[kind]):
        if start <= t < end or (i==len(PHASES[kind])-1 and t<=end):
            return i, start, end, head, desc, flag
    raise AssertionError("timeline hole")

def animate_title(d,kind,t):
    idx,begin,end,head,desc,flag=phase(kind,t)
    # Single event-owned explanation; never composite V12/V13 cards.
    fade=min(ease((t-begin)/.28),ease((end-t)/.3))
    box(d,(72,1450,1008,1648),"#14354b","#477d92",24,3)
    dot(d,112,1490,12,AMBER if kind=="heat" else CYAN)
    txt(d,155,1490,flag,22,CYAN if kind=="ssd" else AMBER,True,anchor="lm")
    txt(d,540,1547,head,32,WHITE,True)
    txt(d,540,1597,desc,24,"#afccdb")
    bar(d,83,1697,995,CYAN if kind=="ssd" else AMBER,t/DUR)
    txt(d,540,1732,"STEP %d / 6"%(idx+1),24,MUTED,True)
    # meaningful changing phase label is a single temporary card
    assert len([p for p in PHASES[kind] if p[0]<=t<p[1]])<=1
    return idx,begin,end

def packet(d,x,y,t,index,color=CYAN):
    wobble=4*math.sin(t*6+index)
    box(d,(x-36,y-19+wobble,x+36,y+19+wobble),"#19475d",color,9,2)
    line(d,[(x-24,y+wobble),(x+23,y+wobble)],color,3)
    dot(d,x+23,y+wobble,4,WHITE)

def ssd_frame(t,back):
    im=back.copy()
    d=ImageDraw.Draw(im)
    idx,begin,end,_,_,_=phase("ssd",t)
    # Host file persists, but the bytes and their physical destinations change.
    box(d,(105,428,375,568),"#142f46","#4ea8c2",22)
    txt(d,240,472,"HOST STORAGE",24,MUTED,True)
    txt(d,240,520,"FILE A  •  LBA 42",30,WHITE,True)
    box(d,(700,428,975,568),"#163548","#6dc1c9",22)
    txt(d,839,471,"CONTROLLER",26,WHITE,True)
    txt(d,839,516,"FTL  /  WEAR MAP",24,GREEN,True)
    arrow(d,385,496,689,496,CYAN,7)
    for k in range(3):
        f=((t*.45+k/3)%1)
        packet(d,410+250*f,495,t,k)
    box(d,(114,610,966,1175),"#0d2234","#42667c",25)
    txt(d,540,655,"NAND FLASH  •  PHYSICAL ERASE BLOCKS",27,"#c6e6f4",True)
    coords={}
    for n in range(12):
        c,r=n%4,n//4
        x,y=230+c*210,755+r*145
        coords[n]=(x,y)
        hot=n in (0,1,2)
        selected=(n==0 and t<18) or (n==7 and t>=18)
        color="#1c4157" if not selected else ("#77543a" if n==0 else "#1b655c")
        outline=AMBER if n==0 and t>=10 else (GREEN if n==7 and t>=16 else "#527b90")
        box(d,(x-78,y-43,x+78,y+48),color,outline,15)
        txt(d,x,y-9,"P%02d"%n,30,WHITE,True)
        # Per-cell persistent wear meters; no fake exact lifetime value.
        pct=(.17+.09*(n%4))+(0.13*ease((t-10)/5) if hot else .01*ease((t-23)/5))
        bar(d,x-57,y+20,x+57,AMBER if hot else GREEN,pct)
        if t>10 and n<3:
            for k in range(2):
                dot(d,x-58+k*116,y-36,4+3*abs(math.sin(t*3+k)),AMBER)
    # Logical-to-physical map is persistent and changes exactly once.
    box(d,(126,1232,954,1342),"#193950","#51849a",18)
    mapped="P00" if t<18 else "P07"
    txt(d,285,1270,"LBA 42  /  FILE A",28,WHITE,True)
    arrow(d,500,1280,622,1280,GREEN,7)
    txt(d,758,1275,mapped,37,GREEN if t>=18 else AMBER,True)
    if 10<=t<16:
        # Erase-count snapshots ripple through the hottest chips
        for k in range(4):
            f=((t-10)*.65+k/4)%1
            x=coords[k%3][0]
            y=coords[k%3][1]
            ring(d,x,y,50+28*f,AMBER,3)
    if 16<=t<23:
        f=ease((t-16)/7)
        x1,y1=coords[0];x2,y2=coords[7]
        arrow(d,x1,y1+52,x2,y2-50,GREEN,5)
        dot(d,mix(x1,x2,f),mix(y1+52,y2-50,f),19,GREEN)
        ring(d,x2,y2,50+18*abs(math.sin(t*3)),GREEN,4)
        txt(d,540,1188,"FTL UPDATE  •  LBA 42 → P07",25,GREEN,True)
    if t>=23:
        for k in range(9):
            n=[3,6,8,10,7,5,11,9,4][k]
            x,y=coords[n]
            f=((t-23)*.31+k/9)%1
            dot(d,x+50*math.sin(f*2*math.pi),y-18+8*math.cos(f*2*math.pi),6,GREEN)
        txt(d,540,1188,"DYNAMIC WEAR LEVELING (SIMPLIFIED)",23,GREEN,True)
    animate_title(d,"ssd",t)
    return im

def heat_frame(t,back):
    im=back.copy()
    d=ImageDraw.Draw(im)
    idx,begin,end,_,_,_=phase("heat",t)
    box(d,(110,455,370,590),"#5e302b","#e78f65",20)
    txt(d,240,490,"HOT CHIP",31,WHITE,True)
    temp="HIGH HEAT INPUT" if t>=2 else "STARTUP"
    txt(d,240,542,temp,19,AMBER,True)
    for i in range(6):
        x=225+i*122
        box(d,(x-42,1070,x+42,1228),"#244d64","#619ab0",10)
        for k in range(3):
            line(d,[(x-32,1102+k*36),(x+32,1102+k*36)],"#588ba5",3)
    txt(d,550,1258,"EXTERNAL COOLING FINS  •  HEAT SINK",24,"#8cbdce",True)
    box(d,(108,649,982,1038),"#89513a","#eab581",70,9)
    box(d,(135,675,955,1008),"#285263","#eab581",65,8)
    # continuous wick bands, colored blue: liquid returns along the inside wall
    box(d,(159,708,933,751),"#356e84","#5aacc3",16,2)
    box(d,(159,934,933,975),"#356e84","#5aacc3",16,2)
    box(d,(205,774,889,910),"#173449","#508296",40,3)
    txt(d,540,824,"SEALED VAPOR CHANNEL",30,WHITE,True)
    txt(d,240,627,"EVAPORATOR",27,AMBER,True)
    txt(d,826,627,"CONDENSER",27,CYAN,True)
    # Physically distinct channels/directions, not the same stream.
    arrow(d,300,876,800,876,AMBER,6)
    arrow(d,810,954,260,954,CYAN,5)
    arrow(d,215,1040,215,996,AMBER,8)
    arrow(d,850,1030,850,1065,CYAN,8)
    # heat enters from hot chip; the exchanger rejects heat into fins
    for k in range(5):
        u=((t*.45+k/5)%1)
        x=175+88*(k/4)
        y=635+40*math.sin(u*2*math.pi)
        ring(d,x,y,10+14*u,AMBER,2)
        dot(d,x,y,5,AMBER)
    for k in range(4):
        u=((t*.31+k/4)%1)
        x=785+55*k/4
        y=1010+100*u
        dot(d,x,y,8,AMBER)
        arrow(d,x,y+7,x,y+20,AMBER,3)
    if t>=5:
        # liquid near warm end -> expanding vapor bubbles
        for k in range(8):
            f=((t-5)*.8+k/8)%1
            x=210+115*math.sin((k+1)*1.7)
            y=890-115*f
            ring(d,x,y,5+12*f,AMBER,2)
    if t>=10:
        for k in range(14):
            f=((t-10)*.19+k/14)%1
            x=255+590*f
            y=837+20*math.sin(t*2.6+k*1.6)
            dot(d,x,y,5+6*(1-f),AMBER)
            if k%3==0: ring(d,x,y,12+8*f,AMBER,2)
    if t>=16:
        for k in range(7):
            f=((t-16)*.27+k/7)%1
            x=810+45*math.sin(k*2)
            y=832+90*f
            dot(d,x,y,6+6*(1-f),CYAN)
        for k in range(5):
            f=((t-16)*.2+k/5)%1
            ring(d,800+30*k/4,1050+90*f,7+11*f,CYAN,2)
    if t>=22:
        for k in range(14):
            f=((t-22)*.21+k/14)%1
            x=810-575*f
            y=958+6*math.sin(t*4+k)
            dot(d,x,y,7,CYAN)
            if k%3==0:ring(d,x,y,15,CYAN,2)
    # state mini-cards always visible, meaningful evolving status
    box(d,(112,1280,482,1356),"#1b3b4f","#4b7990",14)
    box(d,(599,1280,972,1356),"#1b3b4f","#4b7990",14)
    txt(d,295,1310,"VAPOR  →",27,AMBER,True)
    txt(d,785,1310,"←  LIQUID / WICK",25,CYAN,True)
    bar(d,150,1331,445,AMBER,0 if t<5 else ease((t-5)/8))
    bar(d,630,1331,930,CYAN,0 if t<16 else ease((t-16)/8))
    animate_title(d,"heat",t)
    return im

def make_audio(path,kind):
    sr=44100
    samples=np.zeros(round(sr*DUR),dtype=np.float32)
    transitions=[0.5,4,10,16,23,28] if kind=="ssd" else [.5,5,10,16,22,28]
    freq=[440,650,370,780,520,620] if kind=="ssd" else [220,310,420,550,340,260]
    # very soft continuous ambience, sound cues mark real changes
    tt=np.arange(len(samples),dtype=np.float32)/sr
    samples+=.009*np.sin(2*np.pi*(75 if kind=="ssd" else 60)*tt)
    for k,(at,f) in enumerate(zip(transitions,freq)):
        start=int(sr*at);n=int(sr*.34)
        t=np.arange(n,dtype=np.float32)/sr
        envelope=(1-np.exp(-t*80))*np.exp(-t*11)
        samples[start:start+n]+=.115*np.sin(2*np.pi*(f*t+120*t*t))*envelope
    for at in np.arange(1.0,DUR,1.45):
        ix=int(at*sr)
        n=int(sr*.065)
        t=np.arange(n,dtype=np.float32)/sr
        samples[ix:ix+n]+=.033*np.sin(2*np.pi*980*t)*np.exp(-t*62)
    samples=np.clip(samples,-.8,.8)
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes((samples*32767).astype("<i2").tobytes())

def run(kind,out,full=True):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    back=make_back(kind)
    make_audio(out/(kind+"_premium.wav"),kind)
    mp4=out/(kind+"_premium.mp4")
    ff=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24",
        "-s",f"{W}x{H}","-r",str(FPS),"-i","pipe:0",
        "-i",str(out/(kind+"_premium.wav")),"-c:v","libx264","-preset","veryfast",
        "-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
        "-t",str(DUR),"-movflags","+faststart",str(mp4)]
    n=FPS*DUR if full else FPS*3
    snapshots=[0,4,8,12,17,24,30]
    p=subprocess.Popen(ff,stdin=subprocess.PIPE)
    try:
        for i in range(n):
            t=i/FPS
            im=ssd_frame(t,back) if kind=="ssd" else heat_frame(t,back)
            if i in {round(s*FPS) for s in snapshots}:
                im.save(out/(f"{kind}_premium_frame_{int(t):02d}.png"))
            p.stdin.write(im.tobytes())
    finally:
        p.stdin.close()
    assert p.wait()==0,"FFmpeg failed"
    meta=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(mp4)]))
    video=[s for s in meta["streams"] if s["codec_type"]=="video"]
    audio=[s for s in meta["streams"] if s["codec_type"]=="audio"]
    assert len(video)==len(audio)==1
    v=video[0];a=audio[0]
    assert (v["width"],v["height"],v["codec_name"],v["r_frame_rate"])==(W,H,"h264","30/1")
    assert a["codec_name"]=="aac"
    if full: assert abs(float(meta["format"]["duration"])-DUR)<.12
    result={"episode_id": "egi-ssd-wear-leveling-v16" if kind=="ssd" else "egi-heat-pipe-phase-change-v16",
            "duration":float(meta["format"]["duration"]),"width":W,"height":H,"fps":FPS,
            "sha256":hashlib.sha256(mp4.read_bytes()).hexdigest(),"full":full}
    (out/(kind+"_premium_qa.json")).write_text(json.dumps(result,indent=2)+"\n")
    print("EGI_PREMIUM_OK",json.dumps(result),flush=True)
    return result

def check():
    # Every timeline boundary, first and last frame: one and only one explanatory stage.
    for kind in ("ssd","heat"):
        b=make_back(kind)
        for t in [0,.001,1/FPS,1,3.99,4,4.01,5,9.99,10,15.99,16,21.99,22,23,27.99,28,31.99]:
            assert phase(kind,t)[0] in range(6)
            im=ssd_frame(t,b) if kind=="ssd" else heat_frame(t,b)
            assert im.mode=="RGB" and im.size==(W,H)
        for a,b,head,desc,flag in PHASES[kind]:
            assert head and desc and flag and b>a
        assert PHASES[kind][0][0]==0 and PHASES[kind][-1][1]==DUR
        assert all(PHASES[kind][i][1]==PHASES[kind][i+1][0] for i in range(5))
    print("EGI_PREMIUM_BOUNDARY_QA_PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--kind",choices=["ssd","heat","both","check"],default="both")
    parser.add_argument("--out",default="outputs/egi_rd_premium")
    parser.add_argument("--smoke",action="store_true")
    opt=parser.parse_args()
    check()
    if opt.kind!="check":
        for item in (["ssd","heat"] if opt.kind=="both" else [opt.kind]):
            run(item,opt.out,full=not opt.smoke)
