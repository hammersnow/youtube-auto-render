#!/usr/bin/env python3
"""V8.9 — original premium 2.5D turbocharger explainer.

No modification/overlay of any prior video footage: all RGB video frames are composed
from geometry and scene assets generated here. Only the sound mix is reused from
user-supplied prior V8 production (89239.mp4). Explanatory typography lives in
reserved header/stage/information panels.

Model: turbine and compressor rotate on one rigid shaft; separated exhaust and
fresh intake air streams, with no mixing. Explanatory schematic, not CFD.
"""
import os, math, argparse, subprocess, sys, os, time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W,H=1080,1920
FPS=24
DURATION=26.0
N=int(FPS*DURATION)
FONT_DIR='/usr/share/fonts/opentype/inter/' if os.path.isfile('/usr/share/fonts/opentype/inter/Inter-Regular.otf') else '/usr/share/fonts/truetype/dejavu/'
FONT=os.path.join(FONT_DIR,'Inter-Regular.otf' if 'inter' in FONT_DIR else 'DejaVuSans.ttf')
FONT_B=os.path.join(FONT_DIR,'Inter-Bold.otf' if 'inter' in FONT_DIR else 'DejaVuSans-Bold.ttf')
FONT_M=os.path.join(FONT_DIR,'Inter-Medium.otf' if 'inter' in FONT_DIR else 'DejaVuSans.ttf')
FONT_SB=os.path.join(FONT_DIR,'Inter-SemiBold.otf' if 'inter' in FONT_DIR else 'DejaVuSans-Bold.ttf')
BLUE=(54,204,251)
BLUE_DIM=(37,110,152)
GOLD=(255,209,105)
AMBER=(255,166,75)
TEAL=(76,222,168)
RED=(252,115,83)
WHITE=(238,244,251)
MUTED=(152,166,185)
BG=(9,17,29)
NAVY=(14,25,40)
CHAMBER=(20,18,20)

def ff(size,bold=False,medium=False):
    return ImageFont.truetype(FONT_B if bold else FONT_M if medium else FONT,size)

F_KICKER=ff(27,bold=True); F_MICRO=ff(24,medium=True)
F_HEADER=ff(58,bold=True); F_SUB=ff(26,medium=True)
F_INDEX=ff(32,bold=True); F_STAGE=ff(30,bold=True)
F_BIG=ff(60,bold=True); F_DESC=ff(36,medium=True); F_DETAIL=ff(29,medium=True)
F_WM=ff(23,medium=True); F_FOOT=ff(25,medium=True)
F_INOUT=ff(29,bold=True)

STAGES=[
    ('00','THE FOUR-STROKE CYCLE','ONE SPARK. FOUR STROKES.','Watch how a piston turns heat into rotation.',GOLD),
    ('01','INTAKE','FRESH CHARGE ENTERS','Intake valve opens  /  piston moves DOWN',BLUE),
    ('02','COMPRESSION','THE MIXTURE IS SQUEEZED','Both valves close  /  piston moves UP',GOLD),
    ('03','POWER','COMBUSTION DOES THE WORK','Spark ignites mixture  /  piston moves DOWN',AMBER),
    ('04','EXHAUST','BURNT GASES LEAVE','Exhaust valve opens  /  piston moves UP',TEAL),
    ('05','THE CYCLE REPEATS','FOUR STROKES  /  TWO TURNS','The crankshaft converts linear motion into rotation.',GOLD),
]
STEP_NAMES=('INTAKE','SQUEEZE','POWER','EXHAUST')
STEP_COLORS=(BLUE,GOLD,AMBER,TEAL)

# 2 second intro, four 5.5-second stages, 2 second outro
CUTS=(0,2,7.5,13,18.5,24,26)

def stage_at(t):
    for i in range(6):
        if t<CUTS[i+1]:
            return i,(t-CUTS[i])/(CUTS[i+1]-CUTS[i])
    return 5,1.0

def clamp(v,a=0.,b=1.): return min(b,max(a,v))
def lerp(a,b,t): return a+(b-a)*t

def smoothstep(x):
    x=clamp(x);return x*x*(3-2*x)

def tint(rgb,amount):return tuple(round(v*amount) for v in rgb)

def arc_poly(cx,cy,rx,ry,a0,a1,n=80):
    return [(cx+rx*math.cos(math.radians(lerp(a0,a1,i/(n-1)))),cy+ry*math.sin(math.radians(lerp(a0,a1,i/(n-1))))) for i in range(n)]

def text_center(draw,xy,s,f,fill):
    box=draw.textbbox((0,0),s,font=f)
    draw.text((xy[0]-(box[2]-box[0])/2,xy[1]-(box[3]-box[1])/2),s,font=f,fill=fill)

def text_right(draw,xy,s,f,fill):
    box=draw.textbbox((0,0),s,font=f)
    draw.text((xy[0]-(box[2]-box[0]),xy[1]),s,font=f,fill=fill)

def bevel_box(draw,box,r=18,face=(38,47,55),stroke=(139,133,116),highlight=(223,211,170),depth=8):
    x0,y0,x1,y1=map(int,box)
    draw.rounded_rectangle((x0+depth,y0+depth,x1+depth,y1+depth),radius=r,fill=(5,9,14))
    draw.rounded_rectangle((x0,y0,x1,y1),radius=r,fill=face,outline=stroke,width=5)
    draw.line([(x0+r,y0+4),(x1-r,y0+4)],fill=highlight,width=3)
    draw.line([(x0+6,y0+r),(x0+6,y1-r)],fill=(82,80,72),width=3)

def bolt(d,x,y,r=14):
    d.ellipse((x-r-3,y-r-3,x+r+3,y+r+3),fill=(23,23,23),outline=(172,152,119),width=3)
    d.ellipse((x-r+1,y-r+1,x+r-1,y+r-1),fill=(66,60,53),outline=(102,93,78),width=2)
    d.line([(x-r/2,y-r/2),(x+r/2,y+r/2)],fill=(196,182,152),width=2)

def draw_background():
    y=np.arange(H,dtype=np.float32)[:,None,None]
    x=np.arange(W,dtype=np.float32)[None,:,None]
    colors=np.array([10.,19.,31.])[None,None,:]+(y/H)*np.array([2.,1.,7.])[None,None,:]
    # atmospheric glows, precomputed once
    dist=np.sqrt(((x[:,:,0]-520.)/710.)**2+((y[:,0,0][:,None]-940.)/940.)**2)
    glow=np.maximum(0,1-dist)[...,None]*np.array([14.,11.,7.])[None,None,:]
    arr=np.broadcast_to(colors,(H,W,3)).copy()+glow
    im=Image.fromarray(np.uint8(np.clip(arr,0,255)),'RGB')
    d=ImageDraw.Draw(im)
    # Technical grid background in machine zone
    for xx in range(48,W-48,84):
        d.line([(xx,441),(xx,1404)],fill=(23,36,48),width=1)
    for yy in range(450,1410,84):
        d.line([(42,yy),(1038,yy)],fill=(23,36,48),width=1)
    # structural panels
    d.rounded_rectangle((38,435,1042,1410),radius=27,fill=None,outline=(48,59,70),width=2)
    d.rounded_rectangle((38,1452,1042,1779),radius=32,fill=(25,24,24),outline=(72,60,47),width=3)
    d.line([(58,1826),(1022,1826)],fill=(78,74,63),width=2)
    return im

BASE=draw_background()


# All elements are drawn as part of the composition, never attached to a prior video.
TOTAL=26.0
FRAMES=int(FPS*TOTAL)
CUTS=(0.0,2.5,7.8,12.2,18.1,24.0,26.0)
SERIES='INSIDE THE MACHINE'
EP='EPISODE 02'

PHASES=[
    ('00','TURBOCHARGER','EXHAUST ENERGY BECOMES BOOST','The engine throws energy away. A turbo recovers some.',GOLD),
    ('01','EXHAUST ENERGY','HOT GAS SPINS THE TURBINE','Engine exhaust hits the turbine blades.',AMBER),
    ('02','SHARED SHAFT','TWO WHEELS. ONE SHAFT.','The turbine mechanically drives the compressor.',GOLD),
    ('03','FRESH AIR','THE COMPRESSOR PRESSURIZES AIR','Clean incoming air is compressed on the cold side.',BLUE),
    ('04','BOOST TO ENGINE','MORE AIR REACHES THE CYLINDERS','With the right fuel, the engine can make more power.',TEAL),
    ('05','RECAP','EXHAUST DRIVES BOOST','Two separate flows. One connected rotating shaft.',GOLD)
]
TABS=(('EXHAUST',AMBER),('SHAFT',GOLD),('COMPRESS',BLUE),('BOOST',TEAL))

L=(305,855)
RGT=(775,855)
RAD=179


def phase(t):
    for i in range(6):
        if t < CUTS[i+1]:
            return i,clamp((t-CUTS[i])/(CUTS[i+1]-CUTS[i]))
    return 5,1.


def path_points_cubic(p0,p1,p2,p3,n=32):
    out=[]
    for i in range(n):
        t=i/(n-1)
        o=1-t
        x=o**3*p0[0]+3*o*o*t*p1[0]+3*o*t*t*p2[0]+t**3*p3[0]
        y=o**3*p0[1]+3*o*o*t*p1[1]+3*o*t*t*p2[1]+t**3*p3[1]
        out.append((x,y))
    return out


def extend(lines):
    out=[]
    for line in lines:
        out+=line[:-1]
    out.append(lines[-1][-1])
    return out

# A particle has a continuous distance-coordinate along the ENTIRE gas path.
# Exhaust enters the hot side and leaves the turbo without changing into cold-side air.
HOT_PATH=extend([
    path_points_cubic((75,1170),(135,1170),(186,1113),(205,1047),24),
    path_points_cubic((205,1047),(193,985),(204,931),(261,890),22),
    path_points_cubic((261,890),(279,866),(302,853),(310,851),14),
    path_points_cubic((310,851),(286,828),(237,774),(172,718),22),
    path_points_cubic((172,718),(143,687),(105,679),(74,679),16)
])
COLD_PATH=extend([
    path_points_cubic((1008,682),(930,680),(889,744),(843,800),26),
    path_points_cubic((843,800),(803,835),(782,853),(774,857),18),
    path_points_cubic((774,857),(801,883),(838,923),(864,962),18),
    path_points_cubic((864,962),(904,1010),(936,1108),(1009,1132),30)
])


def prep_path(raw):
    lengths=[0.]
    for a,b in zip(raw,raw[1:]):
        lengths.append(lengths[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
    return raw,lengths,lengths[-1]

HOT_DATA=prep_path(HOT_PATH)
COLD_DATA=prep_path(COLD_PATH)


def path_sample(info,delta):
    pts,ls,total=info
    delta=delta%total
    # binary search for position in path
    from bisect import bisect_left
    i=min(len(ls)-1,max(1,bisect_left(ls,delta)))
    v=(delta-ls[i-1])/(ls[i]-ls[i-1] or 1.)
    (ax,ay),(bx,by)=pts[i-1],pts[i]
    return lerp(ax,bx,v),lerp(ay,by,v)


def ring(d,cx,cy,r,fill,stroke,width=3):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=fill,outline=stroke,width=width)


def make_base_scene():
    im=Image.new('RGBA',(W,H),(0,0,0,0))
    d=ImageDraw.Draw(im)

    # cast outer housings (mechanically stable across all segments)
    for (cx,cy),cold in ((L,False),(RGT,True)):
        warm=(175,136,93) if not cold else (106,169,194)
        face=(67,56,47) if not cold else (42,63,70)
        dark=(18,15,16) if not cold else (16,24,31)
        ring(d,cx+10,cy+12,RAD+26,(8,10,13),(63,55,45),7)
        ring(d,cx,cy,RAD+25,face,(169,151,117) if not cold else (139,166,178),10)
        ring(d,cx,cy,RAD+7,(34,32,32) if not cold else (28,37,44),warm,7)
        ring(d,cx,cy,RAD-13,dark,(94,82,64) if not cold else (79,107,119),4)
        # machined inner concentric rim
        ring(d,cx,cy,RAD-35,None,(103,89,72) if not cold else (83,115,135),3)
        for k in range(8):
            a=math.pi*2*k/8
            x=cx+(RAD+18)*math.sin(a)
            y=cy-(RAD+18)*math.cos(a)
            bolt(d,x,y,8)
        # outer fixing arcs
        d.arc((cx-RAD-21,cy-RAD-21,cx+RAD+21,cy+RAD+21),start=205,end=318,fill=(227,201,155) if not cold else (166,207,220),width=5)
        d.arc((cx-RAD-19,cy-RAD-19,cx+RAD+19,cy+RAD+19),start=18,end=127,fill=(72,60,47) if not cold else (57,89,104),width=7)

    # central connecting shaft encased in an open cutaway bridge (rear layer)
    bevel_box(d,(447,813,632,909),19,(80,73,63),(153,145,125),(238,221,178),7)
    d.rounded_rectangle((449,846,633,880),radius=14,fill=(18,23,27),outline=(192,176,139),width=4)
    d.line([(468,858),(615,858)],fill=(236,217,171),width=10)
    d.line([(466,849),(615,849)],fill=(95,83,67),width=3)
    for x in (474,603):
        d.line([(x,836),(x,892)],fill=(145,127,96),width=9)
    # metal side ports and clearly separated pipe channels, two-colored plumbing
    def piped(pts,edge,center):
        d.line(pts,fill=(11,14,20),width=61,joint='curve')
        d.line(pts,fill=edge,width=48,joint='curve')
        d.line(pts,fill=(36,38,38),width=36,joint='curve')
        d.line(pts,fill=center,width=7,joint='curve')
    # warm side ports
    piped([(63,1167),(128,1167),(170,1139),(185,1090),(202,1030)],(133,95,61),(170,120,78))
    piped([(204,807),(151,745),(99,689),(60,689)],(123,92,72),(183,135,86))
    # cold side channels
    piped([(1023,679),(966,679),(911,719),(865,776)],(66,101,120),(113,158,179))
    piped([(876,978),(916,1050),(961,1138),(1025,1138)],(56,93,110),(103,160,185))
    # mini technical flow labels outside device, kept fixed & aligned
    d.rounded_rectangle((56,1190,350,1251),radius=16,fill=(41,32,28),outline=(123,87,63),width=2)
    text_center(d,(203,1220),'FROM ENGINE',F_MICRO,(224,163,114))
    d.rounded_rectangle((59,592,304,653),radius=16,fill=(41,32,28),outline=(122,88,63),width=2)
    text_center(d,(182,621),'EXHAUST OUT',F_MICRO,(229,182,135))
    d.rounded_rectangle((755,593,1022,655),radius=16,fill=(22,39,51),outline=(59,129,167),width=2)
    text_center(d,(887,623),'FRESH AIR IN',F_MICRO,(122,220,255))
    d.rounded_rectangle((729,1196,1025,1257),radius=16,fill=(22,44,51),outline=(62,136,156),width=2)
    text_center(d,(877,1226),'BOOST TO ENGINE',F_MICRO,(120,232,242))

    # fixed stage labels are above rotating faces; not overlays on old video
    d.rounded_rectangle((108,482,498,551),radius=19,fill=(48,37,31),outline=(119,90,66),width=2)
    text_center(d,(303,518),'HOT SIDE / TURBINE',F_INDEX,(255,180,118))
    d.rounded_rectangle((572,482,975,551),radius=19,fill=(31,47,55),outline=(76,112,129),width=2)
    text_center(d,(773,518),'COLD SIDE / COMPRESSOR',F_INDEX,(126,217,255))

    # lower connector rail and physical shaft callout
    d.line([(380,1304),(699,1304)],fill=(112,98,75),width=3)
    d.rounded_rectangle((365,1277,716,1343),radius=18,fill=(35,33,30),outline=(107,92,68),width=2)
    text_center(d,(541,1311),'ONE SHARED SHAFT',F_INDEX,(217,206,174))
    return im

BASE_SCENE=make_base_scene()


def stage_panel(i):
    im=BASE.copy()
    d=ImageDraw.Draw(im)
    idx,title,lead,detail,accent=PHASES[i]
    d.text((56,62),SERIES,font=F_KICKER,fill=(109,216,228))
    d.text((374,62),f'/  {EP}',font=F_KICKER,fill=(101,149,169))
    text_right(d,(1022,62),'TURBO / 2.5D CUTAWAY',F_MICRO,(136,144,157))
    d.text((56,140),'HOW A TURBOCHARGER',font=F_HEADER,fill=WHITE)
    d.text((56,207),'TURNS EXHAUST INTO BOOST',font=F_HEADER,fill=WHITE)
    d.line([(55,308),(1025,308)],fill=(93,82,67),width=2)
    for j,(name,col) in enumerate(TABS):
        xx=55+j*244
        active=(j==i-1)
        d.rounded_rectangle((xx,326,xx+230,424),radius=20,
            fill=(48,53,56) if active else (34,35,37),
            outline=col if active else (59,56,51),width=3 if active else 1)
        if active:
            d.rounded_rectangle((xx+7,412,xx+223,422),radius=4,fill=col)
        d.text((xx+17,346),f'{j+1:02d}',font=F_INDEX,fill=col if active else (104,98,92))
        d.text((xx+57,356),name,font=ff(26,bold=True),fill=WHITE if active else (141,143,149))
    d.rounded_rectangle((58,1474,1022,1735),radius=27,
        fill=(32,27,25),outline=(94,75,53),width=2)
    d.line([(138,1502),(942,1502)],fill=(87,72,57),width=2)
    text_center(d,(540,1557),title,F_BIG,accent)
    text_center(d,(540,1642),lead,F_DESC,WHITE)
    text_center(d,(540,1709),detail,F_DETAIL,MUTED)
    d.line([(60,1787),(1020,1787)],fill=(76,67,57),width=3)
    d.line([(60,1787),(60+(min(max(i-1,0),4))*240,1787)],fill=accent,width=7)
    text_center(d,(540,1830),'EXHAUST AND FRESH AIR NEVER MIX',F_FOOT,(159,178,193))
    d.line([(62,1863),(1018,1863)],fill=(63,68,69),width=2)
    d.text((62,1877),'ORIGINAL MOTION DESIGN',font=F_MICRO,fill=(125,128,129))
    text_right(d,(1018,1877),'Ekrem Gökberk İşcan',F_WM,(188,188,180))
    return im

BG_PANELS=[stage_panel(i) for i in range(6)]


def draw_wheel(d,cx,cy,theta,cold,focused=False):
    # Rotating impeller in a stationary 2.5D cutaway casing.
    c1=(182,146,101) if not cold else (143,195,211)
    c2=(105,88,68) if not cold else (74,118,143)
    rim=(234,199,142) if not cold else (176,226,244)
    ring(d,cx,cy,133,(24,24,27) if not cold else (20,28,35),c2,6)
    ring(d,cx,cy,123,(56,49,42) if not cold else (39,57,65),c1,4)
    for j in range(9):
        a=theta+j*(math.tau/9)
        def polar(rad,angle): return (cx+rad*math.cos(angle),cy+rad*math.sin(angle))
        # Curved, pitched blades, not flat radial spokes.
        outer=polar(120,a+0.25)
        bend=polar(89,a+0.08)
        inner=polar(41,a-0.18)
        in_bend=polar(74,a-0.28)
        edge=polar(120,a-0.07)
        shade=0.75+0.25*max(0,math.sin(a+0.7))
        color=tuple(int(n*shade) for n in (207,178,130) if not cold) if not cold else tuple(int(n*shade) for n in (153,213,229))
        d.polygon([inner,bend,outer,edge,in_bend],fill=color)
        d.line([inner,bend,outer],fill=(255,229,177) if not cold else (207,244,254),width=3,joint='curve')
    ring(d,cx,cy,43,(81,69,51) if not cold else (65,103,122),rim,5)
    ring(d,cx,cy,23,(175,156,118) if not cold else (161,213,230),(59,54,49),5)
    d.line([(cx-11,cy-3),(cx+11,cy+4)],fill=(246,230,196) if not cold else (233,251,254),width=3)
    # Thin highlighted rim to focus on mechanism, never fill the wheel with a giant glow
    if focused:
        d.arc((cx-151,cy-151,cx+151,cy+151),start=214,end=345,
              fill=AMBER if not cold else BLUE,width=8)
        d.arc((cx-151,cy-151,cx+151,cy+151),start=27,end=172,
              fill=(229,173,105) if not cold else (93,208,251),width=6)


def visible_route(d,info,col,focus,leading,pressure=False):
    pts,ls,total=info
    # Thin colored moving streams; no blobs/ellipses/opaque fills.
    for i in range(32):
        distance=(leading + total*i/32)%total
        x,y=path_sample(info,distance)
        radius=3.3+(i%4)*0.7
        alpha=min(255,int(75+160*focus))
        base=(int(col[0]*(0.45+0.55*focus)),
              int(col[1]*(0.45+0.55*focus)),
              int(col[2]*(0.45+0.55*focus)))
        if pressure and distance/total>.52:
            base=(106,243,217)
            radius=4.2+(i%3)
        d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=base)
        if i%5==0:
            d.ellipse((x-1.4,y-1.4,x+1.4,y+1.4),fill=(247,244,214))


def arrows(d,t,focus_hot,focus_cold):
    # Arrowheads travel along path, same direction as particles; no overlays on captions.
    for info,col,focus in ((HOT_DATA,AMBER,focus_hot),(COLD_DATA,BLUE,focus_cold)):
        for k in range(2):
            p=(t*118+info[2]*(k+0.2)/2)%info[2]
            x0,y0=path_sample(info,p)
            x1,y1=path_sample(info,p+18)
            ang=math.atan2(y1-y0,x1-x0)
            r=9+3*focus
            points=[(x1+r*math.cos(ang),y1+r*math.sin(ang)),
                    (x1-13*math.cos(ang-.5),y1-13*math.sin(ang-.5)),
                    (x1-13*math.cos(ang+.5),y1-13*math.sin(ang+.5))]
            d.polygon(points,fill=col)


def motor_angle(t):
    # Integrated smooth speed ramp: no rotational discontinuities at scene changes.
    return math.tau*(0.30*t+1.03*(t-2.6*(1-math.exp(-t/2.6))))


def frame(t):
    i,p=phase(t)
    im=BG_PANELS[i].copy().convert('RGBA')
    im.alpha_composite(BASE_SCENE)
    dynamic=Image.new('RGBA',(W,H),(0,0,0,0))
    d=ImageDraw.Draw(dynamic)
    ang=motor_angle(t)
    hot_focus=1. if i==1 else .65 if i in (2,5) else .38
    cold_focus=1. if i in (3,4) else .70 if i==5 else .35
    draw_wheel(d,L[0],L[1],ang,False,focused=i in (1,2,5))
    draw_wheel(d,RGT[0],RGT[1],ang,True,focused=i in (2,3,4,5))
    # a moving fine groove on the connecting shaft follows the same rotational phase
    xx0,xx1=490,590
    off=7*math.sin(ang)
    d.line([(xx0,855+off),(xx1,855+off)],fill=(244,214,162),width=5)
    d.line([(xx0,855-off),(xx1,855-off)],fill=(95,135,149),width=3)
    # continuous exhaust and compressor air streams, separate pipes and identities.
    visible_route(d,HOT_DATA,AMBER,hot_focus,t*114,False)
    visible_route(d,COLD_DATA,BLUE,cold_focus,t*108,True)
    arrows(d,t,hot_focus,cold_focus)
    # scene progress indicators are drawn into pre-reserved tab area, not on the apparatus.
    if 1 <= i <= 4:
        xx=55+(i-1)*244
        d.rounded_rectangle((xx+7,412,xx+7+216*p,422),radius=4,fill=TABS[i-1][1])
    im.alpha_composite(dynamic)
    return im.convert('RGB')


def audio_synth(path):
    # Original mechanical/air sound, no copyrighted audio assets.
    import wave
    sr=48000
    tt=np.arange(int(TOTAL*sr),dtype=np.float64)/sr
    # mechanical rotating drone + turbo whine without excessive volume
    speed=0.28+1.05*(1-np.exp(-tt/3.0))
    whine=460+245*speed
    cycles=np.cumsum(whine)/sr
    hum=.09*np.sin(math.tau*96*tt)+.045*np.sin(math.tau*191*tt)
    tone=.052*np.sin(math.tau*cycles)
    rng=np.random.default_rng(862)
    noise=rng.standard_normal(tt.size).astype(np.float32)
    smoothed=np.convolve(noise,np.ones(91)/91,mode='same')
    hiss=.07*smoothed
    audio=(hum+tone+hiss)*(0.60+0.40*np.minimum(1,tt/2.5))
    # short, gentle clicks/whooshes at chapter transitions
    for moment in CUTS[1:-1]:
        start=int((moment-.075)*sr); end=min(len(audio),start+int(.22*sr))
        if start<0:continue
        u=np.arange(end-start)/sr
        env=np.exp(-23*u)
        audio[start:end] += .11*np.sin(math.tau*310*u)*env
    fade=min(1,0.75)
    audio*=np.minimum(1,tt/.5)
    audio*=np.minimum(1,(TOTAL-tt)/.6)
    audio=np.clip(audio,-0.92,.92)
    pcm=(audio*32767).astype(np.int16)
    with wave.open(path,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())


def make_video(output,audio_path,limit=None):
    limit=limit or FRAMES
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}',
         '-r',str(FPS),'-i','-','-i',audio_path,'-map','0:v:0','-map','1:a:0','-c:a','aac','-b:a','160k',
         '-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p',
         '-movflags','+faststart','-t',str(limit/FPS),output]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    start=time.time()
    try:
        for j in range(limit):
            proc.stdin.write(np.asarray(frame(j/FPS),dtype=np.uint8).tobytes())
            if j%120==0:
                print('RENDER',j,'/',limit,'elapsed',round(time.time()-start,1),flush=True)
        proc.stdin.close();proc.stdin=None
        err=proc.communicate()[1]
        if proc.returncode!=0: raise RuntimeError(err.decode()[-2000:])
    except BaseException:
        proc.kill()
        raise
    print('DONE',output,round(time.time()-start,1),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',default='/mnt/data/V8_9_Turbo_Premium_2_5D_Ekrem_Gokberk_Iscan.mp4')
    ap.add_argument('--audio',default='/mnt/data/v89_turbo_original_audio.wav')
    ap.add_argument('--stills',action='store_true')
    ap.add_argument('--seconds',type=float,default=TOTAL)
    a=ap.parse_args()
    if a.stills:
        for t in (0.,4.8,9.6,15.2,20.7,24.8):
            frame(t).save(f'/mnt/data/v89_still_{str(t).replace(".","_")}.jpg',quality=94)
        print('STILLS_DONE')
    else:
        audio_synth(a.audio)
        make_video(a.output,a.audio,round(a.seconds*FPS))