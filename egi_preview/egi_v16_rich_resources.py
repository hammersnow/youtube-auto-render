#!/usr/bin/env python3
"""EGI V16: detailed named HTML / CSS / JavaScript resource handoff.

The original V12 physical/camera animations are drawn from SOURCE. Built-in V12
callouts are suppressed before render, and a single replacement event timeline
owns all transient explanations. Continuous motion and media cues are retained.
No webpage reference video is embedded. Educational diagrams are schematics.
"""
import math, os, time, wave, subprocess, argparse
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import egi_v12_software_connected as sw
import egi_v12_tech_mechanics_connected as tm
import egi_v13_icon_microanimations as icons

W,H,FPS,DUR=sw.W,sw.H,30,sw.DUR
WHITE,BLUE,CYAN,GOLD,TEAL=sw.WHITE,sw.BLUE,sw.CYAN,sw.GOLD,sw.TEAL
VIEW=(26,351,1052,1467)
FONTS={i:ImageFont.truetype(sw.SEMI,i) for i in range(17,36)}

# Important: V12 is the only underlying motion source. V13/V14 do NOT get
# composited, because both previously drew their own chips above older chips.
sw.transient_chip=lambda *args,**kwargs:None
sw.micro_word=lambda *args,**kwargs:None
sw.data_files=lambda *args,**kwargs:None

@dataclass(frozen=True)
class Event:
    start:float
    end:float
    label:str
    icon:str
    world:tuple
    offset:tuple
    color:tuple

SOFTWARE=[
    Event(.84,2.82,'TYPE THE URL','keyboard',(369,1300),(-178,-196),CYAN),
    Event(4.30,5.95,'DNS LOOKUP','search',(871,651),(-430,125),BLUE),
    Event(6.60,7.90,'IP FOUND','globe',(868,701),(-235,114),TEAL),
    Event(8.35,9.72,'TCP HANDSHAKE','arrows',(641,901),(-432,-156),GOLD),
    Event(10.57,12.06,'SECURE','lock',(646,939),(-345,-160),TEAL),
    Event(13.07,14.73,'HTTP REQUEST','document',(700,1041),(-300,-140),CYAN),
    Event(15.30,17.15,'SERVER WORK','chip',(883,997),(-310,-160),BLUE),
    Event(20.05,21.63,'200 OK','check',(883,1107),(-285,-145),TEAL),
    Event(26.15,28.15,'PAGE RENDER','code',(364,874),(180,-152),CYAN),
    Event(30.52,32.15,'PAGE READY','check',(362,973),(170,-152),TEAL),
]
TECH=[
    Event(4.48,6.08,'AC CURRENT','wave',(410,1247),(-250,-153),GOLD),
    Event(7.20,8.76,'FIELD FORMS','magnet',(419,993),(156,-125),CYAN),
    Event(10.65,12.35,'FLUX LINKED','link',(405,857),(-185,-119),BLUE),
    Event(15.08,16.67,'INDUCED AC','coil',(415,715),(110,122),GOLD),
    Event(18.29,20.01,'RECTIFIER','diode',(868,808),(-442,-77),CYAN),
    Event(21.57,23.37,'REGULATOR','chip',(868,843),(-447,-86),TEAL),
    Event(25.14,26.83,'DC OUTPUT','arrows',(875,940),(-449,-160),BLUE),
    Event(29.10,30.98,'CHARGING','battery',(896,1126),(-294,-148),TEAL),
]
EVENTS={'software':SOFTWARE,'technology':TECH}
# The resource files and the explanatory text have distinct ownership.
# Detailed file motion is not counted as a second transient callout.
sw.CAPTIONS=[(st,en,head,
    'HTML, CSS and JavaScript arrive as separate files.' if head=='05   RETURN THE RESPONSE'
    else 'HTML structures it. CSS styles it. JavaScript adds behavior.' if head=='06   BUILD THE PAGE'
    else detail)
    for st,en,head,detail in sw.CAPTIONS]



def clamp(a,lo=0.,hi=1.):return max(lo,min(hi,a))
def smooth(a):a=clamp(a);return a*a*(3-2*a)
def project(mode,world,t):return icons.project('software' if mode=='software' else 'technology',world,t)
def a255(x):return round(clamp(x)*255)
def dot(d,p,r,c,a=1.):
    if a<.01:return
    x,y=p;d.ellipse((x-r,y-r,x+r,y+r),fill=(*c,a255(a)))
def ring(d,p,r,c,a=.8,w=2):
    if a<.01:return
    x,y=p;d.ellipse((x-r,y-r,x+r,y+r),outline=(*c,a255(a)),width=w)
def fade(t,start,end,fi=.23,fo=.42):
    return smooth((t-start)/fi)*(1-smooth((t-(end-fo))/fo))


def validate_events():
    for mode,evs in EVENTS.items():
        for i,e in enumerate(evs):
            assert e.start < e.end <= DUR
            assert e.end-e.start >=1.1
            if i:assert evs[i-1].end < e.start, (mode,evs[i-1],e)
            f=FONTS[28]; bb=f.getbbox(e.label)
            assert bb[2]-bb[0] < 260, (e.label,bb)


def draw_event(d,mode,t,event,boxes):
    """ONE event -> ONE card; its label dissolves; icon is the same icon.
    All coordinates are dynamically projected into the moving source scene.
    """
    if not event.start<=t<event.end:return
    age=t-event.start;dur=event.end-event.start
    a=fade(t,event.start,event.end)
    if a<.015:return
    x0,y0=project(mode,event.world,t)
    if not (VIEW[0]+28<x0<VIEW[2]-28 and VIEW[1]+28<y0<VIEW[3]-28):return
    width,height=268,79
    x=clamp(x0+event.offset[0],VIEW[0]+25,VIEW[2]-width-25)
    y=clamp(y0+event.offset[1]-17*(1-smooth(age/.28)),VIEW[1]+24,VIEW[3]-height-24)
    # automatic duplicate/collision check
    bounds=(round(x),round(y),round(x+width),round(y+height))
    for old in boxes:
        overlap=not(bounds[2]<old[0] or old[2]<bounds[0] or bounds[3]<old[1] or old[3]<bounds[1])
        if overlap:raise AssertionError('DUPLICATE_OR_OVERLAP '+mode+': '+event.label)
    boxes.append(bounds)
    # smooth near-origin leader and a separate point, not a filled bubble
    tail_x=clamp(x0,x+13,x+width-13)
    tail_y=clamp(y0,y+8,y+height-8)
    d.line([(x0,y0),(tail_x,tail_y)],fill=(*event.color,a255(a*.62)),width=2)
    ring(d,(x0,y0),7,event.color,a*.88,2)
    # dark elegant floating card with highlight instead of glowing balloon
    d.rounded_rectangle((x+5,y+7,x+width+5,y+height+7),radius=14,fill=(5,10,17,a255(a*.35)))
    d.rounded_rectangle((x,y,x+width,y+height),radius=14,fill=(13,30,44,a255(a*.92)),outline=(*event.color,a255(a*.88)),width=2)
    d.line([(x+16,y+5),(x+width-17,y+5)],fill=(*event.color,a255(a*.23)),width=2)
    d.rounded_rectangle((x+10,y+10,x+71,y+height-10),radius=10,fill=(28,58,70,a255(a*.88)))
    icon_strength=a*(.78+.22*math.sin(math.pi*smooth(age/.35)))
    icons.draw_icon(d,x+21,y+20,41,event.icon,event.color,icon_strength)
    # one measured text; never use a second explanatory card for same event
    size=28
    bb=d.textbbox((0,0),event.label,font=FONTS[size])
    while bb[2]-bb[0]>width-92 and size>17:
        size-=1;bb=d.textbbox((0,0),event.label,font=FONTS[size])
    if bb[2]-bb[0]>width-92:raise ValueError('EVENT_TEXT_OVERFLOW '+event.label)
    d.text((x+81,y+(height-(bb[3]-bb[1]))/2-bb[1]),event.label,font=FONTS[size],fill=(*WHITE,a255(a)))
    # fine progress rail shows cause->consequence without another notification
    prog=smooth(age/dur)
    d.line([(x+12,y+height-7),(x+12+(width-24)*prog,y+height-7)],fill=(*event.color,a255(a*.80)),width=2)
    # short, spatially anchored dissolution after text; no second pop
    q=smooth((t-(event.end-.35))/.35)
    if .03<q<1:
        for i in range(14):
            phi=math.tau*i/14
            xx=x+170 +q*29*math.cos(phi) + 6*q
            yy=y+height/2+q*17*math.sin(phi)-9*q
            dot(d,(xx,yy),1.2+(i%3)*.5,event.color,(1-q)*.50)


def callout_layer(mode,t):
    out=Image.new('RGBA',(W,H),(0,0,0,0))
    d=ImageDraw.Draw(out)
    boxes=[]
    # exclusive ownership: at most one callout per video frame
    for ev in EVENTS[mode]:draw_event(d,mode,t,ev,boxes)
    assert len(boxes)<=1,(mode,t,boxes)
    # independent process detail (not extra popup cards)
    if mode=='software':software_detail(d,t)
    else:tech_detail(d,t)
    # crop strictly to machine viewport, preserve title/caption/watermark
    result=Image.new('RGBA',(W,H),(0,0,0,0))
    result.alpha_composite(out.crop(VIEW),(VIEW[0],VIEW[1]))
    return result


def path_marker(d,t,st,en,path,col,label):
    """One small labelled TCP packet physically traverses an existing route."""
    if not st<=t<en:return
    u=smooth((t-st)/(en-st))
    info=sw.PATH_DATA[path]
    xx,yy=sw.path_xy(info,info[2]*u)
    x,y=project('software',(xx,yy),t)
    if not (VIEW[0]+30<x<VIEW[2]-30 and VIEW[1]+30<y<VIEW[3]-30):return
    a=fade(t,st,en,.1,.14)
    # no balloon, no duplicate badge: packet + tiny 3-letter tag on path
    d.rounded_rectangle((x-20,y-11,x+20,y+11),radius=5,fill=(14,34,45,a255(a*.9)),outline=(*col,a255(a)),width=2)
    if label:
        f=FONTS[17];bb=d.textbbox((0,0),label,font=f)
        d.text((x-(bb[2]-bb[0])/2-bb[0],y-(bb[3]-bb[1])/2-bb[1]),label,font=f,fill=(*WHITE,a255(a)))
    for j in range(1,5):
        px,py=sw.path_xy(info,info[2]*max(0,u-.07*j))
        dot(d,project('software',(px,py),t),3-.40*j,col,a*(.45-.06*j))


def software_detail(d,t):
    # DNS keeps a tiny status dot after success; it is NOT a second text card.
    if t>=6.7:
        x,y=project('software',(961,640),t)
        if VIEW[0]+14<x<VIEW[2]-14 and VIEW[1]+14<y<VIEW[3]-14:
            p=smooth((t-6.7)/.5)
            ring(d,(x,y),10,TEAL,.8*p)
            icons.draw_icon(d,x-7,y-7,14,'check',TEAL,.95*p)
    # TCP handshake: packets share the same paths as V12 connector lines.
    for st,en,path,c,label in ((8.22,8.64,'tls_up',BLUE,'SYN'),(8.70,9.13,'tls_down',GOLD,'S/A'),(9.20,9.62,'tls_up',TEAL,'ACK')):
        path_marker(d,t,st,en,path,c,label)
    # Validated lock exists in original apparatus. Add at most a thin confirmation halo.
    if t>10.65:
        x,y=project('software',(646,943),t)
        if VIEW[0]+25<x<VIEW[2]-25 and VIEW[1]+25<y<VIEW[3]-25:
            p=smooth((t-10.65)/.7)
            ring(d,(x,y),44,TEAL,p*.22,2)
    # Named files travel and remain identifiable until their browser work is complete.
    resource_pipeline(d,t)
    # When page finishes, a small confirmation burst originates in the browser.
    if 30.9<t<32.0:
        x,y=project('software',(357,952),t)
        p=smooth((t-30.9)/1.1)
        for k in range(14):
            th=math.tau*k/14
            dot(d,(x+(19+54*p)*math.cos(th),y+(19+54*p)*math.sin(th)),2.3,TEAL,(1-p)*.62)



# Three semantic objects: never replace their names with a generic RESOURCES caption.
# Their paths are coupled to original HTTP response/resource paths. Positions are
# sampled in world space, then transformed with the SAME continuous V12 camera.
RESOURCE_SPECS=(
    dict(name='HTML',purpose='STRUCTURE',color=GOLD,route='response',start=18.58,end=21.80,dock=22.12),
    dict(name='CSS',purpose='STYLING',color=BLUE,route='resources',start=20.30,end=23.75,dock=23.95),
    dict(name='JAVASCRIPT',purpose='BEHAVIOR',color=TEAL,route='resources',start=22.12,end=25.34,dock=25.50),
)

def resource_document(d,t,spec,idx):
    st,en=spec['start'],spec['end']
    if not (st<=t<en):return
    u=smooth((t-st)/(en-st))
    info=sw.PATH_DATA[spec['route']]
    wx,wy=sw.path_xy(info,info[2]*u)
    # Documents use parallel, slight stagger, but follow the same route.
    lane=(idx-1)*21
    x,y=project('software',(wx,wy+lane),t)
    if not (VIEW[0]+34<x<VIEW[2]-34 and VIEW[1]+30<y<VIEW[3]-30):return
    a=fade(t,st,en,.16,.20)
    if a<.025:return
    col=spec['color']
    # Colored stream and directional velocity streaks are attached to the file.
    for k in range(1,7):
        uu=max(0.,u-.031*k)
        sx,sy=sw.path_xy(info,info[2]*uu)
        px,py=project('software',(sx,sy+lane),t)
        if VIEW[0]+4<px<VIEW[2]-4 and VIEW[1]+4<py<VIEW[3]-4:
            dot(d,(px,py),max(.9,3.4-.36*k),col,a*(.65-.08*k))
    # Single self-contained file icon and its name. No second bubble follows it.
    size=61+4*math.sin(math.pi*u)
    w=91 if idx<2 else 124
    x0=clamp(x-w/2,VIEW[0]+5,VIEW[2]-w-5); y0=y-34
    d.rounded_rectangle((x0+2,y0+4,x0+w+2,y0+64),radius=10,fill=(3,15,24,a255(.55*a)))
    d.rounded_rectangle((x0,y0,x0+w,y0+60),radius=10,fill=(18,39,51,a255(.92*a)),outline=(*col,a255(a)),width=2)
    # dog-ear document icon
    d.line([(x0+10,y0+10),(x0+30,y0+10),(x0+39,y0+19),(x0+39,y0+43),(x0+10,y0+43),(x0+10,y0+10)],fill=(*col,a255(a*.87)),width=2)
    d.line([(x0+30,y0+10),(x0+30,y0+19),(x0+39,y0+19)],fill=(*col,a255(a*.87)),width=2)
    for ky in (28,35):d.line([(x0+16,y0+ky),(x0+33,y0+ky)],fill=(*col,a255(a*.7)),width=2)
    label='JS' if idx==2 else spec['name']
    f=FONTS[23] if idx!=2 else FONTS[25]
    bb=f.getbbox(label)
    tx=x0+45+max(0,(w-49-(bb[2]-bb[0]))/2)-bb[0]
    ty=y0+(60-(bb[3]-bb[1]))/2-bb[1]
    d.text((tx,ty),label,font=f,fill=(*WHITE,a255(a)))
    # The exact file identity stays in the same moving object.

def resource_docks(d,t):
    # The input files settle and become the browser's three processing jobs.
    # The cards are world-anchored, below the existing browser window and above
    # the keyboard, preserving spatial continuity under camera pans and zooms.
    for idx,spec in enumerate(RESOURCE_SPECS):
        st=spec['end']-.12
        p=smooth((t-st)/.55)
        if p<=0.01:continue
        x0=99+idx*151
        x1=x0+143
        y0=1203
        xy0=project('software',(x0,y0),t)
        xy1=project('software',(x1,y0+49),t)
        x,y=xy0;xx,yy=xy1
        if xx<VIEW[0]+20 or x>VIEW[2]-20 or yy<VIEW[1]+20 or y>VIEW[3]-20:continue
        x=clamp(x,VIEW[0]+10,VIEW[2]-150)
        xx=min(VIEW[2]-8,max(x+80,xx))
        y=clamp(y,VIEW[1]+8,VIEW[3]-57)
        yy=min(VIEW[3]-6,max(y+35,yy))
        col=spec['color']
        # Filled edge progress indicates each file being consumed by the browser.
        d.rounded_rectangle((x,y,xx,yy),radius=9,fill=(13,36,47,a255(.88*p)),outline=(*col,a255(.85*p)),width=2)
        label=('HTML','CSS','JS')[idx]
        font=FONTS[24];bb=font.getbbox(label)
        d.text((x+13,y+(yy-y-(bb[3]-bb[1]))/2-bb[1]),label,font=font,fill=(*WHITE,a255(p)))
        # Per-file progress fills in the exact same dock; never create another card.
        prog=smooth((t-spec['end'])/(1.2+idx*.75))
        barx=x+10+(xx-x-20)*prog
        d.line([(x+10,yy-7),(barx,yy-7)],fill=(*col,a255(p)),width=4)
        if prog>.95:
            icons.draw_icon(d,xx-38,y+8,24,'check',col,p)

def process_browser_resources(d,t):
    # Additional visual explanation inside the SAME browser page: DOM hierarchy
    # emerges from HTML; CSS paints existing elements; JS makes a live control.
    if t<22.0:return
    p_html=smooth((t-22.1)/2.25)
    p_css=smooth((t-24.3)/2.2)
    p_js=smooth((t-27.6)/1.15)
    # Three DOM outline boxes build progressively, not a slide transition.
    if .01<p_html<1 and t<25.5:
        a=fade(t,22.,25.5,.5,.6)*.73
        world_boxes=((122,724,509,813),(136,835,507,969),(143,982,507,1080))
        for k,box in enumerate(world_boxes):
            p=smooth((t-(22.15+k*.38))/.55)
            if p<=0:continue
            ax,ay=project('software',(box[0],box[1]),t)
            bx,by=project('software',(box[2],box[3]),t)
            if ax<VIEW[0]+8 or ay<VIEW[1]+8 or bx>VIEW[2]-8 or by>VIEW[3]-8:continue
            # trace four corners of each DOM object, anchored to actual page.
            c=GOLD
            for x,y,sx,sy in ((ax,ay,1,1),(bx,ay,-1,1),(ax,by,1,-1),(bx,by,-1,-1)):
                d.line([(x,y+sy*min(26*p,(by-ay)/3)),(x,y),(x+sx*min(45*p,(bx-ax)/3),y)],fill=(*c,a255(a*p)),width=3)
    if p_css>.01 and t<29.1:
        a=fade(t,24.45,29.1,.4,.7)
        # Paint strokes follow existing browser card edges as style is applied.
        for k in range(4):
            st=24.6+.42*k
            u=smooth((t-st)/.95)
            if u<=0:continue
            ax,ay=project('software',(127+105*k,854),t)
            bx,by=project('software',(127+105*k+70*u,854),t)
            if VIEW[0]+15<ax<bx<VIEW[2]-15 and VIEW[1]+15<ay<VIEW[3]-15:
                d.line([(ax,ay),(bx,by)],fill=(*BLUE,a255(a*u*.75)),width=4)
                dot(d,(bx,by),3.8,BLUE,a*u*.75)
    if p_js>.01 and t<32.4:
        # Click ripple follows the mouse as the page becomes interactive.
        a=fade(t,27.7,32.4,.35,.5)
        center=project('software',(380,1001),t)
        if VIEW[0]+80<center[0]<VIEW[2]-80 and VIEW[1]+80<center[1]<VIEW[3]-80:
            for k in range(2):
                q=((t-28.1-k*.62)/1.2)
                if q<=0 or q>=1:continue
                r=12+40*smooth(q)
                ring(d,center,r,TEAL,(1-q)*a*.72,3)
            if t>29.0:
                icons.draw_icon(d,center[0]+22,center[1]-52,23,'check',TEAL,a*.92)

def resource_pipeline(d,t):
    for k,spec in enumerate(RESOURCE_SPECS):
        resource_document(d,t,spec,k)
    resource_docks(d,t)
    process_browser_resources(d,t)

def tech_detail(d,t):
    # A flow indicator is triggered by magnetic coupling, without duplicating
    # the preexisting V12 11 field lines / coil dots.
    if 10.1<t<16.8:
        q=fade(t,10.1,16.8,.7,.8)
        for k in range(8):
            st=10.1 + k*.26
            u=((t-st)*.50)%1
            if t<st:continue
            # tiny flashes arrive at the receiver through the existing flux field
            px=405+120*math.sin(u*math.tau+k*.35)*(.3+.7*u)
            py=1121-245*u
            x,y=project('technology',(px,py),t)
            if VIEW[0]+15<x<VIEW[2]-15 and VIEW[1]+15<y<VIEW[3]-15:
                dot(d,(x,y),2.7,CYAN,q*.40)
    # Show a single signal in a real circuit location, rather than a second 'AC'
    # bubble or floating oscilloscope window.
    if 16.8<t<26.8:
        q=fade(t,16.8,26.8,.5,.5)
        rectify=smooth((t-18.4)/2.0)
        regulate=smooth((t-22.0)/2.2)
        world=[]
        for j in range(49):
            u=j/48
            raw=math.sin(u*math.tau*2.7-t*2.)
            rect=abs(raw)
            v=raw*(1-rectify)+rectify*(1-regulate)+regulate*.68
            world.append((777+210*u,771-10*v))
        pts=[project('technology',p,t) for p in world]
        d.line(pts,fill=(*CYAN,a255(q*.70)) if regulate<.5 else (*TEAL,a255(q*.74)),width=3,joint='curve')
        # a moving probe dot rides one interpolated value of the waveform
        ix=int(((t-16.8)*.35%1)*48)
        dot(d,pts[ix],3.2,TEAL if regulate>.5 else GOLD,q*.85)
    # Continuous source->IC->battery particles, one connected circuit path.
    for route,st,en,color in (
        ([(555,704),(655,703),(755,778)],15.4,25.8,CYAN),
        ([(875,868),(875,940),(875,1098)],21.5,34.0,TEAL)):
        if not st<t<en:continue
        a=fade(t,st,en,.4,.6)
        path=sw.prep(route)
        for k in range(7):
            s=((t-st)*.34+k/7)%1
            x,y=project('technology',sw.path_xy(path,path[2]*s),t)
            if VIEW[0]+12<x<VIEW[2]-12 and VIEW[1]+12<y<VIEW[3]-12:
                dot(d,(x,y),3.2,color,.58*a)
    # No balloon-shaped fills; only hairline pulses at physical terminals.
    if 21.3<t<24.0:
        x,y=project('technology',(875,879),t)
        p=smooth((t-21.3)/2.7)
        ring(d,(x,y),16+31*p,TEAL,(1-p)*.48,2)


def frame(mode,t):
    base=sw.frame(t) if mode=='software' else tm.frame('tech',t)
    im=base.convert('RGBA')
    im.alpha_composite(callout_layer(mode,t))
    return im.convert('RGB')

CUES={
    'software':[(8.22,500,.031),(8.70,680,.029),(9.20,780,.032),(10.6,940,.024),(18.58,720,.021),(20.30,840,.021),(22.12,990,.021),(22.1,570,.018),(24.5,765,.016),(28.25,920,.023)],
    'technology':[(10.6,420,.020),(16.8,710,.018),(18.4,810,.028),(21.6,930,.026),(25.2,1030,.021)]
}

def audio(mode,path):
    root=os.environ.get('EGI_OUTPUT_DIR','/mnt/data')
    source=os.path.join(root,'EGI_V12_Software_Original_SFX.wav' if mode=='software' else 'EGI_V12_tech_SFX.wav')
    if not os.path.exists(source):
        sw.sound(source) if mode=='software' else tm.audio('tech',source)
    with wave.open(source,'rb') as r:
        sr=r.getframerate();raw=r.readframes(r.getnframes())
        assert sr==48000 and r.getnchannels()==1
    signal=np.frombuffer(raw,dtype=np.int16).astype('float32')/32768
    for j,ev in enumerate(EVENTS[mode]):
        st=int(ev.start*sr);end=min(len(signal),st+int(.145*sr))
        if end<=st:continue
        u=np.arange(end-st,dtype=np.float32)/sr
        hz=560+(j%6)*72
        signal[st:end]+=.018*np.sin(math.tau*(hz+100*u)*u)*np.exp(-u*34)
    for sec,hz,amp in CUES[mode]:
        st=int(sec*sr);end=min(len(signal),st+int(.16*sr))
        if end<=st:continue
        u=np.arange(end-st,dtype=np.float32)/sr
        signal[st:end]+=amp*np.sin(math.tau*hz*u)*np.exp(-u*31)
    signal=np.clip(signal,-.93,.93)
    with wave.open(path,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr)
        w.writeframes((signal*32767).astype(np.int16).tobytes())

def render(mode,out,aud,seconds=DUR):
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',aud,'-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-map','0:v','-map','1:a','-t',str(seconds),'-movflags','+faststart',out]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    start=time.time()
    try:
        for i in range(round(seconds*FPS)):
            proc.stdin.write(np.asarray(frame(mode,i/FPS),dtype=np.uint8).tobytes())
            if i%216==0:print('RENDER',mode,i,'/',round(seconds*FPS),'elapsed',round(time.time()-start,1),flush=True)
        proc.stdin.close();proc.stdin=None
        err=proc.communicate()[1]
        if proc.returncode:raise RuntimeError(err.decode()[-2000:])
    except BaseException:
        proc.kill();raise
    print('DONE',mode,os.path.getsize(out),round(time.time()-start,1),flush=True)

def sheet(mode,out):
    times=[1.3,4.9,6.9,8.8,11.4,14.2,18.9,22.4,26.8,29.9,31.3,34.2]
    canvas=Image.new('RGB',(1000,1332),(7,15,25))
    for i,t in enumerate(times):
        thumb=frame(mode,t).resize((250,444),Image.Resampling.LANCZOS)
        canvas.paste(thumb,((i%4)*250,(i//4)*444))
    canvas.save(out,quality=95)

def verify_timeline():
    validate_events()
    for mode in EVENTS:
        # Each possible displayed event is exclusive; sample all source frames.
        for i in range(int(DUR*FPS)):
            t=i/FPS
            active=sum(e.start<=t<e.end for e in EVENTS[mode])
            assert active<=1,(mode,t,active)
    print('QA: EVENTS_EXCLUSIVE, LABEL_FIT, 1080_TIMESTAMPS_PER_MODE OK',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=('software','technology','both'),default='both')
    parser.add_argument('--preview',action='store_true')
    parser.add_argument('--seconds',type=float,default=DUR)
    args=parser.parse_args()
    if not 1 <= args.seconds <= DUR:
        parser.error('--seconds must be within 1..36')
    os.makedirs(os.environ.get('EGI_OUTPUT_DIR','/mnt/data'),exist_ok=True)
    verify_timeline()
    for mode in ('software','technology') if args.mode=='both' else (args.mode,):
        stem=os.path.join(os.environ.get('EGI_OUTPUT_DIR','/mnt/data'),'EGI_V16_'+('Software_HTML_CSS_JavaScript_Rich_Animation' if mode=='software' else 'Technology_One_Event_One_Callout'))
        sheet(mode,stem+'_Storyboard.jpg')
        print('SHEET_DONE',mode,flush=True)
        if not args.preview:
            audio(mode,stem+'_Audio.wav')
            render(mode,stem+'.mp4',stem+'_Audio.wav',seconds=args.seconds)