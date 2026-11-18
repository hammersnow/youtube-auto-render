#!/usr/bin/env python3
"""EGI V13 — event-anchored icon microanimations over existing continuous V12 films.
The original mechanical/data processes, camera keyframes and music-free synthetic SFX
are preserved. Icons/labels are time-bound and spatially linked to source mechanisms.
No scene cuts, no underlying footage resets; all typography is measured before paint.
"""
import os, math, wave, argparse, subprocess, time
import numpy as np
from PIL import Image, ImageDraw
import egi_v12_software_connected as sw
import egi_v12_tech_mechanics_connected as tm

W,H,FPS,DUR=sw.W,sw.H,sw.FPS,sw.DUR
BLUE,CYAN,GOLD,TEAL,WHITE=sw.BLUE,sw.CYAN,sw.GOLD,sw.TEAL,sw.WHITE

# start, lifetime, label, icon, world anchor, chip offset (screen coords), color
SOFTWARE=[
 (1.65,1.55,'URL INPUT','keyboard',(367,1352),(-150,-210),CYAN),
 (4.75,1.65,'DNS LOOKUP','search',(865,656),(-490,-274),BLUE),
 (6.62,1.70,'IP FOUND','globe',(870,701),(-235,82),TEAL),
 (9.23,1.65,'TLS HANDSHAKE','shield',(642,940),(98,-150),GOLD),
 (11.03,1.72,'ENCRYPTED','lock',(641,941),(91,82),TEAL),
 (13.40,1.85,'HTTP REQUEST','arrows',(720,1037),(-225,-139),CYAN),
 (18.55,1.72,'HTML RECEIVED','document',(775,1110),(-310,-137),GOLD),
 (23.00,1.76,'CSS + JS','code',(676,1177),(-267,78),BLUE),
 (26.05,1.74,'PIXELS PAINT','layers',(325,875),(118,-122),CYAN),
 (30.42,1.86,'PAGE BUILT','check',(356,975),(155,-119),TEAL),
]
TECHNOLOGY=[
 (4.60,1.64,'AC CURRENT','wave',(408,1254),(-170,-130),GOLD),
 (7.25,1.74,'MAGNETIC FIELD','magnet',(408,990),(122,-94),CYAN),
 (10.72,1.74,'FLUX LINKED','link',(409,883),(-242,-120),BLUE),
 (15.08,1.78,'INDUCED AC','coil',(406,717),(110,96),GOLD),
 (17.95,1.80,'RECTIFY','diode',(787,804),(-270,114),CYAN),
 (21.75,1.85,'REGULATE','chip',(876,858),(-282,-138),TEAL),
 (25.65,1.78,'DC CURRENT','arrows',(875,927),(-276,107),BLUE),
 (29.40,2.05,'CHARGING','battery',(892,1107),(-273,-139),TEAL),
]


def clamp(v,a,b):return max(a,min(b,v))
def smooth(v):v=clamp(v,0,1);return v*v*(3-2*v)
def opacity(a):return int(clamp(a,0,1)*255)

def project(mode,source,t):
    # Match the viewport crop/resize of the original production renderers exactly.
    vx0,vy0,vx1,vy1=26,351,1052,1467
    cx,cy,zoom=sw.camera_params(t) if mode=='software' else tm.camera('tech',t)
    vw,vh=vx1-vx0,vy1-vy0
    cw,ch=vw/zoom,vh/zoom
    x0=clamp(cx-cw/2,vx0,vx1-cw)
    y0=clamp(cy-ch/2,vy0,vy1-ch)
    return (vx0+(source[0]-x0)*vw/cw,vy0+(source[1]-y0)*vh/ch)

def draw_icon(d,x,y,size,typ,color,alpha):
    # Small vector pictograms. Strokes keep legible at thumbnail scale.
    c=(*color,opacity(alpha))
    s=size
    p=lambda u,v:(round(x+s*u),round(y+s*v))
    def ln(points,w=4):d.line([p(*q) for q in points],fill=c,width=w,joint='curve')
    def ellipse(x0,y0,x1,y1,w=3):d.ellipse((*p(x0,y0),*p(x1,y1)),outline=c,width=w)
    def rect(x0,y0,x1,y1,r=4,w=3):d.rounded_rectangle((*p(x0,y0),*p(x1,y1)),radius=r,outline=c,width=w)
    if typ=='keyboard':
        rect(.06,.22,.94,.79)
        for i in range(3):
            for j in range(4):
                ln([(.20+j*.16,.35+i*.13),(.26+j*.16,.35+i*.13)],2)
        ln([(.37,.69),(.66,.69)],3)
    elif typ=='search':
        ellipse(.10,.08,.66,.67);ln([(.61,.61),(.96,.95)],5)
    elif typ=='globe':
        ellipse(.1,.1,.9,.9);ln([(.1,.5),(.9,.5)],2);ellipse(.33,.1,.67,.9,2)
    elif typ=='shield':
        ln([(.5,.07),(.85,.2),(.83,.65),(.5,.95),(.17,.65),(.15,.2),(.5,.07)],4)
        ln([(.31,.52),(.45,.65),(.70,.35)],4)
    elif typ=='lock':
        d.arc((*p(.25,.05),*p(.75,.70)),180,360,fill=c,width=4)
        rect(.17,.46,.83,.96,5);ellipse(.44,.62,.57,.74,2)
    elif typ=='arrows':
        ln([(.08,.32),(.87,.32),(.69,.14)],4);ln([(.87,.32),(.68,.51)],4)
        ln([(.92,.70),(.13,.70),(.31,.51)],4);ln([(.13,.70),(.32,.88)],4)
    elif typ=='document':
        ln([(.22,.08),(.68,.08),(.86,.28),(.86,.92),(.22,.92),(.22,.08)],4)
        ln([(.67,.1),(.67,.30),(.84,.30)],3)
        ln([(.33,.48),(.74,.48)],3);ln([(.33,.66),(.68,.66)],3)
    elif typ=='code':
        ln([(.33,.18),(.1,.5),(.33,.82)],4)
        ln([(.68,.18),(.90,.5),(.68,.82)],4)
        ln([(.58,.09),(.43,.90)],3)
    elif typ=='layers':
        ln([(.10,.32),(.5,.06),(.9,.32),(.5,.58),(.10,.32)],3)
        ln([(.10,.50),(.50,.76),(.90,.50)],3)
        ln([(.10,.66),(.50,.93),(.90,.66)],3)
    elif typ=='check':
        ellipse(.08,.08,.92,.92)
        ln([(.25,.49),(.45,.70),(.77,.32)],5)
    elif typ=='wave':
        pts=[(i/24, .5-.33*math.sin(i*math.tau/12)) for i in range(25)]
        ln(pts,4)
    elif typ=='magnet':
        d.arc((*p(.13,.08),*p(.87,.86)),0,180,fill=c,width=7)
        ln([(.13,.48),(.13,.84)],8);ln([(.87,.48),(.87,.84)],8)
    elif typ=='link':
        ellipse(.03,.28,.56,.76);ellipse(.44,.24,.97,.72)
        ln([(.33,.5),(.65,.5)],3)
    elif typ=='coil':
        pts=[(.09,.53)]
        for i in range(4):
            for z in range(11):
                u=z/10
                pts.append((.12+i*.20+.10*u,.52-.24*math.sin(u*math.tau)))
        ln(pts+[ (.94,.53)],3)
    elif typ=='diode':
        ln([(.04,.5),(.32,.5)],3)
        d.polygon([p(.32,.23),p(.32,.77),p(.72,.5)],outline=c)
        ln([(.73,.2),(.73,.8)],4);ln([(.73,.5),(.96,.5)],3)
    elif typ=='chip':
        rect(.2,.2,.8,.8,5)
        for i in range(3):
            z=.32+.18*i
            ln([(.06,z),(.2,z)],3);ln([(.8,z),(.94,z)],3)
            ln([(z,.06),(z,.2)],3);ln([(z,.8),(z,.94)],3)
        ellipse(.4,.4,.6,.6,2)
    elif typ=='battery':
        rect(.1,.20,.85,.82,4)
        d.rectangle((*p(.86,.40),*p(.96,.62)),fill=c)
        ln([(.43,.35),(.3,.56),(.51,.56),(.4,.72),(.66,.46),(.47,.46)],4)

def pop(d,mode,t,event):
    start,duration,label,ico,world,off,color=event
    age=t-start
    if not (0 <= age < duration):return
    sx,sy=project(mode,world,t)
    if not (44<sx<1033 and 365<sy<1432):return
    # Pop moves near its actual source; connection line always points to machine.
    u=smooth(age/.30)
    retire=smooth((age-(duration-.52))/.52)
    x=clamp(sx+off[0],49,732)
    y=clamp(sy+off[1]-(1-u)*22,391,1351)
    ww,hh=306,87
    a=u*(1-retire)
    icon_a=u*(1-smooth((age-(duration-.25))/.25))
    if icon_a>.01:
        # content-attached lead line, short and unobtrusive
        px=clamp(sx,x+14,x+ww-14)
        py=clamp(sy,y+12,y+hh-12)
        line_a=icon_a*.70
        d.line([(sx,sy),(px,py)],fill=(*color,opacity(line_a)),width=3)
        d.ellipse((sx-6,sy-6,sx+6,sy+6),outline=(*color,opacity(icon_a)),width=3)
        d.rounded_rectangle((x,y,x+ww,y+hh),radius=16,fill=(14,30,42,opacity(.85*icon_a)),outline=(*color,opacity(.85*icon_a)),width=2)
        d.rounded_rectangle((x+9,y+10,x+77,y+77),radius=14,fill=(33,62,75,opacity(.75*icon_a)))
        draw_icon(d,x+20,y+20,47,ico,color,icon_a)
        # short expanding aperture pulse from icon, no giant fill
        if age<.55:
            pulse=smooth(age/.55)
            rad=37+19*pulse
            d.arc((x+43-rad,y+43-rad,x+43+rad,y+43+rad),15,165,fill=(*color,opacity((1-pulse)*.6)),width=3)
        # measure text, no overflow and no unknown-length fallback
        fontsize=32
        while fontsize>=15:
            bb=d.textbbox((0,0),label,font=sw.f(fontsize,'bold'))
            if bb[2]-bb[0] <= ww-104: break
            fontsize-=1
        if fontsize<15:raise ValueError('OVERFLOW '+label)
        d.text((x+94,y+(hh-(bb[3]-bb[1]))/2-bb[1]),label,font=sw.f(fontsize,'bold'),fill=(*WHITE,opacity(a)))
    # short dissolving glyph cloud; does not reset underlying view
    if retire>.03:
        centerx,centery=x+ww*.68,y+hh*.48
        for j in range(27):
            ang=j*2.39996
            radius=8+j%7*3
            q=retire
            xx=centerx+math.cos(ang)*radius*q + 16*q
            yy=centery+math.sin(ang)*radius*q-14*q
            al=opacity((1-q)*u*.6)
            if al>2:
                rr=1.5+(j%3)*.5
                d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill=(*color,al))


def traveling_cue(d,mode,t):
    # Tiny cause-and-effect markers moving on *existing* flow paths, never teleporting.
    if mode=='software':
        cues=[('dns_up',4.5,6.5,'search',GOLD),('tls_up',8.9,10.9,'shield',BLUE),
              ('get',13.0,15.3,'arrows',TEAL),('response',18.0,20.7,'document',CYAN)]
        for path,st,end,ico,col in cues:
            if not st<=t<=end:continue
            pts=sw.PATH_DATA[path];L=pts[2];p=clamp((t-st)/(end-st),0,1)
            xx,yy=sw.path_xy(pts,L*p)
            x,y=project(mode,(xx,yy),t)
            if 46<x<1032 and 369<y<1437:
                halo=7+4*math.sin(math.pi*p)
                d.ellipse((x-halo,y-halo,x+halo,y+halo),outline=(*col,190),width=2)
                draw_icon(d,x-9,y-9,18,ico,col,.9)
    else:
        # Traveling current markers follow the pre-existing electronics path.
        route=[((550,701),(660,701),(759,781),13.7,16.3,'wave',BLUE),
               ((780,867),(874,867),(874,945),21.4,24.2,'chip',TEAL)]
        for a,m,z,st,end,ico,col in route:
            if st<=t<=end:
                info=sw.prep([a,m,z]);xx,yy=sw.path_xy(info,info[2]*clamp((t-st)/(end-st),0,1))
                x,y=project(mode,(xx,yy),t)
                if 50<x<1028 and 373<y<1432:
                    d.ellipse((x-11,y-11,x+11,y+11),fill=(11,31,43,210),outline=(*col,230),width=2)
                    draw_icon(d,x-7,y-7,14,ico,col,.9)


def frame(mode,t):
    base=sw.frame(t) if mode=='software' else tm.frame('tech',t)
    layer=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(layer)
    traveling_cue(d,mode,t)
    for event in SOFTWARE if mode=='software' else TECHNOLOGY:
        pop(d,mode,t,event)
    # Strict safe area to prevent callouts bleeding into title or fixed explanation.
    result=base.convert('RGBA')
    result.alpha_composite(layer.crop((26,351,1052,1467)),(26,351))
    return result.convert('RGB')


def audio(mode,path):
    # Original V12 audio remains; new punctuated UI sounds match each pop emergence.
    old='/mnt/data/EGI_V12_Software_Original_SFX.wav' if mode=='software' else '/mnt/data/EGI_V12_tech_SFX.wav'
    if not os.path.exists(old):
        if mode=='software':sw.sound(old)
        else:tm.audio('tech',old)
    with wave.open(old,'rb') as w:
        sr=w.getframerate(); raw=w.readframes(w.getnframes()); ch=w.getnchannels()
    assert ch==1 and sr==48000
    out=np.frombuffer(raw,dtype=np.int16).astype(np.float32)/32768
    ev=SOFTWARE if mode=='software' else TECHNOLOGY
    for j,(start,duration,label,ico,loc,offs,col) in enumerate(ev):
        s=int(start*sr); n=min(int(.19*sr),len(out)-s)
        u=np.arange(n,dtype=np.float32)/sr
        fq=640+72*(j%5)
        out[s:s+n]+=(.027*np.sin(2*math.pi*(fq+160*u)*u)+.011*np.sin(2*math.pi*2.1*fq*u))*np.exp(-u*27)
        # fading word cloud: extremely subtle glassy tick after icon has landed
        s2=int((start+duration-.54)*sr); n2=min(int(.13*sr),len(out)-s2)
        if n2>0:
            u=np.arange(n2,dtype=np.float32)/sr
            out[s2:s2+n2]+=.011*np.sin(2*math.pi*1370*u)*np.exp(-u*32)
    out=np.clip(out,-.93,.93)
    with wave.open(path,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr)
        w.writeframes((out*32767).astype(np.int16).tobytes())

def animation_layer(mode,t):
    # Render only new *transparent* event animation. Source V12 is preserved
    # pixel-for-pixel beneath it, making the upgrade both faster and additive.
    layer=Image.new('RGBA',(W,H),(0,0,0,0))
    small=Image.new('RGBA',(W,H),(0,0,0,0))
    d=ImageDraw.Draw(small)
    traveling_cue(d,mode,t)
    for event in SOFTWARE if mode=='software' else TECHNOLOGY:
        pop(d,mode,t,event)
    layer.alpha_composite(small.crop((26,351,1052,1467)),(26,351))
    return layer


def render(mode,path,aud,seconds=None):
    base='/mnt/data/EGI_V12_Software_Connected_Microanimations.mp4' if mode=='software' else '/mnt/data/EGI_V12_Technology_Wireless_Charging_Microanimations.mp4'
    limit=int((seconds if seconds is not None else DUR)*FPS)
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y',
         '-i',base,
         '-f','rawvideo','-pixel_format','rgba','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0',
         '-i',aud,
         '-filter_complex','[0:v][1:v]overlay=shortest=1:format=auto,format=yuv420p[v]',
         '-map','[v]','-map','2:a:0','-c:v','libx264','-preset','veryfast','-crf','17',
         '-c:a','aac','-b:a','160k','-t',str(limit/FPS),'-movflags','+faststart',path]
    ff=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for i in range(limit):
            ff.stdin.write(np.asarray(animation_layer(mode,i/FPS),dtype=np.uint8).tobytes())
            if i%216==0:print('RENDER',mode,i,flush=True)
        ff.stdin.close();ff.stdin=None
        err=ff.communicate()[1]
        if ff.returncode:raise RuntimeError(err.decode()[-2500:])
    except BaseException:
        ff.kill();raise
    print('DONE',mode,os.path.getsize(path),flush=True)

def storyboard(mode,path):
    times=[1.85,4.9,6.9,9.6,11.2,13.7,18.8,23.4,29.8] if mode=='software' else [4.9,7.5,10.9,15.4,18.2,22,25.95,29.75,33]
    im=Image.new('RGB',(864,1536),(8,17,27))
    for i,t in enumerate(times):
        x=frame(mode,t).resize((288,512),Image.Resampling.LANCZOS)
        im.paste(x,((i%3)*288,(i//3)*512))
    im.save(path,quality=95)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--mode',choices=('software','technology','both'),default='both');a.add_argument('--preview',action='store_true');a.add_argument('--seconds',type=float);v=a.parse_args()
    for mode in ('software','technology') if v.mode=='both' else (v.mode,):
        stem='/mnt/data/EGI_V13_'+('Software' if mode=='software' else 'Technology')+'_Iconic_Continuous'
        storyboard(mode,stem+'_Storyboard.jpg')
        if not v.preview:
            a_path=stem+'_Audio.wav';audio(mode,a_path)
            render(mode,stem+'.mp4',a_path,v.seconds)