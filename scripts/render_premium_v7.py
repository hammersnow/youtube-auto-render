#!/usr/bin/env python3
from pathlib import Path
import cv2
import numpy as np
import math
import wave
import subprocess
import json
import hashlib
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

OUT = Path("outputs/latest")
OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS = 1080, 1920, 30
DAY = datetime.now(ZoneInfo("Europe/Istanbul"))
SEED = int(DAY.strftime("%Y%m%d"))
SOLVE_START = 0.35
ACTIVE_DURATION = 9.6
ACTIVE_REVEAL = 7.25

FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FONT_CACHE = {}
_BG_CACHE = {}
_VIGNETTE = None

PALETTES = [
    ((7, 12, 28), (29, 13, 58), (255, 194, 64), (255, 111, 91)),
    ((5, 20, 28), (8, 50, 61), (70, 240, 214), (64, 156, 255)),
    ((20, 7, 34), (54, 12, 70), (242, 104, 255), (87, 180, 255)),
    ((19, 15, 5), (55, 39, 9), (76, 229, 255), (255, 145, 55)),
]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def ease(x):
    x = clamp(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def font(size, bold=True):
    key = (size, bold)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)
    return _FONT_CACHE[key]


def pil_text(im, text, xy, size, fill=(244, 248, 255), anchor="mm", bold=True,
             stroke=2, stroke_fill=(8, 10, 20), spacing=8):
    rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    d = ImageDraw.Draw(img)
    d.multiline_text(xy, text, font=font(size, bold), fill=fill, anchor=anchor,
                     align="center", spacing=spacing, stroke_width=stroke, stroke_fill=stroke_fill)
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def alpha_blend(base, overlay, alpha):
    return cv2.addWeighted(overlay, alpha, base, 1.0 - alpha, 0)


def mesh_background(seed, palette_index, t):
    a, b, accent, secondary = PALETTES[palette_index % len(PALETTES)]
    key = (palette_index,)
    if key not in _BG_CACHE:
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        aa = np.array(a, np.float32)[None, None, :]
        bb = np.array(b, np.float32)[None, None, :]
        _BG_CACHE[key] = (aa * (1 - yy) + bb * yy + np.zeros((1, W, 1), np.float32)).astype(np.float32)
    im = _BG_CACHE[key].copy()

    small_w, small_h = 270, 480
    sy, sx = np.mgrid[0:small_h, 0:small_w].astype(np.float32)
    blobs = np.zeros((small_h, small_w, 3), np.float32)
    rng = np.random.default_rng(seed + palette_index * 1009)
    cols = [np.array(accent, np.float32), np.array(secondary, np.float32)]
    for i in range(4):
        ph = float(rng.uniform(0, math.tau))
        cx = small_w * (0.22 + 0.56 * (0.5 + 0.5 * math.sin(t * (0.12 + .02*i) + ph)))
        cy = small_h * (0.18 + 0.64 * (0.5 + 0.5 * math.cos(t * (0.10 + .015*i) + ph*1.3)))
        sigma = 70 + 20 * i
        dist = ((sx-cx)**2 + (sy-cy)**2) / (2 * sigma * sigma)
        fall = np.exp(-dist)[..., None] * (0.11 if i < 2 else 0.07)
        blobs += fall * cols[i % 2][None, None, :]
    blobs = cv2.resize(blobs, (W, H), interpolation=cv2.INTER_CUBIC)
    im = np.clip(im + blobs, 0, 255).astype(np.uint8)

    rng = np.random.default_rng(seed + palette_index*313)
    overlay = im.copy()
    for i in range(28):
        layer = 1 + (i % 3)
        x0 = int(rng.integers(-60, W+60))
        y0 = int(rng.integers(230, H-130))
        spd = 6 + layer * 5
        x = int((x0 + math.sin(t*.25 + i)*22*layer) % (W+100)) - 50
        y = int((y0 + t*spd) % (H-260)) + 160
        r = 2 + layer*2
        c = accent if i % 2 == 0 else secondary
        col = tuple(int(v*0.7) for v in c)
        cv2.circle(overlay, (x, y), r, col, -1, cv2.LINE_AA)
    im = alpha_blend(im, overlay, 0.45)
    return im, accent, secondary


def glass_panel(im, rect, radius=34, fill=(21, 28, 48), alpha=.72,
                border=(154, 175, 210), border_alpha=.45, shadow=True):
    x1, y1, x2, y2 = map(int, rect)
    if shadow:
        sh = np.zeros_like(im)
        cv2.rectangle(sh, (x1+12, y1+18), (x2+12, y2+18), (0,0,0), -1)
        sh = cv2.GaussianBlur(sh, (0,0), 18)
        im[:] = cv2.addWeighted(im, 1.0, sh, .32, 0)
    layer = im.copy()
    cv2.rectangle(layer, (x1+radius, y1), (x2-radius, y2), fill, -1, cv2.LINE_AA)
    cv2.rectangle(layer, (x1, y1+radius), (x2, y2-radius), fill, -1, cv2.LINE_AA)
    for cx,cy in [(x1+radius,y1+radius),(x2-radius,y1+radius),(x1+radius,y2-radius),(x2-radius,y2-radius)]:
        cv2.circle(layer,(cx,cy),radius,fill,-1,cv2.LINE_AA)
    im[:] = alpha_blend(im, layer, alpha)
    border_layer = np.zeros_like(im)
    cv2.rectangle(border_layer, (x1+radius,y1), (x2-radius,y2), border, 2, cv2.LINE_AA)
    cv2.rectangle(border_layer, (x1,y1+radius), (x2,y2-radius), border, 2, cv2.LINE_AA)
    cv2.ellipse(border_layer,(x1+radius,y1+radius),(radius,radius),0,180,270,border,2,cv2.LINE_AA)
    cv2.ellipse(border_layer,(x2-radius,y1+radius),(radius,radius),0,270,360,border,2,cv2.LINE_AA)
    cv2.ellipse(border_layer,(x2-radius,y2-radius),(radius,radius),0,0,90,border,2,cv2.LINE_AA)
    cv2.ellipse(border_layer,(x1+radius,y2-radius),(radius,radius),0,90,180,border,2,cv2.LINE_AA)
    im[:] = cv2.addWeighted(im, 1.0, border_layer, border_alpha, 0)


def glow_circle(im, center, radius, color, core=None, intensity=1.0):
    x, y = map(int, center)
    r = max(2, int(radius))
    glow = np.zeros_like(im)
    for mul, alpha in [(2.3,.16),(1.7,.24),(1.3,.35)]:
        cv2.circle(glow, (x,y), int(r*mul), color, -1, cv2.LINE_AA)
        glow = cv2.GaussianBlur(glow, (0,0), max(3, r*.22))
        im[:] = cv2.addWeighted(im, 1.0, glow, alpha*intensity, 0)
        glow[:] = 0
    cv2.circle(im, (x,y), r, core if core is not None else color, -1, cv2.LINE_AA)
    cv2.circle(im, (x-int(r*.28), y-int(r*.28)), max(2,int(r*.20)), (255,255,255), -1, cv2.LINE_AA)


def glow_line(im, p1, p2, color, width=7, alpha=1.0):
    glow = np.zeros_like(im)
    cv2.line(glow, tuple(map(int,p1)), tuple(map(int,p2)), color, width*4, cv2.LINE_AA)
    glow = cv2.GaussianBlur(glow, (0,0), width*2.4)
    im[:] = cv2.addWeighted(im, 1.0, glow, .30*alpha, 0)
    cv2.line(im, tuple(map(int,p1)), tuple(map(int,p2)), color, width, cv2.LINE_AA)


def bloom(im):
    sm = cv2.resize(im, (W//4, H//4), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, 35, 115], np.uint8), np.array([179,255,255], np.uint8))
    bright = cv2.bitwise_and(sm, sm, mask=mask)
    bright = cv2.GaussianBlur(bright, (0,0), 7.5)
    bright = cv2.resize(bright, (W,H), interpolation=cv2.INTER_CUBIC)
    return cv2.addWeighted(im, 1.0, bright, .34, 0)


def finish_frame(im, seed, frame_idx):
    global _VIGNETTE
    im = bloom(im)
    if _VIGNETTE is None:
        y = np.linspace(-1,1,H,dtype=np.float32)[:,None]
        x = np.linspace(-1,1,W,dtype=np.float32)[None,:]
        r = np.sqrt(x*x + (y*.78)*(y*.78))
        _VIGNETTE = np.clip(1.07 - .32*np.power(np.clip(r,0,1.5),1.8), .70, 1.05)[...,None]
    im = np.clip(im.astype(np.float32) * _VIGNETTE, 0,255).astype(np.uint8)
    rng = np.random.default_rng(seed + frame_idx*17)
    n = rng.normal(0, 2.2, (H//8, W//8, 1)).astype(np.float32)
    n = cv2.resize(n, (W,H), interpolation=cv2.INTER_LINEAR)
    if n.ndim == 2:
        n = n[...,None]
    im = np.clip(im.astype(np.float32) + n, 0,255).astype(np.uint8)
    return im


def timer(im, t, accent):
    if not (SOLVE_START <= t < ACTIVE_REVEAL):
        return
    p = clamp((t-SOLVE_START)/(ACTIVE_REVEAL-SOLVE_START), 0, 1)
    x1,y1,x2 = 165,1700,915
    cv2.line(im,(x1,y1),(x2,y1),(58,64,82),12,cv2.LINE_AA)
    cv2.line(im,(x1,y1),(int(x1+(x2-x1)*(1-p)),y1),accent,12,cv2.LINE_AA)
    glow_line(im,(x1,y1),(int(x1+(x2-x1)*(1-p)),y1),accent,3,.7)


def reveal_pulse(im, center, t, color=(78,245,151)):
    if t < ACTIVE_REVEAL:
        return
    q = clamp((t-ACTIVE_REVEAL)/max(.5, ACTIVE_DURATION-ACTIVE_REVEAL),0,1)
    x,y=map(int,center)
    for k in range(3):
        r=int(55+(q+k*.15)*150)
        cv2.circle(im,(x,y),r,color,max(2,7-k*2),cv2.LINE_AA)


def header(im, title, subtitle=None):
    sz = 58
    test_img = Image.new("RGB", (W, 260))
    d = ImageDraw.Draw(test_img)
    while sz > 38:
        box = d.textbbox((0,0), title, font=font(sz, True), stroke_width=3)
        if box[2]-box[0] <= W-96:
            break
        sz -= 2
    im = pil_text(im, title, (W//2, 165), sz, anchor="mm", stroke=3)
    if subtitle:
        im = pil_text(im, subtitle, (W//2, 235), 26, fill=(180,194,220), bold=False, stroke=1)
    return im


def footer_result(im, text, color=(91,255,164)):
    glass_panel(im,(165,1465,915,1608),32,(18,28,38),.80,(110,160,140),.5)
    return pil_text(im,text,(W//2,1536),42,fill=color,stroke=2)


def set_timing(duration, reveal):
    global ACTIVE_DURATION, ACTIVE_REVEAL
    ACTIVE_DURATION=float(duration); ACTIVE_REVEAL=float(reveal)


def wrong_motion(t, seed, frame_idx=0):
    im, accent, secondary = mesh_background(seed,0,t)
    im = header(im,"WHICH ORB BREAKS THE PATTERN?","One orbit is moving against the flow")
    centers=[]
    for r in range(3):
        for c in range(3): centers.append((300+c*240,600+r*310))
    bad=seed%9
    for i,(cx,cy) in enumerate(centers):
        glass_panel(im,(cx-92,cy-92,cx+92,cy+92),28,(17,24,43),.54,(120,145,185),.28,shadow=False)
        cv2.circle(im,(cx,cy),60,(73,85,112),2,cv2.LINE_AA)
        direction=-1 if i==bad else 1
        ang=direction*(t*2.55+i*.53)
        pts=[]
        for k in range(8,0,-1):
            tt=max(0,t-k*.035)
            aa=direction*(tt*2.55+i*.53)
            pts.append((int(cx+52*math.cos(aa)),int(cy+52*math.sin(aa))))
        for k in range(1,len(pts)):
            col=tuple(int(v*(.25+.06*k)) for v in accent)
            cv2.line(im,pts[k-1],pts[k],col,max(2,k//2),cv2.LINE_AA)
        x=int(cx+52*math.cos(ang)); y=int(cy+52*math.sin(ang))
        glow_circle(im,(x,y),17,accent,intensity=.8)
        cv2.circle(im,(cx,cy),7,(235,244,255),-1,cv2.LINE_AA)
    if t>=ACTIVE_REVEAL:
        cx,cy=centers[bad]
        reveal_pulse(im,(cx,cy),t)
        cv2.circle(im,(cx,cy),85,(78,245,151),5,cv2.LINE_AA)
        im=footer_result(im,"REVERSE ORBIT FOUND")
    timer(im,t,accent)
    return finish_frame(im,seed,frame_idx)


def poly_point(points,q):
    q=clamp(q,0,1); lens=[]; total=0
    for a,b in zip(points[:-1],points[1:]):
        d=math.hypot(b[0]-a[0],b[1]-a[1]); lens.append(d); total+=d
    want=q*total; acc=0
    for i,d in enumerate(lens):
        if acc+d>=want:
            u=0 if d==0 else (want-acc)/d
            a,b=points[i],points[i+1]
            return int(a[0]+(b[0]-a[0])*u),int(a[1]+(b[1]-a[1])*u)
        acc+=d
    return points[-1]


def animated_maze(t,seed,frame_idx=0):
    im,accent,secondary=mesh_background(seed,1,t)
    im=header(im,"WHICH SIGNAL REACHES THE CORE?","Follow the energy — only one path is complete")
    glass_panel(im,(90,360,990,1430),46,(12,27,40),.57,(80,170,180),.28)
    good=seed%4
    ys=[530,760,1040,1270]; core=(865,900)
    routes=[]
    rng=np.random.default_rng(seed+88)
    for i,y in enumerate(ys):
        p=[(145,y),(330,y+int(rng.integers(-130,130))),(540,y+int(rng.integers(-160,160)))]
        p.append(core if i==good else (820,470+i*250))
        routes.append(p)
    for i,pts in enumerate(routes):
        for a,b in zip(pts[:-1],pts[1:]): glow_line(im,a,b,(85,110,140),7,.18)
        im=pil_text(im,chr(65+i),(118,pts[0][1]),28,fill=(218,230,244),stroke=1)
        if .2<t<ACTIVE_REVEAL:
            q=((t-.2)*.31+i*.17)%1.0
            px,py=poly_point(pts,q)
            glow_circle(im,(px,py),14,accent,intensity=.75)
    glow_circle(im,core,35,(75,241,174),core=(40,120,95),intensity=1.0)
    if t>=ACTIVE_REVEAL:
        pts=routes[good]
        for a,b in zip(pts[:-1],pts[1:]): glow_line(im,a,b,(78,245,151),10,1.0)
        reveal_pulse(im,core,t)
        im=footer_result(im,f"PATH {chr(65+good)} REACHES THE CORE")
    timer(im,t,accent)
    return finish_frame(im,seed,frame_idx)


def memory_shuffle(t,seed,frame_idx=0):
    im,accent,secondary=mesh_background(seed,2,t)
    im=header(im,"TRACK THE HIDDEN ORB","Memorize it, then follow the shuffle")
    slots=[(245,900),(540,900),(835,900)]
    target=seed%3
    rng=np.random.default_rng(seed+17)
    swaps=[[(0,1),(1,2),(0,2)][int(rng.integers(0,3))] for _ in range(5)]
    perm=[0,1,2]
    pos={i:[float(slots[i][0]),float(slots[i][1])] for i in range(3)}
    start=.95; end=ACTIVE_REVEAL-.15
    if t>=start:
        u=clamp((t-start)/(end-start),0,.999999)
        seg=min(4,int(u*5)); local=ease(u*5-seg)
        for k in range(seg):
            a,b=swaps[k]; perm[a],perm[b]=perm[b],perm[a]
        for sidx,obj in enumerate(perm): pos[obj]=[float(slots[sidx][0]),float(slots[sidx][1])]
        a,b=swaps[seg]; oa,ob=perm[a],perm[b]
        ax,ay=slots[a]; bx,by=slots[b]
        arc=-185*math.sin(math.pi*local)
        pos[oa]=[ax+(bx-ax)*local,ay+arc]
        pos[ob]=[bx+(ax-bx)*local,by-arc]
    for obj in range(3):
        x,y=pos[obj]
        glass_panel(im,(x-103,y-145,x+103,y+145),36,(19,24,45),.78,(130,145,190),.38)
        if t<.9 and obj==target:
            glow_circle(im,(x,y),37,(78,245,151),intensity=1.0)
        else:
            im=pil_text(im,"?",(int(x),int(y)),76,fill=(218,227,242),stroke=2)
    if t>=ACTIVE_REVEAL:
        final=[0,1,2]
        for a,b in swaps: final[a],final[b]=final[b],final[a]
        target_slot=final.index(target); x,y=slots[target_slot]
        reveal_pulse(im,(x,y),t)
        cv2.rectangle(im,(x-117,y-160),(x+117,y+160),(78,245,151),5,cv2.LINE_AA)
        im=footer_result(im,"TARGET LOCKED")
    timer(im,t,accent)
    return finish_frame(im,seed,frame_idx)


def draw_glyph(im,kind,x,y,size,col,rot=0):
    x,y,size=int(x),int(y),int(size)
    if kind==0:
        glow_circle(im,(x,y),size,col,intensity=.25)
    elif kind==1:
        pts=np.array([[0,-size],[size,0],[0,size],[-size,0]],np.float32)
        a=math.radians(rot); ca,sa=math.cos(a),math.sin(a)
        R=np.array([[ca,-sa],[sa,ca]],np.float32)
        pts=(pts@R.T+np.array([x,y])).astype(np.int32)
        cv2.fillPoly(im,[pts],col,cv2.LINE_AA)
    elif kind==2:
        cv2.rectangle(im,(x-size,y-size),(x+size,y+size),col,-1,cv2.LINE_AA)
    else:
        cv2.line(im,(x-size,y),(x+size,y),col,max(5,size//3),cv2.LINE_AA)
        cv2.line(im,(x,y-size),(x,y+size),col,max(5,size//3),cv2.LINE_AA)


def spot_difference(t,seed,frame_idx=0):
    im,accent,secondary=mesh_background(seed,3,t)
    im=header(im,"SPOT THE MOVING DIFFERENCE","Both panels look identical… almost")
    glass_panel(im,(70,355,510,1425),42,(22,27,42),.67,(160,148,112),.30)
    glass_panel(im,(570,355,1010,1425),42,(22,27,42),.67,(160,148,112),.30)
    rng=np.random.default_rng(seed+55)
    kinds=[int(rng.integers(0,4)) for _ in range(24)]
    bad=seed%24
    for idx in range(24):
        r,c=divmod(idx,4); y=500+r*168; x1=130+c*100; x2=630+c*100
        kind=kinds[idx]; pulse=1+.08*math.sin(t*3.2+idx*.7); sz=20*pulse
        col=accent if idx%3 else secondary
        draw_glyph(im,kind,x1,y,sz,col,rot=t*28+idx*8)
        rot=t*28+idx*8 + (34 if idx==bad else 0)
        draw_glyph(im,kind,x2,y,sz,col,rot=rot)
    if .6<t<ACTIVE_REVEAL:
        q=ease((t-.6)/(ACTIVE_REVEAL-.6)); sx=int(105+345*q)
        glow_line(im,(sx,390),(sx,1385),accent,3,.55)
        glow_line(im,(sx+500,390),(sx+500,1385),accent,3,.55)
    br,bc=divmod(bad,4); bx=630+bc*100; by=500+br*168
    if t>=ACTIVE_REVEAL:
        reveal_pulse(im,(bx,by),t)
        cv2.rectangle(im,(bx-46,by-46),(bx+46,by+46),(78,245,151),5,cv2.LINE_AA)
        im=footer_result(im,"DIFFERENCE FOUND")
    timer(im,t,accent)
    return finish_frame(im,seed,frame_idx)


def physics_error(t,seed,frame_idx=0):
    im,accent,secondary=mesh_background(seed,1,t)
    im=header(im,"WHICH ORB IGNORES PHYSICS?","Eight bounce normally. One cheats gravity.")
    glass_panel(im,(100,360,980,1420),46,(10,25,35),.56,(95,160,175),.28)
    bad=seed%9
    centers=[]
    for r in range(3):
        for c in range(3): centers.append((290+c*250,600+r*310))
    for i,(cx,cy) in enumerate(centers):
        ph=i*.49+(seed%11)*.13
        if i==bad:
            y=cy+80*math.sin(t*2.45+ph); x=cx+36*math.sin(t*.9+ph)
        else:
            s=((t*.70+ph)%1.0); h=4*s*(1-s)
            y=cy+72-145*h; x=cx+26*math.sin(t*.75+ph)
        glow_circle(im,(x,y),24,accent if i%2==0 else secondary,intensity=.55)
        cv2.ellipse(im,(cx,cy+92),(45,10),0,0,360,(45,55,72),-1,cv2.LINE_AA)
    if t>=ACTIVE_REVEAL:
        cx,cy=centers[bad]
        reveal_pulse(im,(cx,cy),t)
        cv2.circle(im,(cx,cy),105,(78,245,151),5,cv2.LINE_AA)
        im=footer_result(im,"THIS ORB BREAKS GRAVITY")
    timer(im,t,accent)
    return finish_frame(im,seed,frame_idx)


def portal_path(t,seed,frame_idx=0):
    im,accent,secondary=mesh_background(seed,2,t)
    im=header(im,"WHICH PORTAL DOES IT EXIT?","Track the orb through the teleport chain")
    portals=[(235,610),(535,560),(835,650),(300,1050),(600,1120),(850,1040)]
    glass_panel(im,(95,365,985,1425),48,(22,16,40),.55,(145,100,190),.30)
    for i,(x,y) in enumerate(portals):
        c=accent if i%2==0 else secondary
        for rr,al in [(64,.28),(50,.5),(38,1.0)]:
            cv2.ellipse(im,(x,y),(rr,int(rr*.42)),0,0,360,c,max(2,int(5*al)),cv2.LINE_AA)
        im=pil_text(im,chr(65+i),(x,y+92),26,fill=(205,216,240),stroke=1)
    chain=[0,4,1,5,2,3]
    segdur=(ACTIVE_REVEAL-.5)/(len(chain)-1)
    if t<ACTIVE_REVEAL:
        seg=min(len(chain)-2,max(0,int((t-.3)/segdur)))
        local=clamp(((t-.3)-seg*segdur)/segdur,0,1)
        a=portals[chain[seg]]; b=portals[chain[seg+1]]; q=ease(local)
        x=a[0]+(b[0]-a[0])*q; y=a[1]+(b[1]-a[1])*q - 85*math.sin(math.pi*q)
        glow_circle(im,(x,y),22,(78,245,151),intensity=1.0)
        glow_line(im,a,(x,y),(78,245,151),3,.25)
    exit_idx=chain[-1]
    if t>=ACTIVE_REVEAL:
        x,y=portals[exit_idx]
        reveal_pulse(im,(x,y),t)
        cv2.ellipse(im,(x,y),(86,38),0,0,360,(78,245,151),7,cv2.LINE_AA)
        im=footer_result(im,f"EXIT PORTAL {chr(65+exit_idx)}")
    timer(im,t,accent)
    return finish_frame(im,seed,frame_idx)


def laser_core(t,seed,frame_idx=0):
    im,accent,secondary=mesh_background(seed,3,t)
    im=header(im,"WHICH LASER HITS THE CORE?","Mirrors rotate — predict the final beam")
    glass_panel(im,(90,370,990,1420),48,(29,23,9),.53,(155,135,75),.28)
    core=(870,900); good=seed%3
    starts=[(150,590),(150,900),(150,1210)]
    mirrors=[[(350,560),(560,700)],[(360,900),(585,900)],[(350,1240),(565,1110)]]
    for i,s in enumerate(starts):
        p=[s]+mirrors[i]+([core] if i==good else [(835,520+i*360)])
        for a,b in zip(p[:-1],p[1:]): glow_line(im,a,b,(80,100,115),5,.18)
        im=pil_text(im,chr(65+i),(115,s[1]),26,fill=(225,232,242),stroke=1)
        if .2<t<ACTIVE_REVEAL:
            px,py=poly_point(p,((t-.2)*.34+i*.2)%1)
            glow_circle(im,(px,py),12,accent,intensity=.65)
    glow_circle(im,core,30,(78,245,151),core=(40,105,80),intensity=.85)
    if t>=ACTIVE_REVEAL:
        p=[starts[good]]+mirrors[good]+[core]
        for a,b in zip(p[:-1],p[1:]): glow_line(im,a,b,(78,245,151),9,1)
        reveal_pulse(im,core,t)
        im=footer_result(im,f"LASER {chr(65+good)} HITS")
    timer(im,t,accent)
    return finish_frame(im,seed,frame_idx)


FAMILIES = {
    "wrong_motion": (wrong_motion, "Which Orb Breaks the Pattern? ✨ #Shorts", 9.4, 7.1),
    "animated_maze": (animated_maze, "Which Signal Reaches the Core? ⚡ #Shorts", 9.5, 7.2),
    "memory_shuffle": (memory_shuffle, "Can You Track the Hidden Orb? 🟢 #Shorts", 9.6, 7.25),
    "spot_difference": (spot_difference, "Spot the Moving Difference 🔎 #Shorts", 9.6, 7.25),
    "physics_error": (physics_error, "Which Orb Ignores Physics? 🧲 #Shorts", 9.3, 7.0),
    "portal_path": (portal_path, "Which Portal Does It Exit? 🌀 #Shorts", 9.5, 7.2),
    "laser_core": (laser_core, "Which Laser Hits the Core? 🔺 #Shorts", 9.4, 7.1),
}
PROVEN = ["wrong_motion", "animated_maze", "memory_shuffle", "spot_difference"]
EXPERIMENTS = ["physics_error", "portal_path", "laser_core"]


def synth_audio(path, base_freq, duration, reveal, seed):
    sr=32000; n=int(sr*duration); tt=np.arange(n,dtype=np.float32)/sr
    left=.010*np.sin(2*np.pi*base_freq*tt)+.004*np.sin(2*np.pi*(base_freq*.5)*tt)
    right=.010*np.sin(2*np.pi*(base_freq*1.006)*tt)+.004*np.sin(2*np.pi*(base_freq*.503)*tt)
    for sec in np.arange(.7,reveal,.72):
        st=int(sec*sr); nn=min(int(.055*sr),n-st)
        if nn<=0: continue
        x=np.arange(nn,dtype=np.float32)/sr; env=np.exp(-x*45)
        tone=.022*np.sin(2*np.pi*(base_freq*2.1)*x)*env
        left[st:st+nn]+=tone; right[st:st+nn]+=tone*.9
    st=int(reveal*sr); nn=min(int(.55*sr),n-st)
    if nn>0:
        x=np.arange(nn,dtype=np.float32)/sr; env=np.exp(-x*5.2)
        rng=np.random.default_rng(seed)
        noise=rng.normal(0,1,nn).astype(np.float32)
        noise=cv2.GaussianBlur(noise.reshape(-1,1),(1,0),2).reshape(-1)
        chime=(.045*np.sin(2*np.pi*(base_freq*2.5)*x)+.027*np.sin(2*np.pi*(base_freq*3.75)*x))*env
        whoosh=.012*noise*env
        left[st:st+nn]+=chime+whoosh; right[st:st+nn]+=chime*.96-whoosh
    sig=np.stack([left,right],axis=1)
    sig=np.clip(sig,-.92,.92)
    with wave.open(str(path),"wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((sig*32767).astype("<i2").tobytes())


def encode(name, fn, seed, duration, reveal, freq):
    set_timing(duration,reveal)
    raw=OUT/(name+"_raw.mp4"); wav=OUT/(name+".wav"); fin=OUT/(name+".mp4")
    v=cv2.VideoWriter(str(raw),cv2.VideoWriter_fourcc(*"mp4v"),FPS,(W,H))
    if not v.isOpened(): raise RuntimeError("VideoWriter failed: "+str(raw))
    total=int(round(FPS*duration))
    for i in range(total):
        frame=fn(i/FPS,seed,i)
        if frame.shape!=(H,W,3): raise RuntimeError(f"Bad frame shape {frame.shape}")
        v.write(frame)
    v.release()
    synth_audio(wav,freq,duration,reveal,seed)
    subprocess.run([
        "ffmpeg","-y","-loglevel","error","-i",str(raw),"-i",str(wav),
        "-c:v","libx264","-preset","slow","-crf","18","-profile:v","high","-level","4.1",
        "-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",str(fin)
    ],check=True)
    raw.unlink(missing_ok=True); wav.unlink(missing_ok=True)
    return hashlib.sha256(fin.read_bytes()).hexdigest()


def daily_selection(seed):
    day_index=int(DAY.strftime("%j"))
    p1=PROVEN[day_index%len(PROVEN)]
    p2=PROVEN[(day_index+2)%len(PROVEN)]
    exp=EXPERIMENTS[day_index%len(EXPERIMENTS)]
    order=[p1,p2,exp]
    shift=day_index%3
    return order[shift:]+order[:shift]


def smoke_previews(selection):
    prev=Path("outputs/previews"); prev.mkdir(parents=True,exist_ok=True)
    for idx,fam in enumerate(selection):
        fn,_,duration,reveal=FAMILIES[fam]
        set_timing(duration,reveal)
        for tag,t in [("solve",min(3.1,reveal-.4)),("reveal",min(duration-.2,reveal+.35))]:
            fr=fn(t,SEED+idx*7919,int(t*FPS))
            cv2.imwrite(str(prev/f"v7_{idx+1}_{fam}_{tag}.jpg"),fr,[cv2.IMWRITE_JPEG_QUALITY,94])
    print("V7 smoke previews:",selection)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--smoke",action="store_true",help="render preview JPGs only")
    args=ap.parse_args()
    selection=daily_selection(SEED)
    if args.smoke:
        smoke_previews(selection); return
    names=["short_1_premium","short_2_premium","short_3_premium"]
    items=[]
    for i,fam in enumerate(selection):
        fn,title,duration,reveal=FAMILIES[fam]
        local=SEED+i*7919
        sha=encode(names[i],fn,local,duration,reveal,168+i*27)
        items.append({
            "file":names[i]+".mp4", "title":title, "family":fam,
            "variant":f"premium-v7-{local}", "sha256":sha,
            "duration_sec":duration, "reveal_at_sec":reveal,
            "solve_window_sec":round(reveal-SOLVE_START,2), "quality_tier":"premium-v7",
            "description":"Solve the premium animated visual puzzle before the reveal. Comment your answer before time runs out. #visualpuzzle #brainteaser #satisfying #shorts",
            "tags":["visual puzzle","brain teaser","satisfying animation","motion design",fam.replace("_"," "),"shorts"]
        })
    manifest={
        "date":DAY.strftime("%Y-%m-%d"), "timezone":"Europe/Istanbul",
        "strategy":"premium-motion-v7", "selection_policy":"2-proven-1-experiment-v1",
        "daily_short_count":3, "resolution":"1080x1920", "fps":30,
        "encoder":"libx264 slow crf18", "timing_policy":"retention-v2",
        "visual_stack":["animated mesh gradient","parallax bokeh","glass panels","bloom","glow trails","Pillow typography","vignette","procedural grain","procedural stereo sound"],
        "shorts":items
    }
    (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Premium Motion V7 rendered:",[(x["family"],x["sha256"][:10]) for x in items])

if __name__=="__main__":
    main()
