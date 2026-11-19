#!/usr/bin/env python3
"""V8.4 — original frame-by-frame premium 2.5D four-stroke engine explainer.

No modification/overlay of any prior video footage: all RGB video frames are composed
from geometry and scene assets generated here. Audio is synthesized locally from original oscillators and phase cues; no third-party footage or audio is reused. Explanatory typography lives in
reserved header/stage/information panels.

Mechanical model: 4-stroke SI engine, 720 crank degrees per cycle. Slider-crank
piston movement from exact rod length, intake valve open on intake stroke and
exhaust valve open on exhaust stroke, spark at early power stroke. Stylized
particle paths illustrate air/fuel and exhaust, not CFD.
"""
import math, argparse, subprocess, sys, os, time, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W,H=1080,1920
FPS=24
DURATION=26.0
N=int(FPS*DURATION)
FD='/usr/share/fonts/opentype/inter/' if os.path.isfile('/usr/share/fonts/opentype/inter/Inter-Regular.otf') else '/usr/share/fonts/truetype/dejavu/'
FONT=FD+('Inter-Regular.otf' if 'inter' in FD else 'DejaVuSans.ttf')
FONT_B=FD+('Inter-Bold.otf' if 'inter' in FD else 'DejaVuSans-Bold.ttf')
FONT_M=FD+('Inter-Medium.otf' if 'inter' in FD else 'DejaVuSans.ttf')
FONT_SB=FD+('Inter-SemiBold.otf' if 'inter' in FD else 'DejaVuSans-Bold.ttf')
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

# Static engine layers, re-used, no external PNG assets.
CENTER_X=540
CRANK_Y=1182
R=108
ROD_LENGTH=310
P_HEIGHT=140
CH_Y=570
CYL_LEFT=333
CYL_RIGHT=747


def engine_base_layer():
    im=Image.new('RGBA',(W,H),(0,0,0,0))
    d=ImageDraw.Draw(im)
    # rear crankcase shadow and disk; detailed metallic rings
    d.ellipse((CENTER_X-206,CRANK_Y-206,CENTER_X+206,CRANK_Y+206),fill=(8,11,15),outline=(73,62,45),width=5)
    for r,col,w in [(190,(98,76,48),14),(170,(174,147,99),6),(156,(47,44,43),7),(135,(72,65,55),2)]:
        d.ellipse((CENTER_X-r,CRANK_Y-r,CENTER_X+r,CRANK_Y+r),outline=col,width=w)
    d.ellipse((CENTER_X-130,CRANK_Y-130,CENTER_X+130,CRANK_Y+130),fill=(58,48,38))
    for a in range(0,360,45):
        rad=math.radians(a)
        x,y=CENTER_X+172*math.cos(rad),CRANK_Y+172*math.sin(rad)
        bolt(d,x,y,7)
    # cylinder outer casting shell
    bevel_box(d,(CYL_LEFT-35,CH_Y-4,CYL_RIGHT+35,1062),34,face=(68,59,48),stroke=(172,152,121),highlight=(199,174,138),depth=13)
    d.rounded_rectangle((CYL_LEFT-14,CH_Y+12,CYL_RIGHT+14,1040),radius=22,fill=(30,26,25),outline=(135,113,83),width=6)
    d.rounded_rectangle((CYL_LEFT+9,CH_Y+18,CYL_RIGHT-9,1032),radius=12,fill=(24,21,20),outline=(70,60,48),width=2)
    # three dimensional rim cavity ridge / edge on both sides
    d.line([(CYL_LEFT-5,CH_Y+32),(CYL_LEFT-5,1025)],fill=(204,182,143),width=6)
    d.line([(CYL_LEFT+10,CH_Y+38),(CYL_LEFT+10,1018)],fill=(119,102,79),width=7)
    d.line([(CYL_RIGHT+5,CH_Y+33),(CYL_RIGHT+5,1025)],fill=(175,150,112),width=7)
    d.line([(CYL_RIGHT-12,CH_Y+33),(CYL_RIGHT-12,1018)],fill=(94,75,54),width=6)
    # outer mounts
    for yy in (622,744,862,980):
        bolt(d,CYL_LEFT-25,yy,11); bolt(d,CYL_RIGHT+25,yy,11)
    # intake / exhaust machined manifolds, 2.5D round pipes
    bevel_box(d,(142,541,366,608),26,(116,92,52),(153,128,82),(204,171,104),6)
    bevel_box(d,(714,541,942,608),26,(102,73,54),(158,113,79),(207,163,108),6)
    # ports have dark inner flow channel
    d.rounded_rectangle((154,552,365,593),radius=19,fill=(65,56,40))
    d.rounded_rectangle((715,552,932,593),radius=19,fill=(66,46,36))
    # head casting and valve sleeves
    bevel_box(d,(320,484,760,642),25,(90,76,57),(190,173,141),(238,216,166),6)
    d.rounded_rectangle((338,498,741,620),radius=19,fill=(43,36,30),outline=(139,122,97),width=5)
    d.line([(355,510),(721,510)],fill=(162,142,104),width=3)
    # cylinder's upper chamber visible from below lower head
    d.rounded_rectangle((348,623,731,674),radius=9,fill=(25,20,19))
    # left/right fixed port labels, intentionally positioned above pipe (not over movable object)
    d.text((161,507),'IN',font=F_INOUT,fill=(223,206,159))
    d.text((852,507),'OUT',font=F_INOUT,fill=(223,206,159))
    # cylinder head bolts
    for x in (346,730): bolt(d,x,613,9)
    # central spark electrode fixed component
    d.rounded_rectangle((529,445,551,560),radius=10,fill=(222,207,168),outline=(84,76,63),width=3)
    d.rectangle((535,526,545,624),fill=(223,216,194))
    d.rounded_rectangle((526,601,554,632),radius=6,fill=(207,201,168))
    # static valve collar mounts
    for x in (447,633):
        d.rounded_rectangle((x-44,542,x+44,562),radius=10,fill=(167,157,133),outline=(227,205,160),width=3)
        d.rounded_rectangle((x-11,504,x+11,546),radius=6,fill=(195,187,161))
    # bottom machine badge
    d.rounded_rectangle((438,1338,642,1379),radius=16,fill=(20,25,29),outline=(68,68,60),width=2)
    text_center(d,(540,1358),'SECTION / 01',F_MICRO,(153,146,134))
    return im

ENGINE_BASE=engine_base_layer()

def engine_front_layer():
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
    # bottom lip, foreground occlusion, casting bolthead
    d.rounded_rectangle((308,1029,774,1085),radius=19,fill=(72,61,48),outline=(160,136,103),width=5)
    d.line([(345,1041),(741,1041)],fill=(187,163,125),width=4)
    for x in (344,736): bolt(d,x,1054,12)
    # static crankshaft shaft cap
    d.ellipse((510,1152,570,1212),fill=(177,154,113),outline=(77,66,49),width=7)
    d.ellipse((525,1167,555,1197),fill=(225,204,157))
    return im
FRONT=engine_front_layer()

# stage templates: all text integrated at layout stage, not pasted over an existing video

def build_stage_base(stage):
    bg=BASE.copy();d=ImageDraw.Draw(bg)
    idx,title,lead,detail,accent=STAGES[stage]
    d.text((56,62),'INSIDE THE MACHINE',font=F_KICKER,fill=(109,216,228))
    d.text((370,62),'/  EPISODE 01',font=F_KICKER,fill=(101,149,169))
    text_right(d,(1022,62),'4-STROKE  /  2.5D CUTAWAY',F_MICRO,(136,144,157))
    d.text((56,145),'HOW AN ENGINE',font=F_HEADER,fill=WHITE)
    d.text((56,212),'TURNS FUEL INTO MOTION',font=F_HEADER,fill=WHITE)
    # step tabs occupy dedicated area
    d.line([(55,308),(1025,308)],fill=(93,82,67),width=2)
    for si,(name,col) in enumerate(zip(STEP_NAMES,STEP_COLORS)):
        xx=55+si*244
        active=(si==stage-1)
        d.rounded_rectangle((xx,326,xx+230,424),radius=22,
            fill=(48,59,64) if active else (36,35,35),
            outline=col if active else (59,56,51),width=3 if active else 1)
        if active:
            d.rounded_rectangle((xx+6,412,xx+224,422),radius=4,fill=col)
        d.text((xx+17,346),f'{si+1:02d}',font=F_INDEX,fill=col if active else (104,98,92))
        d.text((xx+64,354),name,font=F_STAGE,fill=WHITE if active else (141,143,149))
        d.ellipse((xx+110,436,xx+120,446),fill=col if active else (80,70,60))
    # caption card in own area separate from machine
    d.rounded_rectangle((58,1474,1022,1735),radius=28,fill=(32,27,25),outline=(94,75,53),width=2)
    d.line([(138,1502),(942,1502)],fill=(87,72,57),width=2)
    text_center(d,(540,1557),title,F_BIG,accent)
    text_center(d,(540,1642),lead,F_DESC,WHITE)
    text_center(d,(540,1709),detail,F_DETAIL,MUTED)
    # bottom progress + reserved footer
    d.line([(60,1787),(1020,1787)],fill=(76,67,57),width=3)
    d.line([(60,1787),(60+(stage if stage<5 else 4)*240,1787)],fill=accent,width=7)
    text_center(d,(540,1830),'ONE CYCLE = TWO CRANKSHAFT ROTATIONS',F_FOOT,(159,178,193))
    d.line([(62,1863),(1018,1863)],fill=(63,68,69),width=2)
    d.text((62,1877),'ORIGINAL MOTION DESIGN',font=F_MICRO,fill=(125,128,129))
    text_right(d,(1018,1877),'Ekrem Gökberk İşcan',F_WM,(188,188,180))
    return bg
STAGE_BASE=[build_stage_base(i) for i in range(6)]


def tapered_line(d,xy1,xy2,width,color,outline=None):
    x0,y0=xy1; x1,y1=xy2
    if outline:
        d.line([(x0,y0),(x1,y1)],fill=outline,width=width+12,joint='curve')
        for x,y,r in ((x0,y0,(width+12)/2),(x1,y1,(width+12)/2)):
            d.ellipse((x-r,y-r,x+r,y+r),fill=outline)
    d.line([(x0,y0),(x1,y1)],fill=color,width=width,joint='curve')
    for x,y,r in ((x0,y0,width/2),(x1,y1,width/2)):
        d.ellipse((x-r,y-r,x+r,y+r),fill=color)


def draw_gas(back,st,p,top):
    # Continuous charge motion: particles persist visually from one stroke to the next
    # instead of disappearing and reappearing as a new set.
    g=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(g)
    gap=max(18.,top-640)
    left,right=366,714

    def chamber_particle(xx,yy,rr,col,a):
        if xx<left+6 or xx>right-6 or yy<642 or yy>top-10:
            return
        d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill=(*col,int(a)))

    if st==1:  # intake: charge enters and visually fills the chamber volume
        d.rounded_rectangle((153,549,420,594),radius=20,fill=(*BLUE,44))
        # intake runner particles
        for i in range(16):
            u=(p*1.65+i/16)%1
            xi=lerp(184,444,u)
            yi=571+10*math.sin((u*2.4+i)*math.pi)
            rr=5+2.2*u
            d.ellipse((xi-rr,yi-rr,xi+rr,yi+rr),fill=(*BLUE,int(105+130*u)))
        # No full-area fill, haze or ellipse inside the intake cylinder.
        # Only individual moving particles are allowed in the charge space.
        # chamber particles spread out from the intake valve and occupy the whole volume
        for i in range(70):
            s=(p*1.05+i/70)%1
            spread=(0.16 + 0.84*smoothstep(p))
            xx=452+172*s + spread*36*math.sin(i*0.67+s*6.1)
            yy=650+(gap-20)*(0.05+0.90*s)
            rr=3.4+2.8*(1-s)
            chamber_particle(xx,yy,rr,BLUE,125+105*(1-s))
        # a second softer set gives the impression that the incoming charge really fills the cavity
        for i in range(44):
            s=(i/43 + p*0.42)%1
            xx=430+220*((i*0.754877666)%1)
            yy=655+(gap-26)*s
            rr=2.5+1.8*((i%5)/4)
            chamber_particle(xx,yy,rr,(130,230,255),88+82*s)

    elif st==2:  # compression: same charge is squeezed upward and warms slightly near the end
        warm=smoothstep(max(0,(p-0.55)/0.45))
        for i in range(44):
            u=i/43
            # start from filled volume, end as compressed cluster near spark plug
            x0=438+204*u + 18*math.sin(i*1.31)
            y0=658+(gap-22)*(0.10+0.82*((i*0.61803398875)%1))
            x1=540+70*math.cos(i*2.39996322973)
            y1=676+min(86,max(20,gap*0.22))*abs(math.sin(i*1.17))
            xx=lerp(x0,x1,smoothstep(p))
            yy=lerp(min(y0,top-16),min(y1,top-20),smoothstep(p))
            rr=lerp(4.3,2.7,smoothstep(p))
            col=(
                int(lerp(BLUE[0],GOLD[0],warm*0.55)),
                int(lerp(BLUE[1],GOLD[1],warm*0.55)),
                int(lerp(BLUE[2],GOLD[2],warm*0.55)),
            )
            chamber_particle(xx,yy,rr,col,92+90*(1-u))
        for k in range(3):
            yy=top-18-k*10
            if yy<656: continue
            d.line([(406,yy),(676,yy)],fill=(*GOLD,int(18+54*warm)),width=3)

    elif st==3:  # power: compressed charge ignites, then expands downward smoothly
        ignite=smoothstep(min(1,p/0.26))
        for i in range(46):
            u=i/45
            # compressed position near top at stage start
            x0=540+68*math.cos(i*2.39996322973)
            y0=678+min(82,max(18,gap*0.22))*abs(math.sin(i*1.17))
            # expanded position pushes down with swirl, still inside cylinder
            x1=540+142*math.cos(i*1.91)*(0.45+0.55*u)
            y1=702+(top-720)*(0.24+0.68*((i*0.38196601125)%1))
            xx=lerp(x0,x1,smoothstep(p))
            yy=lerp(min(y0,top-20),min(y1,top-18),smoothstep(p))
            rr=lerp(2.8,4.6,ignite*(0.4+0.6*(1-u)))
            col=(
                int(lerp(GOLD[0],AMBER[0],ignite)),
                int(lerp(GOLD[1],AMBER[1],ignite)),
                int(lerp(BLUE[2],AMBER[2],ignite)),
            )
            chamber_particle(xx,yy,rr,col,94+110*(1-u))
        if p<.30:
            intensity=math.sin(math.pi*clamp(p/.30))
            R0=int(30+92*intensity)
            d.ellipse((540-R0,678-R0*.56,540+R0,678+R0*.58),fill=(255,193,88,int(60*intensity)))
            for j in range(10):
                ang=j*2*math.pi/10
                x1,y1=540+26*math.cos(ang),670+18*math.sin(ang)
                x2,y2=540+88*math.cos(ang),670+68*math.sin(ang)
                d.line([(x1,y1),(x2,y2)],fill=(*GOLD,int(138*intensity)),width=4)

    elif st==4:  # exhaust: hot gases rise and leave through the exhaust port continuously
        vent=smoothstep(p)
        for i in range(38):
            u=i/37
            # carry over hot gases from power stroke and push them toward exhaust valve
            x0=540+135*math.cos(i*1.91)*(0.45+0.45*u)
            y0=706+(top-722)*(0.18+0.72*((i*0.38196601125)%1))
            x1=622+34*math.sin(i*0.9)
            y1=662+(1-u)*18
            xx=lerp(x0,x1,vent)
            yy=lerp(min(y0,top-20),y1,vent)
            rr=lerp(4.2,3.0,vent)
            col=(
                int(lerp(AMBER[0],TEAL[0],vent*0.55)),
                int(lerp(AMBER[1],TEAL[1],vent*0.30)),
                int(lerp(RED[2],TEAL[2],vent*0.75)),
            )
            chamber_particle(xx,yy,rr,col,88+110*(1-u))
        # particles visible through exhaust runner, matching what just left the chamber
        d.rounded_rectangle((715,549,932,593),radius=20,fill=(*TEAL,34))
        for i in range(24):
            u=(p*1.28+i/24)%1
            xx=648+lerp(0,284,u)
            yy=571+12*math.sin(u*7.2+i*.75)
            rr=4+2.2*u
            col=(
                int(lerp(AMBER[0],TEAL[0],0.55+0.45*u)),
                int(lerp(AMBER[1],TEAL[1],0.35+0.40*u)),
                int(lerp(RED[2],TEAL[2],0.65+0.35*u)),
            )
            d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill=(*col,int(82+104*u)))
    back.alpha_composite(g)

def valve(d,cx,open_fraction,accent):
    # stem and mechanically visible spring, lift pushes head toward cylinder when open
    lift=int(27*open_fraction)
    d.rounded_rectangle((cx-9,481,cx+9,641+lift),radius=6,fill=(187,182,155),outline=(101,91,72),width=2)
    for i in range(4):
        y=489+i*18
        d.line([(cx-31,y+2),(cx+31,y+9)],fill=(204,192,157),width=6)
        d.line([(cx-31,y+6),(cx+31,y+13)],fill=(94,83,64),width=2)
    head_y=647+lift
    d.rounded_rectangle((cx-49,head_y-8,cx+49,head_y+13),radius=10,fill=(216,205,174),outline=(76,66,51),width=4)
    d.line([(cx-39,head_y-4),(cx+39,head_y-4)],fill=accent if open_fraction>0 else (159,141,112),width=6)


def piston(d,cx,cy,theta):
    # connecting rod and eccentric pin are actual slider-crank geometry
    crank_pin=(cx+R*math.sin(theta),CRANK_Y-R*math.cos(theta))
    piston_pin=(cx,cy)
    # throw, piston rod behind piston
    tapered_line(d,(cx,CRANK_Y),crank_pin,42,(180,155,114),(45,36,26))
    tapered_line(d,(cx,CRANK_Y),crank_pin,22,(223,195,147))
    tapered_line(d,piston_pin,crank_pin,39,(178,149,107),(39,32,24))
    tapered_line(d,piston_pin,crank_pin,22,(233,214,173))
    # counterweight on crank: rotates around axis
    ang=theta+math.pi
    px=cx+100*math.sin(ang);py=CRANK_Y-100*math.cos(ang)
    d.ellipse((px-55,py-55,px+55,py+55),fill=(117,99,74),outline=(66,56,43),width=5)
    # eccentric bolt and polished metal ring
    x,y=crank_pin
    d.ellipse((x-31,y-31,x+31,y+31),fill=(54,42,30),outline=(211,175,119),width=8)
    d.ellipse((x-12,y-12,x+12,y+12),fill=(227,204,163))
    # crank center cap
    d.ellipse((cx-29,CRANK_Y-29,cx+29,CRANK_Y+29),fill=(172,149,111),outline=(66,54,39),width=5)
    d.ellipse((cx-11,CRANK_Y-11,cx+11,CRANK_Y+11),fill=(232,215,175))
    # piston body; highlights/ grooves integrated, not labels
    top=cy-P_HEIGHT/2
    x0,x1=cx-175,cx+175
    bevel_box(d,(x0,top,x1,top+P_HEIGHT),25,(174,170,151),(91,77,60),(254,243,208),5)
    d.rounded_rectangle((x0+16,top+14,x1-16,top+71),radius=14,fill=(204,202,188))
    d.line([(x0+23,top+19),(x1-24,top+19)],fill=(255,251,234),width=7)
    d.line([(x0+23,top+30),(x1-24,top+30)],fill=(154,148,132),width=2)
    for q in (84,99,114):
        d.line([(x0+19,top+q),(x1-19,top+q)],fill=(94,80,62),width=7)
        d.line([(x0+20,top+q-5),(x1-20,top+q-5)],fill=(213,202,174),width=2)
    # wrist pin
    d.ellipse((cx-24,cy-12,cx+24,cy+36),fill=(75,61,44),outline=(224,203,161),width=5)
    d.ellipse((cx-13,cy-1,cx+13,cy+25),fill=(218,206,171))
    return top


def crank_arrow(d,theta,alpha=1.):
    points=arc_poly(CENTER_X,CRANK_Y,218,218,-45,48,n=48)
    d.line(points,fill=GOLD,width=7,joint='curve')
    end=points[-1]
    angle=math.radians(48)
    arr=[(end[0]-27*math.cos(angle-.65),end[1]-27*math.sin(angle-.65)),
        (end[0]-27*math.cos(angle+.65),end[1]-27*math.sin(angle+.65))]
    d.polygon([end,*arr],fill=GOLD)


def render_frame(t):
    st,p=stage_at(t)
    im=STAGE_BASE[st].copy().convert('RGBA')
    im.alpha_composite(ENGINE_BASE)
    # each non-hook segment corresponds to exactly half a crank revolution
    if st==0: theta=0
    elif st==5: theta=4*math.pi
    else: theta=((st-1)+p)*math.pi
    crank_pos=CRANK_Y-(R*math.cos(theta)+math.sqrt(ROD_LENGTH*ROD_LENGTH-R*R*math.sin(theta)**2))
    piston_top=crank_pos-P_HEIGHT/2
    # flow before moving foreground piston, ensuring piston occludes gas and always readable
    draw_gas(im,st,p,piston_top)
    dynamic=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(dynamic)
    # ports highlight only when valved open
    if st==1:
        d.rounded_rectangle((147,548,364,597),radius=20,outline=(*BLUE,220),width=7)
    elif st==4:
        d.rounded_rectangle((718,548,942,597),radius=20,outline=(*TEAL,220),width=7)
    piston(d,CENTER_X,crank_pos,theta)
    # intake/exhaust valves open independently, strokes use smooth ramp for readability
    v=math.sin(math.pi*clamp(p))**.6 if st in (1,4) else 0
    valve(d,445,v if st==1 else 0.,BLUE)
    valve(d,633,v if st==4 else 0.,TEAL)
    # spark from TDC when stage 3 begins
    if st==3 and p<.23:
        intensity=math.sin(math.pi*clamp(p/.23))
        y=682
        d.line([(540,625),(531,y-3),(549,y+20),(535,y+43)],fill=(*GOLD,int(220*intensity)),width=8)
        d.ellipse((525,y-11,555,y+12),fill=(*AMBER,int(180*intensity)))
    if st not in (0,5): crank_arrow(d,theta)
    # thin stage progress line within section bar; not an overlay on scene
    if st in (1,2,3,4):
        xx=55+(st-1)*244
        d.rounded_rectangle((xx+7,412,xx+7+217*p,422),radius=4,fill=STAGES[st][4])
    im.alpha_composite(dynamic)
    im.alpha_composite(FRONT)
    return im.convert('RGB')


def make_video(path,audio,frames=N):
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-']
    if audio and os.path.exists(audio):
        cmd += ['-i',audio]
    cmd += ['-map','0:v:0']
    if audio and os.path.exists(audio): cmd += ['-map','1:a:0','-c:a','aac','-b:a','128k','-ar','48000']
    else:cmd += ['-an']
    cmd += ['-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',
        '-movflags','+faststart','-t',str(frames/FPS),path]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    start=time.time()
    try:
        for frame in range(frames):
            im=render_frame(frame/FPS)
            process.stdin.write(np.asarray(im,dtype=np.uint8).tobytes())
            if frame%48==0:
                print(f'FRAME {frame}/{frames} elapsed={time.time()-start:.1f}s',flush=True)
        process.stdin.close()
        process.stdin=None
        stderr=process.communicate()[1]
        if process.returncode!=0: raise RuntimeError(f'ffmpeg failed: {stderr[-1500:]}')
    except Exception:
        try:process.kill()
        except:pass
        raise
    print('DONE',path,'elapsed',round(time.time()-start,1))


def make_original_audio(path):
    """Original non-copyright audio: quiet crank hum and stage-specific short cues."""
    sr=48000
    t=np.arange(int(DURATION*sr),dtype=np.float32)/sr
    output=.013*np.sin(2*np.pi*74*t)+.009*np.sin(2*np.pi*146*t)
    # Cyclic crank accent, separate from stage labels
    for at in np.arange(1.0,DURATION-.3,.50):
        s=int(at*sr); n=int(.09*sr)
        u=np.arange(n,dtype=np.float32)/sr
        output[s:s+n]+=.024*np.exp(-u*39)*np.sin(2*np.pi*420*u)
    for at,frequency in ((2,340),(7.5,610),(13,860),(18.5,390),(24,460)):
        s=int(at*sr); n=int(.34*sr)
        u=np.arange(n,dtype=np.float32)/sr
        output[s:s+n]+=.082*np.sin(2*np.pi*(frequency*u+110*u*u))*np.exp(-u*12)
    output*=np.minimum(1,t/.5)*np.minimum(1,(DURATION-t)/.55)
    os.makedirs(os.path.dirname(os.path.abspath(path)),exist_ok=True)
    with wave.open(path,'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(output,-.85,.85)*32767).astype('<i2').tobytes())

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--stills',action='store_true')
    a.add_argument('--video',default=os.path.join(os.environ.get('EGI_OUTPUT_DIR','/tmp'),'EGI_Engine_Four_Stroke_V88.mp4'))
    a.add_argument('--audio',default=os.path.join(os.environ.get('EGI_OUTPUT_DIR','/tmp'),'egi_engine_v88.wav'))
    a.add_argument('--seconds',type=float,default=DURATION)
    opt=a.parse_args()
    if opt.stills:
        for t in (0,5,9.8,15.2,21.7,24.5):
            render_frame(t).save(os.path.join(os.environ.get('EGI_OUTPUT_DIR','/tmp'),f'egi_engine_still_{str(t).replace(".","_")}.jpg'),quality=92)
        print('STILLS DONE')
    else:
        if not os.path.isfile(opt.audio):
            make_original_audio(opt.audio)
        make_video(opt.video,opt.audio,int(opt.seconds*FPS))