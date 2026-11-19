#!/usr/bin/env python3
"""EGI original causal animations. R&D only; no catalog/publisher integration."""
import argparse, math, os, subprocess, wave, hashlib, json, time
from PIL import Image, ImageDraw, ImageFont
import numpy as np

W,H,FPS,DURATION=1080,1920,30,9
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(n,b=False): return ImageFont.truetype(BOLD if b else FONT,n)
def clamp(v): return max(0,min(1,v))
def smooth(v): v=clamp(v); return v*v*(3-2*v)
def mix(a,b,t): return a+(b-a)*t
def text(d,xy,s,size=42,fill="#eaf5ff",bold=False,anchor="mm"):
    d.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor,stroke_width=0)
def rect(d,xy,fill,outline=None,width=3,r=22):
    d.rounded_rectangle(xy,radius=r,fill=fill,outline=outline,width=width)
def pulse(d,x,y,r,color):
    d.ellipse((x-r,y-r,x+r,y+r),fill=color)
def arrow(d,a,b,color="#67e6ff",width=10):
    d.line((a,b),fill=color,width=width)
    angle=math.atan2(b[1]-a[1],b[0]-a[0])
    p=(b[0]-25*math.cos(angle),b[1]-25*math.sin(angle))
    d.polygon([b,(p[0]+14*math.sin(angle),p[1]-14*math.cos(angle)),(p[0]-14*math.sin(angle),p[1]+14*math.cos(angle))],fill=color)
def base(title,category):
    im=Image.new("RGB",(W,H),"#081525"); d=ImageDraw.Draw(im)
    for y in range(0,H,16):
        v=int(10+12*y/H)
        d.rectangle((0,y,W,y+16),fill=(7,v,29+int(11*y/H)))
    text(d,(540,100),"EGI",68,"#69e6fa",True)
    text(d,(540,163),"CURIOSITY IN MOTION",27,"#a4bacb",True)
    text(d,(540,274),title,53,"#ffffff",True)
    text(d,(540,350),category.upper(),27,"#78d7e6")
    d.line((120,390,960,390),fill="#27536b",width=3)
    text(d,(540,1792),"EGI  •  Original procedural illustration",26,"#8aa4b6")
    text(d,(540,1850),"Ekrem Gökberk ISCAN",27,"#82b5c5")
    return im,d
def progress(d,t):
    d.rounded_rectangle((130,1690,950,1704),radius=7,fill="#183c50")
    filled = round(820 * clamp(t / DURATION))
    # At t=0 (or before the first visible pixel), do not draw a zero-width
    # rounded rectangle. Radius must also fit very narrow early frames.
    if filled > 0:
        d.rounded_rectangle(
            (130,1690,130+filled,1704),
            radius=min(7, filled // 2),
            fill="#50d9f0"
        )
def one_callout(d,t,events):
    active=[(a,b,msg) for a,b,msg in events if a<=t<b]
    assert len(active)<=1, "overlapping callouts"
    if active:
        a,b,msg=active[0]
        alpha=min(smooth((t-a)/.22),smooth((b-t)/.22))
        if alpha>.05:
            rect(d,(105,1490,975,1600),"#17354a",outline="#3b91a8")
            text(d,(540,1545),msg,36,"#e7f8ff",True)
def ssd(t):
    im,d=base("Why SSDs Move Your Data","software  /  storage")
    rect(d,(90,480,990,1300),"#10283c",outline="#477087",r=30)
    text(d,(540,530),"FLASH CONTROLLER",40,"#9de8fa",True)
    cells=[(170+c*183,650+r*150) for r in range(3) for c in range(4)]
    for i,(x,y) in enumerate(cells):
        is_hot=i in (0,1,2)
        # physical erase-block locations persist; logical data can move
        fill="#25455d"
        if t>=2.8 and i==0: fill="#553c43"
        if t>=4.5 and i==7: fill="#236e68"
        rect(d,(x-65,y-48,x+65,y+48),fill,outline="#5c8196",r=12)
        text(d,(x,y-5),f"P{i:02d}",29,"#d4e8f4",True)
        if is_hot and t<2.8:
            pulse(d,x+45,y-31,8,"#ffbd6b")
    text(d,(540,1195),"PHYSICAL FLASH BLOCKS",30,"#9eb8c8")
    # A logical address remains unchanged as its mapping changes
    rect(d,(145,1340,935,1450),"#1b3448",outline="#467d91")
    text(d,(540,1375),"LOGICAL FILE: A",35,"#ffffff",True)
    target=0 if t<3.7 else 7
    text(d,(540,1422),f"MAPS TO P{target:02d}",28,"#68e6cc",True)
    if .8<t<2.8:
        n=int((t-.8)*5)
        for j in range(min(n,9)):
            pulse(d,300+j*51,1020,10,"#ffbd6b")
    if 3.0<t<4.5:
        f=smooth((t-3)/1.5)
        x=mix(cells[0][0],cells[7][0],f); y=mix(cells[0][1],cells[7][1],f)
        pulse(d,x,y,29,"#5ee5cb")
        arrow(d,(cells[0][0],cells[0][1]+65),(cells[7][0],cells[7][1]-65),"#5ee5cb",6)
    if t>=5:
        for i,(x,y) in enumerate(cells):
            # indicate even wear distribution, not literal cell health
            d.rectangle((x-44,y+28,x-44+int((15+(i%4)*9)),y+35),fill="#64d3d0")
    events=[(.5,2.8,"Repeated writes stress the same block"),(3.0,4.9,"Controller remaps logical data"),(5.0,8.6,"Writes spread across physical blocks")]
    one_callout(d,t,events);progress(d,t)
    return im
def heat(t):
    im,d=base("How a Heat Pipe Moves Heat","physics  /  engineering")
    rect(d,(90,505,990,1260),"#12283a",outline="#537d93",r=30)
    # sealed copper pipe with wick and distinct liquid/vapor paths
    rect(d,(170,745,910,1050),"#88502e",outline="#e0a86d",width=8,r=80)
    rect(d,(190,777,890,1019),"#2e4e5b",outline="#e7b26e",width=5,r=65)
    rect(d,(212,803,868,839),"#459ab2",r=12)
    rect(d,(212,960,868,997),"#459ab2",r=12)
    text(d,(260,697),"EVAPORATOR",30,"#ffb979",True)
    text(d,(814,697),"CONDENSER",30,"#78dffc",True)
    text(d,(540,907),"VAPOR CHANNEL",33,"#dceef7",True)
    # source heat and sink fins remain separate and physically placed
    rect(d,(120,1090,360,1180),"#873b30",outline="#f6a16e")
    text(d,(240,1135),"HOT CHIP",29,"#fff3e8",True)
    for x in range(750,925,37):
        d.rectangle((x,1090,x+15,1210),fill="#477f96")
    text(d,(830,1260),"COOLING FINS",28,"#8fdaf4")
    arrow(d,(250,1090),(250,1040),"#ff9b67",9)
    arrow(d,(830,1040),(830,1090),"#7fdaf9",9)
    if t>=1.4:
        f=((t-1.4)*.30)%1
        # vapor travels hot -> cold
        for j in range(5):
            x=245+570*((f+j/5)%1)
            pulse(d,x,910,13,"#ffb56e")
        arrow(d,(350,870),(710,870),"#ffb56e",7)
    if t>=3.4:
        for j in range(4):
            x=790-j*19; y=855+j*38
            pulse(d,x,y,11,"#79dafa")
    if t>=5.1:
        f=((t-5.1)*.25)%1
        for j in range(6):
            x=810-560*((f+j/6)%1)
            pulse(d,x,980,10,"#6cd8ee")
        arrow(d,(720,978),(340,978),"#70d8f1",7)
    text(d,(540,1355),"SEALED PIPE  •  WICK RETURN",32,"#d5e7f0",True)
    events=[(.5,2.8,"Heat evaporates working fluid"),(3.0,5.0,"Vapor condenses at the cool end"),(5.1,8.6,"Wick returns liquid by capillary action")]
    one_callout(d,t,events);progress(d,t)
    return im
def audio(path,kind):
    sr=44100;n=int(sr*DURATION);arr=np.zeros(n,dtype=np.float32)
    events=([(.8,540),(2.9,350),(3.7,760),(5.0,440)] if kind=="ssd" else [(1.4,280),(3.4,620),(5.1,370),(7.3,490)])
    for at,freq in events:
        length=.16; m=int(sr*length); idx=int(at*sr)
        x=np.arange(m)/sr; env=np.exp(-22*x)
        arr[idx:idx+m]+=0.14*env*np.sin(2*np.pi*(freq*x+110*x*x))
    arr=np.clip(arr,-.7,.7)
    with wave.open(path,"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr)
        w.writeframes((arr*32767).astype("<i2").tobytes())
def render(kind,out,seconds=DURATION):
    assert kind in ("ssd","heat")
    os.makedirs(out,exist_ok=True)
    wav=os.path.join(out,kind+".wav");mp4=os.path.join(out,kind+".mp4")
    audio(wav,kind)
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","pipe:0","-i",wav,"-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",mp4]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    start=time.monotonic(); count=int(seconds*FPS)
    for i in range(count):
        frame=(ssd(i/FPS) if kind=="ssd" else heat(i/FPS))
        if i in (0,int(2*FPS),int(4*FPS),int(7*FPS)):
            frame.save(os.path.join(out,f"{kind}_frame_{i:03d}.png"))
        p.stdin.write(frame.tobytes())
    p.stdin.close();rc=p.wait()
    assert rc==0 and os.path.getsize(mp4)>50000,"invalid/empty video"
    probe=subprocess.check_output(["ffprobe","-v","error","-show_entries","stream=codec_name,width,height","-of","json",mp4],text=True)
    streams=json.loads(probe)["streams"]
    assert any(x.get("codec_name")=="h264" and x.get("width")==W and x.get("height")==H for x in streams)
    assert any(x.get("codec_name")=="aac" for x in streams)
    result={"episode_id":"egi-ssd-wear-leveling-v16" if kind=="ssd" else "egi-heat-pipe-phase-change-v16","seconds":seconds,"frames":count,"sha256":hashlib.sha256(open(mp4,"rb").read()).hexdigest(),"render_seconds":round(time.monotonic()-start,2)}
    with open(os.path.join(out,kind+"_qa.json"),"w") as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--kind",choices=["ssd","heat","both"],default="both");a.add_argument("--out",default="outputs/egi_rd");a.add_argument("--seconds",type=float,default=9)
    args=a.parse_args()
    for kind in (["ssd","heat"] if args.kind=="both" else [args.kind]):render(kind,args.out,args.seconds)
