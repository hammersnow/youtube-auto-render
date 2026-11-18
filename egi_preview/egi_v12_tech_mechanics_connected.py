#!/usr/bin/env python3
"""EGI V12: continuous 2.5D wireless induction and open differential explainers.
36 seconds per video, no cuts/slide transitions; synchronized visual event SFX.
Mechanisms illustrated schematically, not CFD/electromagnetic FEM or CAD.
Depends on egi_v11_software_continuous.py drawing helpers.
"""
import math, os, argparse, subprocess, time, wave
import numpy as np
from PIL import Image, ImageDraw
import egi_v12_software_connected as b
W,H,FPS,DUR=b.W,b.H,b.FPS,b.DUR
P=os.environ.get('EGI_OUTPUT_DIR','/mnt/data')
BLUE,CYAN,GOLD,TEAL,CORAL,SILVER,WHITE,GRAY=b.BLUE,b.CYAN,b.GOLD,b.TEAL,b.CORAL,b.SILVER,b.WHITE,b.GRAY
mix,smooth,clamp,ramp,gate,fit,rbox,dot,arrow=b.mix,b.smooth,b.clamp,b.ramp,b.gate,b.fit,b.rbox,b.dot,b.arrow

CAPTIONS={
 'tech':[
   (0,4.0,'THE HIDDEN POWER PATH','No cable, but two coils are still connected by a changing field.'),
   (4,9.0,'AC THROUGH THE PAD','Alternating current drives the transmitter coil.'),
   (9,15,'A CHANGING MAGNETIC FIELD','The varying field links to the coil inside the phone.'),
   (15,21,'INDUCED AC IN THE PHONE','The receiver coil generates an alternating voltage.'),
   (21,27,'POWER ELECTRONICS TAKE OVER','Rectification and regulation prepare safe battery charging.'),
   (27,32,'THE BATTERY GAINS ENERGY','Controlled DC current charges the battery.'),
   (32,36,'ENERGY CROSSES THE GAP','Pad coil → changing field → receiver → circuit → battery.')
 ],
 'mechanical':[
   (0,4,'ONE INPUT. TWO OUTPUTS.','The ring gear drives the differential carrier.'),
   (4,10,'STRAIGHT AHEAD','Both wheel speeds match. Spider gears do not spin on their axes.'),
   (10,16,'WHY A TURN CHANGES THINGS','The outside wheel follows a longer path.'),
   (16,24,'SPIDER GEARS ALLOW SLIP','Relative gear motion lets wheel speeds differ.'),
   (24,29,'THE OUTSIDE WHEEL SPEEDS UP','The inside wheel slows by the same amount.'),
   (29,33,'THE SPEEDS STILL ADD UP','Left speed + right speed = twice the carrier speed.'),
   (33,36,'ONE DRIVE. TWO WHEEL SPEEDS.','An open differential makes smooth cornering possible.')
 ]
}
CAM={
 'tech':[(0,540,930,1.),(4,400,1108,1.14),(7.7,402,1136,1.18),(12.5,406,916,1.22),(17,610,804,1.23),(24.5,795,924,1.24),(30.8,794,991,1.21),(34.7,540,930,1.0),(36,540,930,1.0)],
 'mechanical':[(0,540,918,1.),(4.0,532,875,1.13),(9.6,532,875,1.19),(15.5,528,906,1.13),(21.2,533,918,1.21),(27.1,538,922,1.14),(33.6,540,930,1.),(36,540,930,1.)]
}


def bg(mode):
    y=np.arange(H,dtype=np.float32)[:,None];x=np.arange(W,dtype=np.float32)[None,:]
    ambient=np.maximum(0,1-((x-535)/805)**2-((y-965)/1070)**2)
    arr=np.zeros((H,W,3),dtype=np.uint8)
    for ch,n in enumerate(b.NAVY):arr[:,:,ch]=np.clip(n+ambient*(15 if ch==2 else 8)+y/H*(8 if ch==2 else 2),0,255)
    im=Image.fromarray(arr,'RGB');d=ImageDraw.Draw(im)
    for xx in range(53,1050,82):d.line([(xx,365),(xx,1470)],fill=(21,43,58),width=1)
    for yy in range(373,1490,82):d.line([(30,yy),(1053,yy)],fill=(21,43,58),width=1)
    d.rounded_rectangle((26,351,1052,1467),radius=30,outline=(51,87,110),width=3)
    d.line([(54,118),(1028,118)],fill=(64,109,132),width=2)
    d.line([(54,331),(1028,331)],fill=(64,109,132),width=2)
    fit(d,'EGI',(55,47,195,111),66,50,WHITE,'bold')
    fit(d,('TECHNOLOGY / 01' if mode=='tech' else 'MECHANICS / 01'),(225,57,558,100),26,22,BLUE if mode=='tech' else GOLD,'semi')
    fit(d,'ONE CONTINUOUS PROCESS',(630,60,1028,97),23,20,GRAY,'semi',True)
    first,second=(('HOW WIRELESS CHARGING','ACTUALLY WORKS') if mode=='tech' else ('WHY WHEELS TURN','AT DIFFERENT SPEEDS'))
    fit(d,first,(55,153,1020,221),56,41,WHITE,'bold')
    fit(d,second,(55,222,1020,292),67,44,WHITE,'bold')
    rbox(d,(43,1510,1037,1774),(26,30,35),(81,75,68),r=28,w=3)
    d.line([(80,1559),(998,1559)],fill=(90,79,66),width=2)
    d.line([(61,1800),(1019,1800)],fill=(77,85,89),width=2)
    d.line([(61,1858),(1019,1858)],fill=(62,78,91),width=2)
    fit(d,'Curiosity in Motion',(58,1874,495,1916),26,20,GRAY)
    fit(d,'Ekrem Gökberk İşcan',(714,1874,1020,1916),26,20,SILVER)
    return im
BASE={m:bg(m) for m in ('tech','mechanical')}

# Metallized enamel coils, fully drawn every frame with uninterrupted rotation.
def coil(d,cx,cy,rx,ry,t,hot=False,focus=.5):
    edge=(141,104,69) if hot else (90,148,162)
    dark=(50,34,23) if hot else (24,48,57)
    glow=GOLD if hot else BLUE
    # 2.5D metallic rim
    d.ellipse((cx-rx-22,cy-ry-12,cx+rx+22,cy+ry+20),fill=(11,21,28),outline=(75,93,102),width=7)
    d.ellipse((cx-rx-15,cy-ry-16,cx+rx+15,cy+ry+11),fill=dark,outline=edge,width=7)
    for k in range(10):
        r=1-k*.073
        d.ellipse((cx-rx*r,cy-ry*r,cx+rx*r,cy+ry*r),outline=mix(edge,glow,k/14+.15),width=7)
        a=t*2.1+k*.35
        x=cx+rx*r*math.cos(a);y=cy+ry*r*math.sin(a)
        dot(d,x,y,3.8,WHITE if k%3==0 else glow)
    for k in range(4):
        a=t*1.2+k*math.tau/4
        x=cx+rx*.89*math.cos(a);y=cy+ry*.89*math.sin(a)
        dot(d,x,y,5+2*focus,glow)


def static_tech():
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
    # phone and charging pad in exploded cutaway, orientation exaggerated for clarity
    rbox(d,(108,488,711,918),(13,21,29),(78,113,133),r=45,w=9)
    rbox(d,(131,510,692,898),(28,54,64),(164,199,206),r=39,w=5)
    d.line([(158,524),(642,524)],fill=(220,233,229),width=3)
    fit(d,'PHONE / CUTAWAY',(153,538,667,600),32,25,WHITE,'bold',True)
    # receiver bobbin backing circle
    d.ellipse((228,604,584,823),fill=(10,34,45),outline=(73,143,165),width=5)
    # phone's circuit trace exit
    d.line([(570,700),(670,700),(736,765)],fill=(57,91,103),width=19,joint='curve')
    d.line([(570,691),(670,691),(736,755)],fill=(129,181,192),width=3,joint='curve')
    # AC induction charger pad below
    rbox(d,(122,1124,710,1403),(13,20,28),(66,95,109),r=42,w=9)
    rbox(d,(139,1139,690,1382),(47,53,53),(172,141,102),r=37,w=5)
    d.line([(164,1150),(670,1150)],fill=(233,191,140),width=3)
    fit(d,'CHARGING PAD',(174,1345,648,1390),27,22,GOLD,'bold',True)
    # input AC source graphic left of pad
    rbox(d,(51,1127,160,1263),(20,40,54),(84,120,145),r=20,w=3)
    fit(d,'AC',(61,1139,148,1186),29,22,BLUE,'bold',True)
    # electronics on right side (schematically exploded from phone)
    rbox(d,(752,683,1024,867),(24,38,46),(119,152,169),r=24,w=5)
    fit(d,'POWER IC',(774,704,1007,765),29,22,WHITE,'bold',True)
    d.line([(780,763),(996,763)],fill=(67,104,124),width=2)
    for k in range(4):
        d.rounded_rectangle((779+k*59,793,812+k*59,830),radius=7,fill=(42,82,94),outline=(106,150,161),width=2)
    rbox(d,(785,925,1008,1289),(35,54,61),(143,177,177),r=27,w=5)
    d.rounded_rectangle((877,914,917,943),radius=7,fill=(143,177,177))
    d.rounded_rectangle((804,956,987,1245),radius=17,fill=(14,35,39),outline=(72,119,130),width=2)
    fit(d,'BATTERY',(802,1261,999,1293),25,19,TEAL,'bold',True)
    d.line([(875,867),(875,927)],fill=(86,136,145),width=15)
    d.line([(875,867),(875,927)],fill=(158,204,204),width=3)
    fit(d,'MAGNETIC COUPLING',(173,948,689,998),31,22,BLUE,'bold',True)
    fit(d,'GAP ENLARGED FOR CLARITY',(194,1011,663,1051),20,16,GRAY,'semi',True)
    return im
TECH_BASE=static_tech()


def circuit_packets(d,points,t,col,begin,velocity=110,n=10):
    info=b.prep(points)
    for k in range(n):
        age=t-begin-k*.16
        if age<0:continue
        dist=velocity*age
        if dist>info[2]:continue
        x,y=b.path_xy(info,dist)
        dot(d,x,y,4+(k%3),col)
        if k%3==0:
            x2,y2=b.path_xy(info,max(0,dist-15));d.line([(x2,y2),(x,y)],fill=mix((32,62,80),col,.65),width=3)


def tech_dynamic(d,t):
    coil(d,406,717,167,91,t,False,ramp(t,9,13))
    coil(d,413,1254,238,85,t,True,ramp(t,3,8))
    # animated AC, left input
    vals=[]
    for xx in range(63,147,3):
        yy=1226-22*math.sin((xx/37+t*1.8)*math.tau)
        vals.append((xx,yy))
    d.line(vals,fill=GOLD,width=4,joint='curve')
    # animated flux: curved lines, no translucent bubble/fill
    focus=ramp(t,5,9)
    for k in range(11):
        phase=t*4.9+k*.45
        x=242+k*33
        wobble=12*math.sin(phase)
        c=mix((37,67,84),BLUE,.3+.50*focus+.13*math.sin(phase))
        # flux follows a continuous curved path from near lower coil toward receiver
        pts=[]
        for j in range(23):
            u=j/22
            xj=x+27*math.sin(u*math.pi*1.7+phase*.2)*math.sin(u*math.pi)
            yj=1120-251*u+(-18*math.sin(u*math.pi))
            pts.append((xj,yj))
        d.line(pts,fill=c,width=3,joint='curve')
        # each field marker moves along the same curve rather than appearing as a blob
        u=((t*.42+k*.11)%1)
        j=int(u*21);xj,yj=pts[j];dot(d,xj,yj,4,CYAN)
    # induced AC travels into regulator
    lines=[[(550,701),(660,701),(759,781)],[(780,867),(874,867),(874,945)]]
    for pts,col,st in ((lines[0],BLUE,13.4),(lines[1],TEAL,21.0)):
        d.line(pts,fill=mix((45,91,107),col,.53),width=5,joint='curve')
        circuit_packets(d,pts,t,col,st,125,11)
    # small independent IC gates pulse along with rectifier activity
    for k in range(4):
        on=ramp(t,17.0,21.5)
        c=mix((49,86,100),TEAL,.18+on*(.4+.4*math.sin(t*7+k*1.2)**2))
        d.rounded_rectangle((783+k*59,797,809+k*59,825),radius=5,fill=c)
        if on>.2:
            dot(d,795+k*59,809,3,WHITE)
    # battery charges gradually, direct consequence of regulated current
    amt=.15+.72*ramp(t,22,32)
    fill_h=int(275*amt)
    d.rounded_rectangle((814,1236-fill_h,977,1236),radius=13,fill=TEAL)
    for j in range(8):
        xx=829+(j%4)*43; yy=1194-((t*48+j*43)%220)
        if yy>1236-fill_h:dot(d,xx,yy,3,WHITE)
    # moving charge percentage and charging bolt emblem
    pct=int(amt*100)
    fit(d,str(pct)+'%',(813,968,975,1037),43,32,WHITE,'bold',True)
    d.line([(897,1098),(866,1141),(895,1141),(875,1182)],fill=(216,255,229),width=7,joint='curve')
    # schematic screen at top gains a small charging pulse
    p=.4+.6*math.sin(t*1.2)**2
    d.arc((348,584,468,703),215,333,fill=mix((53,86,100),TEAL,p),width=6)
    # active motion traces for caption area of apparatus
    d.line([(178,1087),(685,1087)],fill=(56,83,99),width=2)
    for k in range(6):
        x=198+((t*57+k*94)%450); dot(d,x,1087,3,BLUE)


def integ_turn(t):
    if t<=12:return 0.
    if t>=20:return t-16.
    s=(t-12)/8
    return 8*(s**3-.5*s**4)


def gear(d,cx,cy,r,angle,col=GOLD,teeth=22,thick=14):
    pts=[]
    for j in range(teeth*4):
        a=angle+j*math.tau/(teeth*4)
        rr=r+(8 if j%4 in (1,2) else -7)
        pts.append((cx+rr*math.cos(a),cy+rr*math.sin(a)))
    d.polygon([(xx+9,yy+10) for xx,yy in pts],fill=(9,15,22))
    d.polygon(pts,fill=mix(col,(27,45,54),.56),outline=col)
    d.ellipse((cx-r*.75,cy-r*.75,cx+r*.75,cy+r*.75),fill=(21,38,48),outline=mix(col,WHITE,.26),width=6)
    for j in range(5):
        a=angle+j*math.tau/5
        dot(d,cx+r*.47*math.cos(a),cy+r*.47*math.sin(a),6,mix(col,WHITE,.16))
    dot(d,cx,cy,17,(26,45,52))
    d.line([(cx-8,cy-8),(cx+8,cy+8)],fill=WHITE,width=3)


def static_mech():
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
    # permanent shafts and cornering curve
    for x0,x1 in ((88,332),(740,992)):
        d.line([(x0,919+11),(x1,919+11)],fill=(7,12,17),width=42)
        d.line([(x0,919),(x1,919)],fill=(109,133,147),width=34)
        d.line([(x0,910),(x1,910)],fill=(208,220,226),width=5)
    # differential body lip
    d.ellipse((275,647,805,1207),fill=(9,16,22),outline=(96,124,134),width=18)
    d.ellipse((290,665,789,1183),fill=(28,40,47),outline=(159,172,168),width=8)
    # ring gear track
    d.ellipse((305,687,777,1160),outline=(105,113,111),width=15)
    # input pinion housing & driveshaft
    d.line([(538,494),(538,629)],fill=(102,125,137),width=37)
    d.line([(529,494),(529,629)],fill=(225,231,230),width=5)
    d.rounded_rectangle((483,472,594,544),radius=19,fill=(39,54,63),outline=(129,155,164),width=5)
    fit(d,'INPUT',(490,486,590,538),23,18,GOLD,'bold',True)
    # wheel silhouettes mounted on continuous axles
    for cx in (107,981):
        d.ellipse((cx-65,847,cx+65,991),fill=(11,20,25),outline=(122,156,166),width=9)
        d.ellipse((cx-44,871,cx+44,965),outline=(78,126,142),width=6)
        dot(d,cx,919,17,(101,134,146))
    # static road path visualization below mechanical housing
    for r,col in ((280,(40,92,117)),(390,(93,75,55))):
        d.arc((545-r,1020,545+r,1650),start=12,end=168,fill=col,width=6)
    # Speed cards are drawn as camera-independent HUD so labels never crop.
    # fixed informational labels
    fit(d,'CONVENTIONAL OPEN DIFFERENTIAL',(175,408,914,476),30,24,SILVER,'bold',True)
    fit(d,'CARRIER + RING GEAR',(310,1214,773,1265),26,19,GOLD,'bold',True)
    return im
MECH_BASE=static_mech()


def mechanical_dynamic(d,t):
    delta=.38*ramp(t,12,20)
    motion=integ_turn(t)
    omega=1.35
    ring=omega*t
    left=omega*(t-.38*motion)
    right=omega*(t+.38*motion)
    spider=omega*.38*motion
    # input pinion engages ring teeth, ratio schematic not exact gear ratio
    gear(d,538,612,58,ring*2.2,SILVER,12)
    # rotating outer carrier ring, internal mechanism remains observable
    d.ellipse((296,666,784,1174),outline=(150,135,96),width=13)
    for k in range(30):
        a=ring*.32+k*math.tau/30
        x=539+243*math.cos(a);y=920+252*math.sin(a)
        dot(d,x,y,6, GOLD if k%3==0 else (159,142,108))
    # outputs: side gears rotate with different speeds without discontinuity
    gear(d,420,922,100,left,SILVER,19)
    gear(d,657,922,100,right,CYAN,19)
    # spider gears spin relative to the carrier only during turning
    gear(d,538,818,59,spider,GOLD,11)
    gear(d,538,1027,59,-spider,GOLD,11)
    # support pins center / bearing arc
    d.line([(535,855),(535,983)],fill=(78,98,108),width=15)
    d.line([(533,854),(533,982)],fill=(194,201,197),width=4)
    dot(d,538,920,17,GOLD)
    for x,ang in ((107,left),(981,right)):
        for j in range(5):
            th=ang+j*math.tau/5
            d.line([(x+16*math.cos(th),919+16*math.sin(th)),(x+43*math.cos(th),919+43*math.sin(th))],fill=CYAN if x>500 else BLUE,width=6)
    # shaft grooves rotate as visible small bands
    for x0,speed,col in ((165,1-delta,BLUE),(811,1+delta,TEAL)):
        for k in range(4):
            x=x0+((t*speed*35+k*37)%140)
            if x>990:continue
            d.line([(x,907),(x+13,934)],fill=col,width=4)
    # relative spider motion LED engages gradually, is not a second scene
    a=ramp(t,12,20)
    for k in range(12):
        ang=spider+k*math.tau/12
        r=80+11*math.sin(t*1.2+k)
        x=538+r*math.cos(ang);y=817+r*math.sin(ang)
        dot(d,x,y,2+3*a,mix((39,65,81),GOLD,a))
    # followable road position particles, outside arc has farther path
    for k in range(10):
        if t<10:break
        rad=280 if k%2==0 else 390
        a0=math.radians(12)
        a1=math.radians(168)
        s=((t-10)*(.055 if rad==280 else .083)+k/10)%1
        ang=a0+(a1-a0)*s
        x=545+rad*math.cos(ang);y=1335+315*math.sin(ang)
        if 1100<y<1455:dot(d,x,y,3.2,BLUE if rad==280 else GOLD)
    # continuity of measured speeds, no jump: ratios converge only before corner
    lratio=1-delta;rratio=1+delta
    # Readable ratios are composited after the moving camera.
    # wheel speed bars below label text
    d.line([(329,1220),(328+135*(1-delta),1220)],fill=BLUE,width=5)
    d.line([(611,1220),(611-135*(1+delta)/1.4,1220)],fill=TEAL,width=5)


# Microactions occur where the underlying physical process happens. They have
# finite start/end times and do not turn the continuous machine into slides.
def physical_microactions(d,mode,t):
    if mode=='tech':
        b.transient_chip(d,t,'AC CURRENT',(180,1068,450,1115),4.3,6.55,GOLD)
        b.transient_chip(d,t,'FIELD LINKED',(562,1055,836,1100),11.0,13.25,BLUE)
        b.transient_chip(d,t,'INDUCED AC',(741,602,1008,648),15.3,18.05,CYAN)
        b.transient_chip(d,t,'REGULATED DC',(750,871,1018,916),21.25,24.35,TEAL)
        b.transient_chip(d,t,'CHARGING',(748,1330,1013,1377),27.6,31.3,TEAL)
        # Pulses trace power into the electronics, then into the battery.
        if 15.5<t<27.5:
            pulse=gate(t,15.5,27.5,1.,1.)
            for k in range(7):
                s=((t-15.5)*.43-k*.19)%1
                x=775+214*s
                y=784+5*math.sin(2*math.pi*s+0.15*t)
                dot(d,x,y,2.3+1.5*pulse,mix(BLUE,TEAL,ramp(t,20,23)))
        if t>=22.0:
            p=ramp(t,22,23.1)
            gleam=.35+.65*math.sin(t*2.4)**2
            d.arc((795,916,999,1280),192,349,fill=(*TEAL,int(140*p*gleam)),width=5)
            d.arc((795,916,999,1280),15,153,fill=(*BLUE,int(105*p*gleam)),width=3)
        # A row of tiny flickering converters below the power management chip.
        if t>17.5:
            strength=gate(t,17.5,33.9,.7,.8)
            for j in range(4):
                x=794+j*58
                for q in range(3):
                    ya=849+q*8
                    col=mix((47,74,88),TEAL,.2+strength*(.25+.45*math.sin(t*5+j*.9+q*.2)**2))
                    d.line([(x,ya),(x+31,ya)],fill=col,width=3)
    else:
        b.transient_chip(d,t,'EQUAL SPEED',(688,545,938,590),5.0,8.5,BLUE)
        b.transient_chip(d,t,'ENTERING TURN',(687,545,945,591),11.65,14.9,GOLD)
        b.transient_chip(d,t,'SPEED SPLIT',(681,544,937,590),18.0,22.55,TEAL)
        b.transient_chip(d,t,'SPEEDS AVERAGE',(670,550,947,596),27.8,31.0,GOLD)
        # A moving trace highlights spider-gear engagement only when turning.
        activation=ramp(t,12.2,18.)
        if activation>.03:
            for j in range(15):
                a=math.tau*j/15 + t*2.9
                r=82 + 8*math.sin(j*1.5+t*.7)
                x,y=538+r*math.cos(a),813+(.57*r)*math.sin(a)
                dot(d,x,y,1.2+activation*2.6,mix((52,72,83),GOLD,activation))
            for j in range(15):
                a=math.tau*j/15 - t*2.9
                r=82+8*math.sin(j*1.5+t*.7)
                x,y=538+r*math.cos(a),1028+(.57*r)*math.sin(a)
                dot(d,x,y,1.2+activation*2.6,mix((52,72,83),BLUE,activation))
        # Speed information stays tied to the corresponding rotating wheel.
        split=ramp(t,11.5,21.0)
        if split>.05:
            for x,col,k in ((107,BLUE,0),(981,TEAL,1)):
                wave=(.5+.5*math.sin(t*3.2+k*.9))
                rr=64+10*wave
                d.arc((x-rr,919-rr,x+rr,919+rr),225,310,
                      fill=(*col,int((70+100*wave)*split)),width=5)
                th=-math.pi*.70+math.sin(t*.4+k)*.08
                arrow(d,(x+rr*math.cos(th),919+rr*math.sin(th)),th+1.5,col,6)

def camera(mode,t):
    arr=CAM[mode]
    for k in range(len(arr)-1):
        a=arr[k];bb=arr[k+1]
        if t<=bb[0]:
            u=smooth((t-a[0])/(bb[0]-a[0]))
            return tuple(a[j]*(1-u)+bb[j]*u for j in (1,2,3))
    return arr[-1][1:]

def zoom_view(im,mode,t):
    x0,y0,x1,y1=26,351,1052,1467
    vw=x1-x0;vh=y1-y0
    cx,cy,zoom=camera(mode,t)
    cw,ch=vw/zoom,vh/zoom
    xx=clamp(cx-cw/2,x0,x1-cw)
    yy=clamp(cy-ch/2,y0,y1-ch)
    patch=im.crop((int(xx),int(yy),int(xx+cw),int(yy+ch))).resize((vw,vh),Image.Resampling.BILINEAR)
    im.paste(patch,(x0,y0))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((x0,y0,x1,y1),radius=28,outline=(69,109,130),width=3)
    return im


def caption(d,mode,t):
    seq=CAPTIONS[mode]
    a0,e0,title,desc=seq[-1]
    for a,e,n,sub in seq:
        if a<=t<e:
            a0,e0,title,desc=a,e,n,sub;break
    fade=clamp(min((t-a0)/.35,(e0-t)/.3))
    color=BLUE if mode=='tech' else GOLD
    fit(d,title,(77,1567,995,1648),47,30,mix((75,84,90),color,fade),'bold')
    fit(d,desc,(80,1665,1000,1738),37,25,mix((78,84,90),WHITE,fade),'semi')
    d.line([(64,1800),(64+952*clamp(t/DUR),1800)],fill=TEAL,width=6)
    for a,_,_,_ in seq[1:]: dot(d,64+952*a/DUR,1800,5,BLUE)

def mechanics_hud(im,t):
    # Never zoom UI text with the apparatus; all speed metrics remain readable.
    d=ImageDraw.Draw(im)
    delta=.38*ramp(t,12,20)
    rbox(d,(92,1340,457,1446),(22,40,55),(59,121,159),r=18,w=3)
    rbox(d,(627,1340,993,1446),(22,44,51),(78,143,130),r=18,w=3)
    fit(d,'LEFT / INNER',(110,1349,440,1392),26,21,BLUE,'bold',True)
    fit(d,'RIGHT / OUTER',(642,1349,980,1392),26,21,TEAL,'bold',True)
    fit(d,f'{1-delta:.2f}x',(115,1391,432,1434),34,27,BLUE,'bold',True)
    fit(d,f'{1+delta:.2f}x',(649,1391,970,1434),34,27,TEAL,'bold',True)
    return im


def frame(mode,t):
    im=BASE[mode].copy().convert('RGBA')
    art=(TECH_BASE if mode=='tech' else MECH_BASE).copy()
    overlay=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(overlay)
    if mode=='tech':tech_dynamic(d,t)
    else:mechanical_dynamic(d,t)
    physical_microactions(d,mode,t)
    art.alpha_composite(overlay)
    # Strict video viewport: no animated shapes can bleed onto explanatory captions.
    x0,y0,x1,y1=26,351,1052,1467
    im.alpha_composite(art.crop((x0,y0,x1,y1)),(x0,y0))
    cd=ImageDraw.Draw(im);caption(cd,mode,t)
    out=zoom_view(im.convert('RGB'),mode,t)
    if mode=='mechanical':out=mechanics_hud(out,t)
    return out


def audio(mode,path):
    sr=48000
    tt=np.arange(int(DUR*sr),dtype=np.float32)/sr
    rng=np.random.default_rng(121 if mode=='tech' else 122)
    noise=rng.normal(0,.002,len(tt)).astype(np.float32)
    if mode=='tech':
        out=.012*np.sin(math.tau*120*tt)+.012*np.sin(math.tau*224*tt)+noise
    else:
        rpm=74+8*np.sin(tt*.20)
        out=.023*np.sin(math.tau*rpm*tt)+.012*np.sin(math.tau*2*rpm*tt)+noise
        # subtle gear teeth rhythm synced to visible carrier rotation
        for ti in np.arange(1.5,DUR-.5,.42):
            s=int(ti*sr);n=min(int(.07*sr),len(tt)-s)
            u=np.arange(n,dtype=np.float32)/sr
            out[s:s+n]+=.028*np.sin(math.tau*(650-190*u)*u)*np.exp(-u*75)
    def fx(at,duration,freq,amp=.08):
        s=int(at*sr);n=min(int(duration*sr),len(tt)-s)
        if n<=0:return
        u=np.arange(n,dtype=np.float32)/sr
        out[s:s+n]+=amp*np.sin(math.tau*(freq+120*u)*u)*np.exp(-u*19)
    if mode=='tech':
        for ti,fq in ((3.8,470),(4.3,610),(9.0,590),(11.0,720),(14.7,780),(15.3,900),(20.5,650),(21.25,830),(27.1,840),(27.6,1000),(32.3,520)):
            fx(ti,.31,fq,.075)
        # quiet induction hum, rising with active field
        out+=.014*np.sin(math.tau*310*tt)*np.clip((tt-5)/2,0,1)
        for t in np.arange(22,32,.65):fx(t,.12,970,.024)
    else:
        for ti,fq in ((4.0,490),(5.0,530),(10.0,620),(11.65,690),(15.8,710),(18.0,940),(24,850),(27.8,760),(29,550)):
            fx(ti,.23,fq,.064)
    out*=np.minimum(1,tt/.5)*np.minimum(1,(DUR-tt)/.6)
    out=np.clip(out,-.9,.9)
    with wave.open(path,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr)
        w.writeframes((out*32767).astype(np.int16).tobytes())


def render(mode,path,aud):
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',aud,'-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-map','0:v','-map','1:a','-t',str(DUR),'-movflags','+faststart',path]
    ff=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    start=time.time()
    try:
        for i in range(int(DUR*FPS)):
            ff.stdin.write(np.asarray(frame(mode,i/FPS),dtype=np.uint8).tobytes())
            if i%216==0:print('RENDER',mode,i,'/',int(DUR*FPS),'elapsed',round(time.time()-start,1),flush=True)
        ff.stdin.close();ff.stdin=None
        err=ff.communicate()[1]
        if ff.returncode:raise RuntimeError(err.decode()[-2000:])
    except BaseException:
        ff.kill();raise
    print('DONE',mode,os.path.getsize(path),round(time.time()-start,1),flush=True)

def storyboard(mode,p):
    times=[1,4.7,8.5,12.3,16.7,21.8,26.0,30.0,34.5]
    im=Image.new('RGB',(864,1536),(8,17,27))
    for i,t in enumerate(times):
        view=frame(mode,t).resize((288,512),Image.Resampling.LANCZOS)
        im.paste(view,((i%3)*288,(i//3)*512))
    im.save(p,quality=93)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['tech','mechanical','all'],default='all');p.add_argument('--preview',action='store_true');a=p.parse_args()
    for mode in (('tech','mechanical') if a.mode=='all' else (a.mode,)):
        sn='Technology_Wireless_Charging' if mode=='tech' else 'Mechanics_Open_Differential'
        story=f'{P}/EGI_V12_{sn}_Microanimations_Storyboard.jpg'
        storyboard(mode,story)
        if not a.preview:
            aud=f'{P}/EGI_V12_{mode}_SFX.wav';audio(mode,aud)
            render(mode,f'{P}/EGI_V12_{sn}_Microanimations.mp4',aud)