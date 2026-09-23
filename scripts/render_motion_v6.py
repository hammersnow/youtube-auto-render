#!/usr/bin/env python3
from pathlib import Path
import cv2, numpy as np, math, wave, subprocess, json, hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

OUT = Path("outputs/latest")
OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS, D = 1080, 1920, 30, 8
DAY = datetime.now(ZoneInfo("Europe/Istanbul"))
SEED = int(DAY.strftime("%Y%m%d"))
FONT = cv2.FONT_HERSHEY_SIMPLEX

def set_timing(duration, reveal):
    global ACTIVE_DURATION, ACTIVE_REVEAL
    ACTIVE_DURATION = float(duration)
    ACTIVE_REVEAL = float(reveal)

PALETTES = [
    ((10, 16, 35), (38, 20, 72), (245, 185, 70)),
    ((6, 28, 34), (16, 64, 66), (80, 235, 190)),
    ((35, 12, 34), (58, 22, 74), (230, 115, 245)),
    ((24, 22, 8), (58, 54, 18), (80, 215, 250)),
    ((12, 18, 30), (18, 48, 70), (245, 150, 75)),
]
_GRADIENT_CACHE = {}

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def smoothstep(x):
    x = clamp(x, 0.0, 1.0)
    return x*x*(3.0-2.0*x)

def centered_text(im, s, y, sc=1.35, col=(245,245,245), th=3):
    (w,_),_ = cv2.getTextSize(s, FONT, sc, th)
    cv2.putText(im, s, ((W-w)//2, y), FONT, sc, col, th, cv2.LINE_AA)

def gradient(a, b):
    key = (a, b)
    if key not in _GRADIENT_CACHE:
        yy = np.linspace(0,1,H,dtype=np.float32)[:,None,None]
        A = np.array(a,np.float32)[None,None,:]
        B = np.array(b,np.float32)[None,None,:]
        _GRADIENT_CACHE[key] = (A*(1-yy)+B*yy+np.zeros((1,W,1),np.float32)).clip(0,255).astype(np.uint8)
    return _GRADIENT_CACHE[key].copy()

def scene(seed, palette_index, t):
    a,b,accent = PALETTES[palette_index % len(PALETTES)]
    im = gradient(a,b)
    rng = np.random.default_rng(seed + palette_index*101)
    for i in range(20):
        x = int(rng.integers(35,W-35))
        y0 = int(rng.integers(260,H-160))
        speed = 12 + int(rng.integers(0,24))
        y = int((y0 + speed*t) % (H-300)) + 190
        r = 2 + (i % 3)
        col = tuple(int(c*0.42) for c in accent)
        cv2.circle(im,(x,y),r,col,-1,cv2.LINE_AA)
    return im, accent

def draw_timer(im, t, accent, style=0):
    if not (SOLVE_START <= t < ACTIVE_REVEAL):
        return
    p = clamp((t-SOLVE_START)/max(0.1,ACTIVE_REVEAL-SOLVE_START),0,1)
    remain = 1.0-p
    if style % 3 == 0:
        cv2.rectangle(im,(150,1640),(930,1660),(55,60,78),-1)
        cv2.rectangle(im,(150,1640),(150+int(780*remain),1660),accent,-1)
    elif style % 3 == 1:
        center=(540,1642); r=58
        cv2.circle(im,center,r,(55,60,78),9,cv2.LINE_AA)
        cv2.ellipse(im,center,(r,r),-90,0,360*remain,accent,9,cv2.LINE_AA)
    else:
        y=1645
        for i in range(10):
            x=315+i*50
            on=(i/10.0)<remain
            cv2.circle(im,(x,y),8,accent if on else (55,60,78),-1,cv2.LINE_AA)

def reveal_burst(im, x, y, t, col=(70,245,120)):
    reveal_span=max(0.6,ACTIVE_DURATION-ACTIVE_REVEAL-0.3)
    if ACTIVE_REVEAL <= t < ACTIVE_REVEAL+reveal_span:
        q = (t-ACTIVE_REVEAL)/reveal_span
        r = 55 + int(70*q)
        cv2.circle(im,(int(x),int(y)),r,col,8,cv2.LINE_AA)
        if q < 0.45:
            cv2.circle(im,(int(x),int(y)),r+28,col,3,cv2.LINE_AA)

def rounded_card(im, x, y, w, h, col, border=(235,240,250), th=3):
    x1,y1,x2,y2 = int(x-w/2),int(y-h/2),int(x+w/2),int(y+h/2)
    cv2.rectangle(im,(x1+18,y1),(x2-18,y2),col,-1)
    cv2.rectangle(im,(x1,y1+18),(x2,y2-18),col,-1)
    for cx,cy in [(x1+18,y1+18),(x2-18,y1+18),(x1+18,y2-18),(x2-18,y2-18)]:
        cv2.circle(im,(cx,cy),18,col,-1,cv2.LINE_AA)
    cv2.rectangle(im,(x1+12,y1),(x2-12,y2),border,th,cv2.LINE_AA)

def memory_shuffle(t, seed):
    im,accent = scene(seed,0,t)
    centered_text(im,"FOLLOW THE HIDDEN ORB",205,1.20)
    slots=[(250,930),(540,930),(830,930)]
    target=seed%3
    rng=np.random.default_rng(seed+17)
    choices=[(0,1),(1,2),(0,2)]
    swaps=[choices[int(rng.integers(0,len(choices)))] for _ in range(5)]
    perm=[0,1,2]
    pos={i:[float(slots[i][0]),float(slots[i][1])] for i in range(3)}
    start=1.35; end=ACTIVE_REVEAL-0.25
    if t >= start:
        u=clamp((t-start)/(end-start),0,0.999999)
        seg=min(4,int(u*5))
        local=smoothstep(u*5-seg)
        for k in range(seg):
            a,b=swaps[k]; perm[a],perm[b]=perm[b],perm[a]
        for sidx,obj in enumerate(perm):
            pos[obj]=[float(slots[sidx][0]),float(slots[sidx][1])]
        a,b=swaps[seg]
        oa,ob=perm[a],perm[b]
        ax,ay=slots[a]; bx,by=slots[b]
        arc=-120*math.sin(math.pi*local)
        pos[oa]=[ax+(bx-ax)*local, ay+arc]
        pos[ob]=[bx+(ax-bx)*local, by-arc]
        if t >= end:
            perm=[0,1,2]
            for a,b in swaps:
                perm[a],perm[b]=perm[b],perm[a]
            for sidx,obj in enumerate(perm):
                pos[obj]=[float(slots[sidx][0]),float(slots[sidx][1])]
    for obj in range(3):
        x,y=pos[obj]
        rounded_card(im,x,y,190,250,(35,42,66))
        if t < 1.25 and obj==target:
            cv2.circle(im,(int(x),int(y)),40,(70,245,120),-1,cv2.LINE_AA)
            cv2.circle(im,(int(x),int(y)),55,(210,255,225),4,cv2.LINE_AA)
        else:
            centered="?"
            (tw,_),_=cv2.getTextSize(centered,FONT,1.6,4)
            cv2.putText(im,centered,(int(x-tw/2),int(y+18)),FONT,1.6,(215,220,235),4,cv2.LINE_AA)
    if t>=ACTIVE_REVEAL:
        final=[0,1,2]
        for a,b in swaps:
            final[a],final[b]=final[b],final[a]
        target_slot=final.index(target)
        x,y=slots[target_slot]
        cv2.circle(im,(x,y+165),42,(70,245,120),-1,cv2.LINE_AA)
        centered_text(im,"THERE IT IS",1515,1.35,(70,245,120),4)
        reveal_burst(im,x,y,t)
    draw_timer(im,t,accent,0)
    return im

def tracking_positions(t, seed):
    pts=[]
    for i in range(5):
        ph=(seed%97)*0.031+i*1.256
        x=540+285*math.sin(0.82*t+ph)+90*math.sin(1.72*t+ph*0.7)
        y=930+350*math.sin(0.61*t+ph*1.45)+95*math.cos(1.38*t+ph)
        pts.append((int(clamp(x,125,955)),int(clamp(y,430,1450))))
    return pts

def object_tracking(t, seed):
    im,accent = scene(seed,1,t)
    centered_text(im,"TRACK THE TARGET",205,1.28)
    target=seed%5
    pts=tracking_positions(t,seed)
    for i,(x,y) in enumerate(pts):
        trail=[]
        for k in range(6,0,-1):
            tt=max(0,t-k*0.055)
            trail.append(tracking_positions(tt,seed)[i])
        trail.append((x,y))
        cv2.polylines(im,[np.array(trail,np.int32)],False,(45,105,110),3,cv2.LINE_AA)
        cv2.circle(im,(x,y),34,(225,225,230),-1,cv2.LINE_AA)
        cv2.circle(im,(x,y),15,accent,-1,cv2.LINE_AA)
    x,y=pts[target]
    if t<1.25:
        cv2.circle(im,(x,y),64,(70,245,120),7,cv2.LINE_AA)
        centered_text(im,"DON'T LOSE THIS ONE",1515,0.95,(70,245,120),3)
    if t>=ACTIVE_REVEAL:
        cv2.circle(im,(x,y),68,(70,245,120),9,cv2.LINE_AA)
        centered_text(im,"TARGET FOUND",1515,1.25,(70,245,120),4)
        reveal_burst(im,x,y,t)
    draw_timer(im,t,accent,1)
    return im

def poly_point(points, q):
    q=clamp(q,0,1)
    lens=[]
    total=0.0
    for i in range(len(points)-1):
        dx=points[i+1][0]-points[i][0]; dy=points[i+1][1]-points[i][1]
        d=math.hypot(dx,dy); lens.append(d); total+=d
    dtarget=q*total
    acc=0.0
    for i,d in enumerate(lens):
        if acc+d>=dtarget:
            u=0 if d==0 else (dtarget-acc)/d
            x=points[i][0]+(points[i+1][0]-points[i][0])*u
            y=points[i][1]+(points[i+1][1]-points[i][1])*u
            return int(x),int(y)
        acc+=d
    return points[-1]

def animated_maze(t, seed):
    im,accent = scene(seed,2,t)
    centered_text(im,"WHICH SIGNAL REACHES THE CORE?",205,0.98)
    good=seed%4
    starts=[520,730,1030,1240]
    target=(900,930)
    routes=[]
    for i,y in enumerate(starts):
        mid1=(330,y+(-110 if i%2 else 105))
        mid2=(570,y+(80 if i%3 else -70))
        end=target if i==good else (820,430+i*300)
        routes.append([(135,y),mid1,mid2,end])
    for i,pts in enumerate(routes):
        cv2.polylines(im,[np.array(pts,np.int32)],False,(170,178,198),8,cv2.LINE_AA)
        cv2.putText(im,chr(65+i),(80,pts[0][1]+13),FONT,1.0,(245,245,245),3,cv2.LINE_AA)
        if 1.0<t<ACTIVE_REVEAL:
            q=((t-1.0)*0.32+i*0.13)%1.0
            px,py=poly_point(pts,q)
            cv2.circle(im,(px,py),17,accent,-1,cv2.LINE_AA)
            cv2.circle(im,(px,py),28,(235,220,250),2,cv2.LINE_AA)
    cv2.circle(im,target,48,(70,245,120),-1,cv2.LINE_AA)
    cv2.circle(im,target,70,(210,255,225),4,cv2.LINE_AA)
    if t>=ACTIVE_REVEAL:
        cv2.polylines(im,[np.array(routes[good],np.int32)],False,(70,245,120),15,cv2.LINE_AA)
        centered_text(im,"PATH %s"%chr(65+good),1515,1.45,(70,245,120),4)
        reveal_burst(im,target[0],target[1],t)
    draw_timer(im,t,accent,2)
    return im

def draw_symbol(im, kind, x, y, size, col, th=-1):
    x=int(x); y=int(y); size=max(5,int(size))
    if kind==0:
        cv2.circle(im,(x,y),size,col,th,cv2.LINE_AA)
    elif kind==1:
        cv2.rectangle(im,(x-size,y-size),(x+size,y+size),col,th,cv2.LINE_AA)
    elif kind==2:
        pts=np.array([[x,y-size],[x-size,y+size],[x+size,y+size]],np.int32)
        cv2.fillPoly(im,[pts],col,cv2.LINE_AA)
    elif kind==3:
        pts=np.array([[x,y-size],[x+size,y],[x,y+size],[x-size,y]],np.int32)
        cv2.fillPoly(im,[pts],col,cv2.LINE_AA)
    else:
        cv2.line(im,(x-size,y),(x+size,y),col,max(4,size//3),cv2.LINE_AA)
        cv2.line(im,(x,y-size),(x,y+size),col,max(4,size//3),cv2.LINE_AA)

def spot_difference(t, seed):
    im,accent = scene(seed,3,t)
    centered_text(im,"SPOT THE DIFFERENCE",205,1.28)
    left_x,right_x=105,575
    top=455; cell=105
    cv2.rectangle(im,(70,380),(505,1395),(230,235,245),3,cv2.LINE_AA)
    cv2.rectangle(im,(540,380),(975,1395),(230,235,245),3,cv2.LINE_AA)
    rng=np.random.default_rng(seed+55)
    kinds=[int(rng.integers(0,5)) for _ in range(32)]
    bad=seed%32
    for idx in range(32):
        r,c=divmod(idx,4)
        x1=left_x+c*105+45; y=top+r*205
        x2=right_x+c*105+45
        base=kinds[idx]
        pulse=1.0+0.07*math.sin(t*3.1+idx*0.6)
        sz=int(27*pulse)
        col=(90+((idx*31)%120),170,230)
        draw_symbol(im,base,x1,y,sz,col)
        k2=(base+1)%5 if idx==bad else base
        draw_symbol(im,k2,x2,y,sz,col)
    if 1.1<t<ACTIVE_REVEAL:
        q=(t-1.1)/max(0.1,ACTIVE_REVEAL-1.1)
        sx=int(80+390*q)
        cv2.line(im,(sx,400),(sx,1370),accent,3,cv2.LINE_AA)
        cv2.line(im,(sx+470,400),(sx+470,1370),accent,3,cv2.LINE_AA)
    br,bc=divmod(bad,4)
    bx=right_x+bc*105+45; by=top+br*205
    if t>=ACTIVE_REVEAL:
        centered_text(im,"FOUND IT",1515,1.35,(70,245,120),4)
        reveal_burst(im,bx,by,t)
        cv2.rectangle(im,(bx-52,by-52),(bx+52,by+52),(70,245,120),7,cv2.LINE_AA)
    draw_timer(im,t,accent,0)
    return im

def memory_symbol(im, idx, x, y, scale=1.0):
    colors=[(80,205,245),(245,145,75),(85,225,135),(225,105,235),(235,205,75),(120,180,245),(245,110,120),(150,235,215),(210,155,245)]
    kind=idx%5
    draw_symbol(im,kind,x,y,int(34*scale),colors[idx],-1)
    if idx>=5:
        cv2.circle(im,(int(x),int(y)),int(48*scale),(235,240,250),3,cv2.LINE_AA)

def visual_memory(t, seed):
    im,accent = scene(seed,4,t)
    missing=seed%9
    centers=[]
    for r in range(3):
        for c in range(3):
            centers.append((300+c*240,610+r*260))
    if t<2.25:
        centered_text(im,"MEMORIZE THE TILES",205,1.25)
        for idx,(x,y) in enumerate(centers):
            scale=1.0+0.08*math.sin(t*4+idx)
            rounded_card(im,x,y,150,150,(35,42,62),(115,125,155),2)
            memory_symbol(im,idx,x,y,scale)
        centered_text(im,"LOOK CLOSELY",1515,1.0,accent,3)
    elif t<2.65:
        centered_text(im,"MEMORIZE THE TILES",205,1.25)
        q=smoothstep((t-2.25)/0.40)
        cv2.rectangle(im,(0,int(H*(1-q))),(W,H),(20,22,34),-1)
    else:
        centered_text(im,"WHICH TILE VANISHED?",205,1.18)
        flip=min(1.0,(t-2.65)/0.35)
        for idx,(x,y) in enumerate(centers):
            if idx==missing:
                rounded_card(im,x,y,150,150,(28,31,48),(90,95,120),2)
                cv2.putText(im,"?",(x-29,y+31),FONT,1.8,(210,215,230),4,cv2.LINE_AA)
                continue
            rounded_card(im,x,y,max(18,int(150*flip)),150,(35,42,62),(115,125,155),2)
            if flip>0.42:
                memory_symbol(im,idx,x,y,1.0)
    if t>=ACTIVE_REVEAL:
        cv2.rectangle(im,(190,1420),(890,1605),(18,24,38),-1)
        centered_text(im,"MISSING TILE",1490,0.82,(220,225,235),2)
        memory_symbol(im,missing,540,1550,1.25)
        reveal_burst(im,540,1550,t)
    draw_timer(im,t,accent,1)
    return im


def moving_count(t, seed):
    im,accent = scene(seed,0,t)
    centered_text(im,"COUNT THE CYAN ORBS",205,1.22)
    target_n=5+(seed%4); total=15
    for i in range(total):
        ph=(seed%83)*0.027+i*0.73
        x=540+330*math.sin(0.72*t+ph)+70*math.sin(1.55*t+ph*0.5)
        y=930+390*math.cos(0.58*t+ph*1.23)+65*math.sin(1.31*t+ph)
        x=int(clamp(x,100,980)); y=int(clamp(y,390,1460))
        if i<target_n:
            col=(245,195,70)
        else:
            col=(105,95,235) if i%2 else (100,220,135)
        pulse=1.0+0.10*math.sin(t*4.0+i)
        cv2.circle(im,(x,y),int(25*pulse),col,-1,cv2.LINE_AA)
        cv2.circle(im,(x,y),int(34*pulse),(225,230,240),2,cv2.LINE_AA)
    if t>=ACTIVE_REVEAL:
        centered_text(im,"ANSWER: %d"%target_n,1515,1.55,(70,245,120),4)
    draw_timer(im,t,accent,2)
    return im

def rotate_points(points, angle, center, scale=1.0, mirror=False):
    ca,sa=math.cos(angle),math.sin(angle)
    out=[]
    for x,y in points:
        if mirror: x=-x
        x*=scale; y*=scale
        rx=x*ca-y*sa; ry=x*sa+y*ca
        out.append((int(center[0]+rx),int(center[1]+ry)))
    return np.array(out,np.int32)

def shadow_match(t, seed):
    im,accent = scene(seed,1,t)
    centered_text(im,"WHICH SHADOW MATCHES?",205,1.15)
    base=[(-95,-55),(10,-55),(10,-115),(125,0),(10,115),(10,55),(-95,55),(-55,0)]
    angle=t*0.72+(seed%7)*0.18
    main=rotate_points(base,angle,(540,650),1.45,False)
    cv2.fillPoly(im,[main],accent,cv2.LINE_AA)
    cv2.circle(im,(540,650),190,(220,225,240),3,cv2.LINE_AA)

    slots=[(180,1160),(420,1160),(660,1160),(900,1160)]
    correct=seed%4
    for i,(x,y) in enumerate(slots):
        variant=base
        mirror=False
        scale=.62
        if i!=correct:
            if (i+seed)%3==0:
                mirror=True
            elif (i+seed)%3==1:
                variant=list(base); variant[3]=(90,0)
            else:
                variant=list(base); variant[-1]=(-20,0)
        pts=rotate_points(variant,0,(x,y),scale,mirror)
        cv2.fillPoly(im,[pts],(95,105,125),cv2.LINE_AA)
        cv2.putText(im,chr(65+i),(x-18,y+150),FONT,1.0,(235,240,250),3,cv2.LINE_AA)
    if t>=ACTIVE_REVEAL:
        x,y=slots[correct]
        centered_text(im,"SHADOW %s"%chr(65+correct),1515,1.45,(70,245,120),4)
        reveal_burst(im,x,y,t)
    draw_timer(im,t,accent,0)
    return im

def sequence_next(t, seed):
    im,accent = scene(seed,2,t)
    centered_text(im,"WHAT COMES NEXT?",205,1.30)
    start=(seed%4)*45
    seq=[(start+i*90)%360 for i in range(4)]
    xs=[210,430,650,870]
    for i in range(4):
        rounded_card(im,xs[i],650,170,190,(32,38,58),(115,125,155),2)
        if i<3:
            ang=math.radians(seq[i])
            r=52
            x2=int(xs[i]+r*math.cos(ang)); y2=int(650+r*math.sin(ang))
            cv2.arrowedLine(im,(xs[i],650),(x2,y2),accent,9,cv2.LINE_AA,tipLength=.35)
        else:
            cv2.putText(im,"?",(xs[i]-27,675),FONT,1.8,(220,225,240),4,cv2.LINE_AA)

    options=[start%360,(start+90)%360,(start+180)%360,(start+270)%360]
    rng=np.random.default_rng(seed+91); rng.shuffle(options)
    correct_angle=seq[3]
    correct=options.index(correct_angle)
    ox=[180,420,660,900]
    for i,a in enumerate(options):
        rounded_card(im,ox[i],1160,165,175,(28,33,50),(100,110,140),2)
        ang=math.radians(a); r=48
        x2=int(ox[i]+r*math.cos(ang)); y2=int(1160+r*math.sin(ang))
        cv2.arrowedLine(im,(ox[i],1160),(x2,y2),(225,225,230),8,cv2.LINE_AA,tipLength=.35)
        cv2.putText(im,chr(65+i),(ox[i]-16,1300),FONT,.9,(235,240,250),2,cv2.LINE_AA)
    if t>=ACTIVE_REVEAL:
        x=ox[correct]
        cv2.rectangle(im,(x-92,1065),(x+92,1255),(70,245,120),7,cv2.LINE_AA)
        centered_text(im,"OPTION %s"%chr(65+correct),1515,1.35,(70,245,120),4)
        reveal_burst(im,x,1160,t)
    draw_timer(im,t,accent,1)
    return im

def color_memory(t, seed):
    im,accent = scene(seed,3,t)
    colors=[(80,205,245),(245,145,75),(85,225,135),(225,105,235)]
    labels=["CYAN","ORANGE","GREEN","PINK"]
    rng=np.random.default_rng(seed+123)
    order=list(range(4)); rng.shuffle(order)
    wanted=2
    if t<4.3:
        centered_text(im,"MEMORIZE THE COLORS",205,1.18)
        idx=int(clamp((t-.55)/.90,0,3))
        if t<.55: idx=0
        cidx=order[idx]
        pulse=1.0+0.10*math.sin(t*8)
        cv2.circle(im,(540,900),int(165*pulse),colors[cidx],-1,cv2.LINE_AA)
        cv2.circle(im,(540,900),215,(235,240,250),5,cv2.LINE_AA)
        centered_text(im,"COLOR %d"%(idx+1),1320,1.0,(220,225,235),3)
    else:
        centered_text(im,"WHICH COLOR WAS THIRD?",205,1.02)
        xs=[180,420,660,900]
        for i,(col,label) in enumerate(zip(colors,labels)):
            cv2.circle(im,(xs[i],930),72,col,-1,cv2.LINE_AA)
            cv2.putText(im,label,(xs[i]-72,1075),FONT,.55,(235,240,250),2,cv2.LINE_AA)
        correct=order[wanted]
        if t>=ACTIVE_REVEAL:
            x=xs[correct]
            reveal_burst(im,x,930,t)
            centered_text(im,labels[correct],1515,1.45,(70,245,120),4)
    draw_timer(im,t,accent,0)
    return im

def wrong_motion(t, seed):
    im,accent = scene(seed,4,t)
    centered_text(im,"WHICH ORB MOVES WRONG?",205,1.08)
    centers=[]
    for r in range(3):
        for c in range(3):
            centers.append((300+c*240,610+r*300))
    bad=seed%9
    for i,(cx,cy) in enumerate(centers):
        cv2.circle(im,(cx,cy),58,(65,72,92),2,cv2.LINE_AA)
        direction=-1 if i==bad else 1
        ang=direction*(t*2.6+i*.44)
        x=int(cx+48*math.cos(ang)); y=int(cy+48*math.sin(ang))
        cv2.circle(im,(x,y),18,accent,-1,cv2.LINE_AA)
        cv2.circle(im,(cx,cy),8,(225,230,240),-1,cv2.LINE_AA)
    if t>=ACTIVE_REVEAL:
        x,y=centers[bad]
        centered_text(im,"FOUND THE REVERSE ORBIT",1515,.92,(70,245,120),3)
        reveal_burst(im,x,y,t)
    draw_timer(im,t,accent,2)
    return im


def audio(path, freq, duration, reveal):
    sr=24000
    samples=int(sr*duration)
    tt=np.arange(samples,dtype=np.float32)/sr
    sig=.012*np.sin(2*np.pi*freq*tt)+.006*np.sin(2*np.pi*(freq/2.0)*tt)
    for sec in range(2,max(2,int(reveal))):
        start=int(sec*sr); n=min(int(.07*sr),samples-start)
        if n<=0: continue
        x=np.arange(n,dtype=np.float32)/sr
        env=np.linspace(1,0,n,dtype=np.float32)
        sig[start:start+n]+=.045*np.sin(2*np.pi*(freq*1.9)*x)*env
    start=int(reveal*sr); n=min(int(.30*sr),samples-start)
    if n>0:
        x=np.arange(n,dtype=np.float32)/sr
        env=np.linspace(1,0,n,dtype=np.float32)
        sig[start:start+n]+=.065*(np.sin(2*np.pi*(freq*2.25)*x)+.45*np.sin(2*np.pi*(freq*3.0)*x))*env
    sig=np.clip(sig,-.95,.95)
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((sig*32767).astype("<i2").tobytes())

def encode(name, fn, freq, seed, duration, reveal):
    set_timing(duration,reveal)
    raw=OUT/(name+"_raw.mp4"); wav=OUT/(name+".wav"); fin=OUT/(name+".mp4")
    v=cv2.VideoWriter(str(raw),cv2.VideoWriter_fourcc(*"mp4v"),FPS,(W,H))
    if not v.isOpened():
        raise RuntimeError("OpenCV VideoWriter failed for "+str(raw))
    for i in range(int(FPS*duration)):
        frame=fn(i/FPS,seed)
        if frame.shape!=(H,W,3):
            raise RuntimeError("Bad frame shape for "+name+": "+str(frame.shape))
        v.write(frame)
    v.release()
    audio(wav,freq,duration,reveal)
    subprocess.run([
        "ffmpeg","-y","-loglevel","error","-i",str(raw),"-i",str(wav),
        "-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","96k","-shortest","-movflags","+faststart",str(fin)
    ],check=True)
    raw.unlink(missing_ok=True); wav.unlink(missing_ok=True)
    return hashlib.sha256(fin.read_bytes()).hexdigest()

bank_a=[
    ("memory_shuffle",memory_shuffle,"Can You Follow the Hidden Orb? 🟢 #Shorts",11.0,8.5),
    ("object_tracking",object_tracking,"Don't Lose the Target 👀 #Shorts",11.0,8.5),
    ("animated_maze",animated_maze,"Which Signal Reaches the Core? ⚡ #Shorts",10.5,8.0),
    ("spot_difference",spot_difference,"Spot the Difference Before Time Runs Out 🔎 #Shorts",11.0,8.5),
    ("visual_memory",visual_memory,"Which Tile Vanished? 🧠 #Shorts",11.5,9.0),
]
bank_b=[
    ("moving_count",moving_count,"How Many Cyan Orbs Did You Count? 🔵 #Shorts",11.0,8.5),
    ("shadow_match",shadow_match,"Which Shadow Matches? 👤 #Shorts",10.5,8.0),
    ("sequence_next",sequence_next,"What Comes Next? 🧩 #Shorts",10.0,8.0),
    ("color_memory",color_memory,"Which Color Was Third? 🎨 #Shorts",11.0,8.5),
    ("wrong_motion",wrong_motion,"Which Orb Moves the Wrong Way? 👀 #Shorts",10.5,8.0),
]
# Odd/even date rotation guarantees that consecutive days use different
# content families while keeping every daily batch at exactly five Shorts.
rotation_bank="A" if SEED%2==1 else "B"
families=bank_a if rotation_bank=="A" else bank_b

names=["short_1_mesmerizing","short_2_optical","short_3_rain","short_4_loop","short_5_experiment"]
items=[]
for i,(fam,fn,title,duration,reveal) in enumerate(families):
    local=SEED+i*7919
    h=encode(names[i],fn,165+i*21,local,duration,reveal)
    items.append({
        "file":names[i]+".mp4",
        "title":title,
        "family":fam,
        "variant":"motion-v6.1-%s"%local,
        "sha256":h,
        "duration_sec":duration,
        "reveal_at_sec":reveal,
        "solve_window_sec":round(reveal-SOLVE_START,2),
        "description":"Solve the animated visual challenge before the reveal. Comment your answer before time runs out. #visualpuzzle #brainteaser #shorts",
        "tags":["visual puzzle","brain teaser","animated puzzle",fam.replace("_"," "),"shorts"]
    })

manifest={
    "date":DAY.strftime("%Y-%m-%d"),
    "strategy":"motion-rotation-v6.1",
    "rotation_bank":rotation_bank,
    "resolution":"1080x1920",
    "fps":30,
    "timing_policy":"family-adaptive-v1",
    "duration_range_sec":[10.0,11.5],
    "solve_window_range_sec":[6.85,7.85],
    "shorts":items
}
with open(OUT/"manifest.json","w",encoding="utf-8") as f:
    json.dump(manifest,f,ensure_ascii=False,indent=2)
print("Motion Rotation V6.1 rendered:",[(x["family"],x["sha256"][:10]) for x in items])
