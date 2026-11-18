#!/usr/bin/env python3
"""EGI V12: a single continuous 2.5D scene showing URL->DNS->TLS->HTTP->render.
Original procedural visuals and precisely timed original synthesized keyboard / interface sounds.
Schematic representation, not a packet capture. No cuts, no scene reset.
"""
import os, math, bisect, wave, subprocess, argparse, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W,H,FPS=1080,1920,24
DUR=36.0
N=int(DUR*FPS)
ROOT=os.environ.get('EGI_OUTPUT_DIR','/mnt/data')
FONT_DIR=os.environ.get('EGI_FONT_DIR','/usr/share/fonts/opentype/inter/')
if not os.path.isfile(os.path.join(FONT_DIR,'Inter-Regular.otf')):
    FONT_DIR='/usr/share/fonts/truetype/dejavu/'
if os.path.isfile(os.path.join(FONT_DIR,'Inter-Regular.otf')):
    FACE=FONT_DIR+'Inter-Regular.otf'; SEMI=FONT_DIR+'Inter-SemiBold.otf'; BOLD=FONT_DIR+'Inter-Bold.otf'
else:
    FACE=FONT_DIR+'DejaVuSans.ttf'; SEMI=FONT_DIR+'DejaVuSans.ttf'; BOLD=FONT_DIR+'DejaVuSans-Bold.ttf'

NAVY=(7,17,28); PANEL=(21,37,51); PANEL2=(27,46,58)
WHITE=(237,246,252); GRAY=(145,168,183); BLUE=(72,203,252); CYAN=(127,238,255); GOLD=(255,192,103); TEAL=(77,230,179); CORAL=(255,119,101); SILVER=(147,174,192)

FF={}
def f(sz,kind='regular'):
    key=(sz,kind)
    if key not in FF:FF[key]=ImageFont.truetype({'regular':FACE,'semi':SEMI,'bold':BOLD}[kind],sz)
    return FF[key]
def clamp(x,a=0.,b=1.):return max(a,min(b,x))
def smooth(x): x=clamp(x);return x*x*(3-2*x)
def ramp(t,st,ed):return smooth((t-st)/(ed-st))
def gate(t,st,ed,fi=.5,fo=.65):return ramp(t,st,st+fi)*(1-ramp(t,ed-fo,ed))
def mix(a,b,v):return tuple(int(a[i]*(1-v)+b[i]*v) for i in range(3))
def txt(d,txt,x,y,sz=28,c=WHITE,k='regular'):
    d.text((x,y),txt,font=f(sz,k),fill=c)
def center(d,txt,cx,y,sz=29,c=WHITE,k='semi'):
    bb=d.textbbox((0,0),txt,font=f(sz,k));d.text((cx-(bb[2]-bb[0])/2,y),txt,font=f(sz,k),fill=c)
def fit(d,text,box,sz=32,minimum=18,c=WHITE,k='semi',centered=False):
    x0,y0,x1,y1=box
    for s in range(sz,minimum-1,-1):
        bb=d.textbbox((0,0),text,font=f(s,k))
        if bb[2]-bb[0]<=x1-x0-8 and bb[3]-bb[1]<=y1-y0-8:
            x=(x0+x1-(bb[2]-bb[0]))/2-bb[0] if centered else x0-bb[0]
            y=(y0+y1-(bb[3]-bb[1]))/2-bb[1]
            d.text((round(x),round(y)),text,font=f(s,k),fill=c)
            return s
    raise ValueError('TEXT_OVERFLOW '+text+' '+str(box))
def dot(d,x,y,r,c): d.ellipse((x-r,y-r,x+r,y+r),fill=c)
def rbox(d,box,fill,border=(77,119,144),r=22,w=3):
    d.rounded_rectangle(box,radius=r,fill=fill,outline=border,width=w)
    x0,y0,x1,y1=box
    d.line([(x0+r,y0+5),(x1-r,y0+5)],fill=mix(border,WHITE,.14),width=2)
def arrow(d,at,ang,c,sz=11):
    x,y=at
    d.polygon([(x+sz*math.cos(ang),y+sz*math.sin(ang)),(x+sz*math.cos(ang+2.55),y+sz*math.sin(ang+2.55)),(x+sz*math.cos(ang-2.55),y+sz*math.sin(ang-2.55))],fill=c)

# consistent scene geometry
BROWSER=(64,572,574,1192)
DNS=(715,538,1025,747)
SERVER=(711,815,1029,1212)
KEYBOARD=(105,1265,613,1427)

# pathway geometry: all tracks exist all the time, activity is gradual and directional
PATHS={
'dns_up':[(561,689),(647,644),(728,644)],
'dns_down':[(728,704),(653,761),(574,788)],
'tls_up':[(571,882),(644,869),(724,908)],
'tls_down':[(726,959),(649,983),(574,963)],
'get':[(570,1021),(637,1038),(723,1043)],
'response':[(724,1113),(643,1145),(571,1135)],
'resources':[(729,1176),(661,1225),(565,1171)]
}

def prep(path):
    arr=[0.]
    for a,b in zip(path,path[1:]):arr.append(arr[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
    return (path,arr,arr[-1])
PATH_DATA={name:prep(points) for name,points in PATHS.items()}
def path_xy(info,s):
    pts,arc,L=info;s=clamp(s,0,L)
    i=max(1,min(len(arc)-1,bisect.bisect_left(arc,s)))
    v=(s-arc[i-1])/(arc[i]-arc[i-1] or 1)
    return (pts[i-1][0]+(pts[i][0]-pts[i-1][0])*v, pts[i-1][1]+(pts[i][1]-pts[i-1][1])*v)

def path_particles(d,name,t,col,start,end,rate=10,speed=1.0,r=4.8):
    info=PATH_DATA[name]
    activity=gate(t,start,end,fi=.35,fo=.6)
    width=max(.12,activity)
    pts=info[0]
    linecolor=mix((27,59,76),col, .15+.55*activity)
    d.line(pts,fill=linecolor,width=4,joint='curve')
    if activity<.035:return
    speed=130*speed
    # fixed-timing emission: particles are born near start and exit end, not teleported
    for i in range(23):
        age=t-start - i/(rate)
        if age<0:continue
        travel=age*speed
        if travel>info[2]:continue
        x,y=path_xy(info,travel)
        rr=r*(.85+.15*math.sin(t*5+i))
        dot(d,x,y,rr,mix(col,(230,251,255),i%5==0 and .35 or .0))
        if i%4==0:
            x2,y2=path_xy(info,max(0,travel-16))
            d.line([(x2,y2),(x,y)],fill=mix((38,75,95),col,.65),width=4)
    # gentle directional streaks cycling only once journey established
    for p in (0.33,.70):
        if t<start+info[2]/speed:continue
        shift=((t-start)*.28+p)%1
        x,y=path_xy(info,shift*info[2]);x2,y2=path_xy(info,min((shift+.04)*info[2],info[2]))
        angle=math.atan2(y2-y,x2-x)
        arrow(d,(x,y),angle,mix(linecolor,col,.7),8)


def background():
    y=np.arange(H,dtype=np.float32)[:,None];x=np.arange(W,dtype=np.float32)[None,:]
    ambient=np.maximum(0,1-((x-535)/805)**2-((y-950)/1070)**2)
    arr=np.zeros((H,W,3),dtype=np.uint8)
    for ch,n in enumerate(NAVY):arr[:,:,ch]=np.clip(n+ambient*(15 if ch==2 else 8)+y/H*(8 if ch==2 else 2),0,255)
    im=Image.fromarray(arr,'RGB');d=ImageDraw.Draw(im)
    for x in range(53,1050,82):d.line([(x,365),(x,1470)],fill=(21,43,58),width=1)
    for y in range(373,1490,82):d.line([(30,y),(1053,y)],fill=(21,43,58),width=1)
    d.rounded_rectangle((26,351,1052,1467),radius=30,outline=(51,87,110),width=3)
    d.line([(54,118),(1028,118)],fill=(64,109,132),width=2)
    d.line([(54,331),(1028,331)],fill=(64,109,132),width=2)
    fit(d,'EGI',(55,47,195,111),66,50,WHITE,'bold')
    fit(d,'SOFTWARE / 01',(225,57,550,100),26,22,BLUE,'semi')
    fit(d,'ONE CONTINUOUS PROCESS',(630,60,1028,97),23,20,GRAY,'semi',True)
    fit(d,'WHAT HAPPENS WHEN',(55,153,1020,221),56,48,WHITE,'bold')
    fit(d,'YOU TYPE A URL?',(55,222,1020,292),67,48,WHITE,'bold')
    # caption card
    rbox(d,(43,1510,1037,1774),(26,30,35),(81,75,68),r=28,w=3)
    d.line([(80,1559),(998,1559)],fill=(90,79,66),width=2)
    d.line([(61,1800),(1019,1800)],fill=(77,85,89),width=2)
    d.line([(61,1858),(1019,1858)],fill=(62,78,91),width=2)
    fit(d,'Curiosity in Motion',(58,1874,495,1916),26,20,GRAY)
    fit(d,'Ekrem Gökberk İşcan',(714,1874,1020,1916),26,20,SILVER)
    return im
BG=background()

# pre-cached physical device frame

def casing():
    layer=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(layer)
    # browser shadow and screen glass
    bx0,by0,bx1,by1=BROWSER
    rbox(d,(bx0+9,by0+14,bx1+13,by1+14),(7,12,18),(36,63,82),r=29,w=3)
    rbox(d,BROWSER,(28,50,66),(127,165,186),r=30,w=6)
    d.rounded_rectangle((bx0+13,by0+15,bx1-13,by0+87),radius=22,fill=(36,60,75))
    for k,c in enumerate((CORAL,GOLD,TEAL)):dot(d,bx0+42+k*30,by0+46,8,c)
    rbox(d,(bx0+145,by0+29,bx1-20,by0+74),(15,32,45),(66,119,149),r=10,w=2)
    d.rounded_rectangle((bx0+22,by0+100,bx1-22,by1-23),radius=14,fill=(10,24,34))
    # desktop windows etched edges, later rendered inside
    for xx in (92,537):d.line([(xx,701),(xx,1136)],fill=(40,65,80),width=2)
    # DNS compact resolver
    dx0,dy0,dx1,dy1=DNS
    rbox(d,(dx0+9,dy0+12,dx1+9,dy1+12),(8,14,20),(36,61,74),r=25,w=3)
    rbox(d,DNS,(28,48,59),(92,138,160),r=24,w=4)
    fit(d,'DNS RESOLVER',(dx0+17,dy0+15,dx1-15,dy0+63),27,23,WHITE,'bold',True)
    d.line([(dx0+22,dy0+66),(dx1-22,dy0+66)],fill=(75,110,122),width=2)
    # server hardware rack
    sx0,sy0,sx1,sy1=SERVER
    rbox(d,(sx0+8,sy0+11,sx1+10,sy1+13),(6,11,17),(34,57,70),r=29,w=3)
    rbox(d,SERVER,(41,56,65),(126,146,153),r=28,w=6)
    fit(d,'WEB SERVER',(sx0+18,sy0+14,sx1-19,sy0+64),31,24,WHITE,'bold',True)
    for k in range(4):
        y=892+k*72
        rbox(d,(731,y,1007,y+55),(19,35,46),(86,110,122),r=12,w=2)
        d.line([(753,y+12),(846,y+12)],fill=(115,136,148),width=4)
        d.line([(753,y+25),(836,y+25)],fill=(65,97,117),width=3)
        d.ellipse((934,y+15,964,y+45),outline=(104,148,160),width=4)
    # small keyboard with metallic keys; 3 rows, one Enter key
    kx0,ky0,kx1,ky1=KEYBOARD
    rbox(d,(kx0+6,ky0+8,kx1+10,ky1+13),(9,13,20),(48,68,78),r=24,w=3)
    rbox(d,KEYBOARD,(38,48,56),(113,130,139),r=24,w=5)
    for row in range(3):
        for col in range(10 if row<2 else 8):
            x=127+col*43 + (row==1 and 16 or 0)
            y=1281+row*45
            rbox(d,(x,y,x+34,y+31),(48,65,75),(103,129,138),r=6,w=1)
    rbox(d,(495,1323,586,1400),(52,78,84),(126,158,163),r=8,w=2)
    fit(d,'ENTER',(499,1343,582,1372),22,17,WHITE,'semi',True)
    # permanent travel tracks
    for path in PATHS.values():d.line(path,fill=(33,70,88),width=3,joint='curve')
    # framed faint labels by function not disappearing at stages
    fit(d,'CLIENT',(122,493,358,541),29,23,BLUE,'bold')
    fit(d,'THE NETWORK',(582,483,718,524),21,17,GRAY,'semi')
    fit(d,'INPUT',(118,1434,315,1463),21,16,SILVER,'semi')
    return layer
CASING=casing()

URL='https://example.com'
TYPING_START=.65
KEY_INTERVAL=.154
KEY_TIMES=[TYPING_START+k*KEY_INTERVAL for k in range(len(URL))]
ENTER_TIME=3.85


def type_overlay(d,t):
    chars=int(clamp((t-TYPING_START)/KEY_INTERVAL+1,0,len(URL)))
    content=URL[:chars]
    fit(d,content,(BROWSER[0]+221,BROWSER[1]+36,BROWSER[2]-28,BROWSER[1]+68),23,15,WHITE)
    if t<ENTER_TIME and int(t*2.4)%2:
        b=d.textbbox((0,0),content,font=f(20))
        cx=min(BROWSER[2]-45,BROWSER[0]+219 + b[2]-b[0])
        d.line([(cx,BROWSER[1]+39),(cx,BROWSER[1]+65)],fill=BLUE,width=2)
    # keys light up at exact corresponding moments
    for k,kt in enumerate(KEY_TIMES):
        age=t-kt
        if 0<=age<.17:
            row=k%3;col=(k*7)%9
            x=127+col*43+(16 if row==1 else 0)
            y=1281+row*45
            d.rounded_rectangle((x,y+3,x+34,y+27),radius=5,fill=mix((48,65,75),BLUE,(1-age/.17)*.9),outline=CYAN,width=2)
    if ENTER_TIME<=t<ENTER_TIME+.32:
        d.rounded_rectangle((500,1327,580,1396),radius=7,fill=mix((52,78,84),TEAL,1-(t-ENTER_TIME)/.32),outline=CYAN,width=3)
        dot(d,557,685,19,TEAL)


def globe(d,t,activity):
    cx,cy=871,683
    c=mix((48,79,98),CYAN,activity)
    d.ellipse((cx-39,cy-39,cx+39,cy+39),outline=c,width=3)
    d.arc((cx-22,cy-39,cx+22,cy+39),0,360,fill=c,width=2)
    d.line([(cx-38,cy),(cx+38,cy)],fill=c,width=2)
    for k in range(6):
        theta=t*.7+k*math.tau/6
        x=cx+31*math.cos(theta);y=cy+19*math.sin(theta)
        dot(d,x,y,4,TEAL if activity>.3 else SILVER)
    fit(d,'EXAMPLE.COM',(731,607,1018,651),23,19,mix(GRAY,CYAN,activity),'semi',True)
    if t>5.1:
        op=ramp(t,5.2,5.9)
        if op>.02:fit(d,'203.0.113.10',(740,710,1002,739),24,17,mix((42,65,73),TEAL,op),'semi',True)


def server_leds(d,t,activity):
    for k in range(4):
        y=892+k*72
        blink=(math.sin(t*(4.8+k*.3)+k*1.5)>-.1)
        col=mix((42,77,84),TEAL if blink else BLUE,.17+activity*.83)
        dot(d,984,y+30,5,col)
    # cooling fans spin (machinery inside computer server)
    x,y=946,1140
    for j in range(6):
        a=t*3.3+j*math.tau/6
        d.line([(x+6*math.cos(a),y+6*math.sin(a)),(x+19*math.cos(a),y+19*math.sin(a))],fill=mix(SILVER,CYAN,activity),width=3)
    dot(d,x,y,5,SILVER)


# Text fragments are sampled once and move causally into the next visual cue.
# The keyframed text particles are deterministic for every output frame.
def _text_fragments(word,sz=23):
    import random
    font=f(sz,'bold')
    im=Image.new('L',(220,49),0)
    draw=ImageDraw.Draw(im)
    bb=draw.textbbox((0,0),word,font=font)
    draw.text(((220-(bb[2]-bb[0]))/2,4),word,font=font,fill=255)
    arr=np.asarray(im)
    pts=[]
    for yy in range(0,49,2):
        for xx in range(0,220,2):
            if arr[yy,xx]>125:pts.append((xx-110,yy-24))
    random.Random(66).shuffle(pts)
    return pts[:125]

SECURE_PARTICLES=_text_fragments('SECURE')

def micro_word(d,t,word,cx,cy,start,settle,disperse,end,col,seed=0):
    # One meaningful action: a word emerges and becomes tiny directional fragments.
    if t<start or t>=end:return
    grow=ramp(t,start,settle)
    gone=ramp(t,disperse,end)
    alpha=int(225*grow*(1-gone))
    if alpha>2:
        width=174; left=cx-width/2; top=cy-25-(1-grow)*16
        d.rounded_rectangle((left,top,left+width,top+49),radius=13,
            fill=(16,40,49,int(alpha*.62)),outline=(*col,int(alpha*.70)),width=2)
        label_font=f(23,'bold')
        bb=d.textbbox((0,0),word,font=label_font)
        d.text((cx-(bb[2]-bb[0])/2,cy-(bb[3]-bb[1])/2-bb[1]-(1-grow)*16),word,font=label_font,fill=(*WHITE,alpha))
    # Type mask splits into a drift cloud. Each spark has a persistent ID/trajectory.
    if gone>.01:
        for j,(x,y) in enumerate(SECURE_PARTICLES):
            a=j*2.39996323
            fuzz=8+16*((j%13)/13)
            q=smooth(gone)
            # A short cloud blooms away from the text, then converges toward the lock.
            tx=cx+x + math.cos(a)*fuzz*q + 26*q*math.cos(a*.55)
            ty=cy+y+12*q+math.sin(a)*fuzz*q+38*q*q
            opacity=int(215*(1-q)**1.3)
            if opacity<6:continue
            rr=1.4+1.3*((j%6)/6)
            d.ellipse((tx-rr,ty-rr,tx+rr,ty+rr),fill=(*col,opacity))

def transient_chip(d,t,label,box,start,end,col):
    a=gate(t,start,end,fi=.30,fo=.50)
    if a<.02:return
    x0,y0,x1,y1=box
    lift=(1-smooth((t-start)/.5))*11
    d.rounded_rectangle((x0,y0+lift,x1,y1+lift),radius=11,
        fill=(16,34,43,int(170*a)),outline=(*col,int(175*a)),width=2)
    for sz in range(20,15,-1):
        bb=d.textbbox((0,0),label,font=f(sz,'semi'))
        if bb[2]-bb[0]<(x1-x0-14):break
    d.text(((x0+x1-(bb[2]-bb[0]))/2,(y0+y1-(bb[3]-bb[1]))/2-bb[1]+lift),
        label,font=f(sz,'semi'),fill=(*WHITE,int(230*a)))


def lock(d,t,activity):
    x,y=646,939
    strength=clamp(activity)
    verified=ramp(t,10.65,11.25)
    c=mix(mix((44,69,83),GOLD,strength),TEAL,verified)
    d.arc((x-20,y-38,x+20,y+13),190,350,fill=c,width=6)
    rbox(d,(x-27,y-9,x+27,y+43),(21,43,54),c,r=8,w=4)
    dot(d,x,y+13,5,c)
    d.line([(x,y+17),(x,y+30)],fill=c,width=4)
    if verified>.05:
        # Validation turns the lock green but never removes it; TLS state persists.
        d.arc((x-37,y-48,x+37,y+53),195,356,
              fill=(*TEAL,int(140*verified*(.7+.3*math.sin(t*2)**2))),width=3)
        if verified>.75:
            d.line([(x+17,y+22),(x+22,y+28),(x+32,y+14)],fill=(*TEAL,int(190*verified)),width=4)
    if t>10.4:
        p=ramp(t,10.5,11.5)
        for j in range(7):
            z=math.pi*2*j/7+t*.3
            xx=x+40*math.cos(z);yy=y+50*math.sin(z)
            dot(d,xx,yy,2.5,mix((31,59,74),TEAL,p))


def render_page(d,t):
    bx0,by0,bx1,by1=BROWSER
    x0,y0,x1,y1=bx0+33,by0+110,bx1-33,by1-34
    # skeleton to dynamic assembled page
    load=ramp(t,20.9,25.1)
    paint=ramp(t,25.0,28.0)
    if load<.01:
        for j in range(5):
            y=737+j*73;w=320 if j%2==0 else 235
            d.rounded_rectangle((x0+19,y,x0+19+w,y+15),radius=8,fill=(28,52,65))
        return
    d.rounded_rectangle((x0,y0,x1,y1),radius=14,fill=mix((14,29,40),(232,243,248),paint*.88))
    # toolbar skeleton -> colored header
    col=mix((40,77,93),(26,79,111),paint)
    d.rounded_rectangle((x0+12,y0+18,x1-12,y0+93),radius=13,fill=col)
    fit(d,'EXPLORE / IDEAS',(x0+31,y0+34,x1-26,y0+80),27,21,WHITE,'bold')
    # cards appear by progressive DOM construction; fade painted layers
    for j in range(3):
        if load>j*.24:
            amp=ramp(load,j*.24,j*.24+.20)
            xx=x0+20+j*134
            yy=y0+130
            h=95*amp
            c=mix((30,71,89),(40+int(j*28),123+int(j*10),154),paint)
            d.rounded_rectangle((xx,yy,xx+119,yy+h),radius=11,fill=c,outline=mix((48,83,101),CYAN,paint),width=2)
            if paint>.1:
                for b in range(4):
                    w=12;bh=(b+2)*8 + 12*math.sin(j+t*.8+b*.4)**2
                    d.rectangle((xx+15+b*23,yy+70-bh,xx+15+b*23+w,yy+70),fill=mix(BLUE,TEAL,b/4))
    for j in range(4):
        if load> .4+j*.10:
            y=y0+263+j*47
            width=365-j*38
            d.rounded_rectangle((x0+24,y,x0+24+width,y+13),radius=6,fill=mix((43,78,95),(94,126,142),paint))
    # mouse pointer moves after render and initiates subtle scroll
    if t>27.5:
        px=x0+310+90*math.sin(t*.5);py=y0+295+46*math.sin(t*.8)
        d.polygon([(px,py),(px,py+24),(px+9,py+18),(px+19,py+29),(px+26,py+25),(px+16,py+15),(px+26,py+12)],fill=WHITE,outline=(32,65,81))


def data_files(d,t):
    if t<18.2:return
    for j,(label,col) in enumerate((('HTML',GOLD),('CSS',BLUE),('JS',TEAL))):
        age=t-(18.4+j*.55)
        if age<0:return
        length=PATH_DATA['resources'][2]
        p=clamp(age*54/length)
        x,y=path_xy(PATH_DATA['resources'],p*length)
        if p<1:
            d.rounded_rectangle((x-31,y-17,x+31,y+17),radius=9,fill=mix((29,50,66),col,.28),outline=col,width=2)
            fit(d,label,(x-29,y-14,x+29,y+14),16,12,WHITE,'bold',True)


CAPTIONS=[
    (0.,4.0,'01   TYPE THE ADDRESS','A browser begins with a URL.'),
    (4.0,8.2,'02   FIND THE IP ADDRESS','DNS resolves the domain to an address.'),
    (8.2,12.0,'03   MAKE A SECURE CONNECTION','A handshake establishes an encrypted session.'),
    (12.0,17.6,'04   SEND THE HTTP REQUEST','The browser requests a resource from the server.'),
    (17.6,23.5,'05   RETURN THE RESPONSE','The server sends back HTML and related resources.'),
    (23.5,30.3,'06   BUILD THE PAGE','HTML, styles and scripts become visible pixels.'),
    (30.3,36.0,'THE ENTIRE JOURNEY','URL → DNS → TLS → HTTP → render.')
]

def active_caption(t):
    for start,end,title,desc in CAPTIONS:
        if start<=t<end:return start,end,title,desc
    return CAPTIONS[-1]

def caption_draw(d,t):
    start,end,heading,sub=active_caption(t)
    fade=clamp(min((t-start)/.35,(end-t)/.30))
    fit(d,heading,(77,1567,994,1648),47,33,mix((75,84,90),BLUE,fade),'bold')
    fit(d,sub,(80,1665,1000,1738),37,26,mix((78,84,90),WHITE,fade),'semi')
    d.line([(64,1800),(64+952*clamp(t/DUR),1800)],fill=TEAL,width=6)
    for tt in (4,8.2,12,17.6,23.5,30.3):
        x=64+952*tt/DUR
        dot(d,x,1800,5,BLUE)


# A single virtual camera tracks the causally connected process. No slide cuts.
CAMERA_KEYFRAMES=[
    (0.,540.,909.,1.00),
    (1.2,348.,975.,1.17),
    (3.65,348.,975.,1.17),
    (5.1,732.,696.,1.31),
    (7.45,745.,690.,1.29),
    (9.8,637.,923.,1.20),
    (11.7,647.,942.,1.20),
    (14.5,727.,995.,1.22),
    (17.6,721.,993.,1.19),
    (21.0,652.,1048.,1.20),
    (25.5,327.,903.,1.28),
    (29.5,327.,903.,1.27),
    (33.8,540.,909.,1.00),
    (36.0,540.,909.,1.00),
]

def camera_params(t):
    for k in range(len(CAMERA_KEYFRAMES)-1):
        a=CAMERA_KEYFRAMES[k];b=CAMERA_KEYFRAMES[k+1]
        if t<=b[0]:
            u=smooth((t-a[0])/(b[0]-a[0]))
            return tuple(a[j]*(1-u)+b[j]*u for j in (1,2,3))
    return CAMERA_KEYFRAMES[-1][1:]

def focus_view(im,t):
    zx0,zy0,zx1,zy1=26,351,1052,1467
    vw,vh=zx1-zx0,zy1-zy0
    cx,cy,zoom=camera_params(t)
    cw,ch=vw/zoom,vh/zoom
    x0=clamp(cx-cw/2,zx0,zx1-cw)
    y0=clamp(cy-ch/2,zy0,zy1-ch)
    patch=im.crop((int(x0),int(y0),int(x0+cw),int(y0+ch)))
    # fast and smooth, small amount of sharpened detail preserved by linear filter
    patch=patch.resize((vw,vh),Image.Resampling.BILINEAR)
    im.paste(patch,(zx0,zy0))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((zx0,zy0,zx1,zy1),radius=28,outline=(69,109,130),width=3)
    return im

def frame(t):
    canvas=BG.copy().convert('RGBA')
    canvas.alpha_composite(CASING)
    L=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(L)
    # live browser that persists throughout the single animation
    type_overlay(d,t)
    dns_act=gate(t,4.0,8.2,.3,.5)
    tls_act=gate(t,8.2,13.,.3,.7)
    http_act=gate(t,12.,18.5,.35,.6)
    response_act=gate(t,17.5,25.0,.35,.8)
    render_page(d,t)
    globe(d,t,dns_act)
    lock(d,t,ramp(t,8.2,11.8))
    # Security badge grows from the handshake, resolves into a fine particle cloud;
    # the validated lock remains in place throughout later HTTP and render events.
    micro_word(d,t,'SECURE',638,787,10.10,10.48,11.40,12.54,TEAL)
    transient_chip(d,t,'IP FOUND',(757,762,996,807),6.40,8.18,BLUE)
    transient_chip(d,t,'HTTP 200',(785,1234,999,1277),20.15,22.85,TEAL)
    transient_chip(d,t,'PAGE READY',(332,1142,545,1183),29.65,32.25,GOLD)
    server_leds(d,t,clamp(http_act+response_act))
    # request and response loops are separate; data continues inside each path
    path_particles(d,'dns_up',t,GOLD,4.00,6.9,rate=17,speed=.9)
    path_particles(d,'dns_down',t,TEAL,5.45,8.15,rate=17,speed=.9)
    path_particles(d,'tls_up',t,BLUE,8.25,10.5,rate=15,speed=.95)
    path_particles(d,'tls_down',t,GOLD,9.4,12.2,rate=15,speed=.95)
    path_particles(d,'get',t,TEAL,12.0,17.1,rate=13,speed=1.)
    path_particles(d,'response',t,CYAN,17.5,23.6,rate=12,speed=1.)
    path_particles(d,'resources',t,GOLD,18.3,26.2,rate=12,speed=.8)
    data_files(d,t)
    # synced activity meter behind keyboard
    for k in range(26):
        x=670+k*14;y=1310
        p=(t*.8+k*.21)
        height=(12+14*math.sin(p)**2)*(1. if t>=4 else .5)
        d.line([(x,y-height),(x,y+6)],fill=mix((45,72,91),BLUE,.25+.6*math.sin(p+.5)**2),width=5)
    fit(d,'LINK ACTIVITY',(676,1337,1042,1385),22,19,GRAY,'semi')
    # recap halo that re-energizes connected paths
    if t>30.4:
        g=ramp(t,30.4,32.5)*.22
        for route,col in (('dns_up',GOLD),('dns_down',TEAL),('get',BLUE),('response',CYAN)):
            p=PATHS[route]
            d.line(p,fill=mix((30,59,77),col,g),width=5,joint='curve')
    caption_draw(d,t)
    canvas.alpha_composite(L)
    return focus_view(canvas.convert('RGB'),t)

# Original synthesised diegetic SFX. Event timing exactly matches typing animation.
def sound(path):
    sr=48000; rng=np.random.default_rng(261)
    samples=int(DUR*sr); tt=np.arange(samples,dtype=np.float32)/sr
    # low, restrained room ambience
    out=(.011*np.sin(math.tau*78*tt)+.008*np.sin(math.tau*143*tt)).astype(np.float32)
    out+=rng.normal(0,.0018,samples).astype(np.float32)
    def burst(at,duration,func):
        start=max(0,int(at*sr));n=min(int(duration*sr),samples-start)
        if n<=0:return
        t0=np.arange(n,dtype=np.float32)/sr
        out[start:start+n]+=func(t0).astype(np.float32)
    # tactile two-part clicks, varied subtly per character (keyboard visible at same moment)
    for i,t in enumerate(KEY_TIMES):
        vib=0.72+0.24*((i*7)%5)/5
        burst(t,.075,lambda u,vib=vib: .13*vib*np.sin(math.tau*(930-120*u)*u)*np.exp(-u*104)+.050*vib*np.sin(math.tau*132*u)*np.exp(-u*80))
        burst(t+.048,.032,lambda u: .024*np.sin(math.tau*1600*u)*np.exp(-u*185))
    # distinctive Enter key travel and digital confirmation
    burst(ENTER_TIME,.23,lambda u:.19*np.sin(math.tau*540*u)*np.exp(-u*24)+.10*np.sin(math.tau*130*u)*np.exp(-u*30))
    # Precisely synchronized micro-interaction cues: badge, dissolve, response, page.
    for ti,fq in ((6.40,1040),(10.10,960),(10.48,1280),(11.40,1480),(20.15,1180),(29.65,1050)):
        burst(ti,.16,lambda u,fq=fq:.030*np.sin(math.tau*(fq+180*u)*u)*np.exp(-u*23))
    # a brief airy release timed to the SECURE word dissolving, not continuous noise
    burst(11.40,.50,lambda u:.012*np.sin(math.tau*(1400-550*u)*u)*np.exp(-u*6))
    # contextual packet chirps at actual on-screen steps
    for ti,freq in [(4.08,740),(5.5,950),(8.3,500),(9.4,710),(10.6,920),(12.15,620),(17.7,470),(18.4,830),(19.0,890),(20.1,780),(23.6,600),(25.8,820),(30.4,450)]:
        burst(ti,.24,lambda u,freq=freq:.052*np.sin(math.tau*(freq+270*u)*u)*np.exp(-u*16))
    # gently rising processing texture when server is active
    mask=np.clip((tt-12)/1.2,0,1)*np.clip((24-tt)/2,0,1)
    out+=.014*mask*np.sin(math.tau*(181+4*np.sin(tt*1.5))*tt)
    # soft crossfade onset/end
    out*=np.minimum(1,tt/.3)*np.minimum(1,(DUR-tt)/.6)
    out=np.clip(out,-.89,.89)
    with wave.open(path,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr)
        w.writeframes((out*32767).astype(np.int16).tobytes())


def render(path,audio,seconds=None):
    limit=N if seconds is None else int(seconds*FPS)
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',audio,'-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-map','0:v','-map','1:a','-t',str(limit/FPS),'-movflags','+faststart',path]
    ff=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    t0=time.time()
    try:
        for i in range(limit):
            ff.stdin.write(np.asarray(frame(i/FPS),dtype=np.uint8).tobytes())
            if not i%144:print('FRAME',i,'/',limit,'elapsed',round(time.time()-t0,1),flush=True)
        ff.stdin.close();ff.stdin=None
        err=ff.communicate()[1]
        if ff.returncode:raise RuntimeError(err.decode()[-2000:])
    except BaseException:
        ff.kill();raise
    print('OK',path,os.path.getsize(path),round(time.time()-t0,1),flush=True)

def sheet(path):
    times=[1.7,4.6,7.1,10.8,14.0,18.9,22.4,26.6,32.0]
    out=Image.new('RGB',(864,1536),(8,17,27))
    for i,t in enumerate(times):
        im=frame(t).resize((288,512),Image.Resampling.LANCZOS)
        out.paste(im,((i%3)*288,(i//3)*512))
    out.save(path,quality=91)
    for t in (1.7,10.8,26.6):
        frame(t).save(path.replace('Storyboard.jpg',f'{t:.1f}s.jpg'),quality=90)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--preview',action='store_true');a.add_argument('--seconds',type=float);args=a.parse_args()
    sheet(ROOT+'/EGI_V12_Software_Connected_Storyboard.jpg')
    if not args.preview:
        audio=ROOT+'/EGI_V12_Software_Original_SFX.wav';sound(audio)
        render(ROOT+'/EGI_V12_Software_Connected_Microanimations.mp4',audio,args.seconds)