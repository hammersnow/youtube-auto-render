#!/usr/bin/env python3
import os, math, argparse, subprocess, time, wave
from PIL import Image, ImageDraw, ImageFont
import numpy as np

W,H=1080,1920
FPS=24
TOTAL=26.0
FRAMES=int(FPS*TOTAL)
FONT_DIR='/usr/share/fonts/opentype/inter/' if os.path.isfile('/usr/share/fonts/opentype/inter/Inter-Regular.otf') else '/usr/share/fonts/truetype/dejavu/'
FONT=os.path.join(FONT_DIR,'Inter-Regular.otf' if 'inter' in FONT_DIR else 'DejaVuSans.ttf')
FONT_B=os.path.join(FONT_DIR,'Inter-Bold.otf' if 'inter' in FONT_DIR else 'DejaVuSans-Bold.ttf')
FONT_M=os.path.join(FONT_DIR,'Inter-Medium.otf' if 'inter' in FONT_DIR else 'DejaVuSans.ttf')

BG=(9,17,29)
WHITE=(238,244,251)
MUTED=(152,166,185)
GOLD=(255,209,105)
AMBER=(255,166,75)
RED=(252,115,83)
BLUE=(54,204,251)
BLUE2=(123,225,255)
TEAL=(76,222,168)
CYAN=(110,240,255)
SILVER=(160,177,190)
DARKMET=(38,46,55)
LIGHTMET=(79,98,114)

SERIES='INSIDE THE MACHINE'
EP='EPISODE 03'
CUTS=(0.0,2.5,7.8,12.2,18.1,24.0,26.0)
PHASES=[
    ('00','INTERCOOLER','COOL THE BOOST BEFORE THE ENGINE','Hot compressed air releases heat before reaching the cylinders.',GOLD),
    ('01','HOT BOOST ARRIVES','HOT AIR ENTERS THE CORE','Compression heats the intake air leaving the turbo.',AMBER),
    ('02','HEAT TRANSFER','THE CORE ABSORBS HEAT','Charge air heats the metal tubes and the surrounding fins.',GOLD),
    ('03','COOLING AIR','AMBIENT FLOW REMOVES HEAT','Outside air sweeps through the fins and carries heat away.',BLUE),
    ('04','COOLER, DENSER BOOST','THE AIR LEAVES COOLER','Cooler charge air is denser, helping the engine make power.',TEAL),
    ('05','RECAP','HOT IN. COOL OUT.','The intercooler sits between the turbo and the engine.',GOLD)
]
TABS=(('HOT SIDE',AMBER),('CORE',GOLD),('AIRFLOW',BLUE),('COOL OUT',TEAL))

def ff(size,bold=False,medium=False):
    return ImageFont.truetype(FONT_B if bold else FONT_M if medium else FONT,size)
F_KICKER=ff(27,bold=True); F_MICRO=ff(24,medium=True)
F_HEADER=ff(58,bold=True); F_INDEX=ff(32,bold=True); F_BIG=ff(60,bold=True)
F_DESC=ff(36,medium=True); F_DETAIL=ff(29,medium=True); F_WM=ff(23,medium=True); F_FOOT=ff(25,medium=True)

def clamp(v,a=0.,b=1.): return min(b,max(a,v))
def lerp(a,b,t): return a+(b-a)*t
def smoothstep(x):
    x=clamp(x); return x*x*(3-2*x)

def mix(c1,c2,t):
    return tuple(int(lerp(a,b,t)) for a,b in zip(c1,c2))

def text_center(draw,xy,s,f,fill):
    box=draw.textbbox((0,0),s,font=f)
    draw.text((xy[0]-(box[2]-box[0])/2,xy[1]-(box[3]-box[1])/2),s,font=f,fill=fill)

def text_right(draw,xy,s,f,fill):
    box=draw.textbbox((0,0),s,font=f)
    draw.text((xy[0]-(box[2]-box[0]),xy[1]),s,font=f,fill=fill)

# These bounds are checked during storyboard construction, before any frames are encoded.
TEXT_QA=[]
def fitted_text(draw, label, rect, preferred=32, minimum=20, color=WHITE, bold=False, medium=False):
    """Center a single line safely inside rect; reject unreadably small text."""
    x0,y0,x1,y1=rect
    assert x1>x0 and y1>y0, (label, rect)
    # Rect itself is the text safe area (its border/padding already excluded).
    for size in range(int(preferred),int(minimum)-1,-1):
        f=ff(size,bold=bold,medium=medium)
        box=draw.textbbox((0,0),label,font=f)
        tw,th=box[2]-box[0],box[3]-box[1]
        if tw<=x1-x0 and th<=y1-y0:
            x=x0+(x1-x0-tw)/2-box[0]
            y=y0+(y1-y0-th)/2-box[1]
            draw.text((x,y),label,font=f,fill=color)
            qa_box=(x+box[0],y+box[1],x+box[2],y+box[3])
            eps=0.01
            assert qa_box[0]>=x0-eps and qa_box[1]>=y0-eps and qa_box[2]<=x1+eps and qa_box[3]<=y1+eps, (label, qa_box, rect)
            TEXT_QA.append({'label':label,'font_px':size,'bbox':tuple(round(v,1) for v in qa_box),'safe_rect':rect})
            return size
    raise ValueError(f'Text does not fit readable safe area: {label!r}; rect={rect}')

def draw_background():
    y=np.arange(H,dtype=np.float32)[:,None,None]
    x=np.arange(W,dtype=np.float32)[None,:,None]
    colors=np.array([10.,19.,31.])[None,None,:]+(y/H)*np.array([2.,1.,7.])[None,None,:]
    dist=np.sqrt(((x[:,:,0]-540.)/730.)**2+((y[:,0,0][:,None]-950.)/940.)**2)
    glow=np.maximum(0,1-dist)[...,None]*np.array([13.,10.,7.])[None,None,:]
    arr=np.broadcast_to(colors,(H,W,3)).copy()+glow
    im=Image.fromarray(np.uint8(np.clip(arr,0,255)),'RGB')
    d=ImageDraw.Draw(im)
    for xx in range(48,W-48,84): d.line([(xx,441),(xx,1404)],fill=(23,36,48),width=1)
    for yy in range(450,1410,84): d.line([(42,yy),(1038,yy)],fill=(23,36,48),width=1)
    d.rounded_rectangle((38,435,1042,1410),radius=27,fill=None,outline=(48,59,70),width=2)
    d.rounded_rectangle((38,1452,1042,1779),radius=32,fill=(25,24,24),outline=(72,60,47),width=3)
    d.line([(58,1826),(1022,1826)],fill=(78,74,63),width=2)
    return im
BASE=draw_background()

def phase(t):
    for i in range(6):
        if t < CUTS[i+1]:
            return i,clamp((t-CUTS[i])/(CUTS[i+1]-CUTS[i]))
    return 5,1.

def stage_panel(i):
    im=BASE.copy(); d=ImageDraw.Draw(im)
    idx,title,lead,detail,accent=PHASES[i]
    d.text((56,62),SERIES,font=F_KICKER,fill=(109,216,228))
    d.text((374,62),f'/  {EP}',font=F_KICKER,fill=(101,149,169))
    text_right(d,(1022,62),'INTERCOOLER / 2.5D CUTAWAY',F_MICRO,(136,144,157))
    d.text((56,140),'HOW AN INTERCOOLER',font=F_HEADER,fill=WHITE)
    d.text((56,207),'COOLS THE BOOST',font=F_HEADER,fill=WHITE)
    d.line([(55,308),(1025,308)],fill=(93,82,67),width=2)
    for j,(name,col) in enumerate(TABS):
        xx=55+j*244; active=(j==i-1)
        d.rounded_rectangle((xx,326,xx+230,424),radius=20,fill=(48,53,56) if active else (34,35,37),outline=col if active else (59,56,51),width=3 if active else 1)
        if active: d.rounded_rectangle((xx+7,412,xx+223,422),radius=4,fill=col)
        d.text((xx+17,346),f'{j+1:02d}',font=F_INDEX,fill=col if active else (104,98,92))
        fitted_text(d,name,(xx+54,346,xx+219,399),preferred=26,minimum=21,color=WHITE if active else (141,143,149),bold=True)
    d.rounded_rectangle((58,1474,1022,1735),radius=27,fill=(32,27,25),outline=(94,75,53),width=2)
    d.line([(138,1502),(942,1502)],fill=(87,72,57),width=2)
    fitted_text(d,title,(90,1516,990,1598),preferred=60,minimum=38,color=accent,bold=True)
    fitted_text(d,lead,(90,1606,990,1670),preferred=36,minimum=27,color=WHITE,medium=True)
    fitted_text(d,detail,(89,1676,991,1730),preferred=29,minimum=22,color=MUTED,medium=True)
    d.line([(60,1787),(1020,1787)],fill=(76,67,57),width=3)
    d.line([(60,1787),(60+(min(max(i-1,0),4))*240,1787)],fill=accent,width=7)
    text_center(d,(540,1830),'THE INTERCOOLER REDUCES CHARGE TEMPERATURE',F_FOOT,(159,178,193))
    d.line([(62,1863),(1018,1863)],fill=(63,68,69),width=2)
    d.text((62,1877),'ORIGINAL MOTION DESIGN',font=F_MICRO,fill=(125,128,129))
    text_right(d,(1018,1877),'Ekrem Gökberk İşcan',F_WM,(188,188,180))
    return im
BG_PANELS=[stage_panel(i) for i in range(6)]

# Apparatus geometry
CORE=(236,650,844,1110)
PIPE_Y=880
LEFT_PIPE_X0=68; LEFT_PIPE_X1=235
RIGHT_PIPE_X0=844; RIGHT_PIPE_X1=1012
CHANNELS=8
CH_H=32
GAP=18
CHANNEL_X0=286; CHANNEL_X1=794
CHANNEL_W=CHANNEL_X1-CHANNEL_X0
CHANNEL_LEN=CHANNEL_W

def channel_center(j):
    return 706 + j*(CH_H+GAP)

def make_base_scene():
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    # inlet/outlet pipes shadows
    d.line([(LEFT_PIPE_X0,PIPE_Y+14),(LEFT_PIPE_X1,PIPE_Y+14)],fill=(8,10,15),width=88)
    d.line([(RIGHT_PIPE_X0,PIPE_Y+14),(RIGHT_PIPE_X1,PIPE_Y+14)],fill=(8,10,15),width=88)
    # inlet / outlet metal tubes
    for x0,x1,edge,hi in ((LEFT_PIPE_X0,LEFT_PIPE_X1,(128,92,63),(221,168,115)), (RIGHT_PIPE_X0,RIGHT_PIPE_X1,(63,112,125),(168,228,235))):
        d.line([(x0,PIPE_Y),(x1,PIPE_Y)],fill=edge,width=76)
        d.line([(x0,PIPE_Y),(x1,PIPE_Y)],fill=(42,44,48),width=58)
        d.line([(x0,PIPE_Y-10),(x1,PIPE_Y-10)],fill=hi,width=5)
        d.line([(x0,PIPE_Y+14),(x1,PIPE_Y+14)],fill=(70,74,78),width=3)
    # end tanks
    for box,edge,face,hi in (((190,742,286,1018),(126,92,64),(59,52,48),(214,170,122)), ((794,742,890,1018),(76,122,133),(46,60,67),(172,226,233))):
        x0,y0,x1,y1=box
        d.rounded_rectangle((x0+10,y0+10,x1+10,y1+10),radius=28,fill=(8,10,12))
        d.rounded_rectangle(box,radius=28,fill=face,outline=edge,width=6)
        d.line([(x0+16,y0+10),(x1-16,y0+10)],fill=hi,width=3)
        for yy in (776,984):
            d.ellipse((x0+18,yy-14,x0+46,yy+14),fill=(55,52,50),outline=edge,width=3)
            d.ellipse((x1-46,yy-14,x1-18,yy+14),fill=(55,52,50),outline=edge,width=3)
    # main core block
    x0,y0,x1,y1=CORE
    d.rounded_rectangle((x0+14,y0+14,x1+14,y1+14),radius=30,fill=(7,10,12))
    d.rounded_rectangle(CORE,radius=30,fill=(49,60,71),outline=(141,160,173),width=6)
    d.rounded_rectangle((255,670,825,1090),radius=22,fill=(24,30,37),outline=(102,119,132),width=3)
    # fins
    for xx in range(268,816,14):
        d.line([(xx,676),(xx,1084)],fill=(78,97,110),width=4)
        d.line([(xx+2,676),(xx+2,1084)],fill=(132,152,168),width=1)
    # charge channels
    for j in range(CHANNELS):
        cy=channel_center(j)
        d.rounded_rectangle((CHANNEL_X0,cy-CH_H//2,CHANNEL_X1,cy+CH_H//2),radius=12,fill=(17,20,24),outline=(88,101,116),width=2)
    # labels
    d.rounded_rectangle((62,1175,336,1238),radius=16,fill=(41,32,28),outline=(123,87,63),width=2)
    fitted_text(d,'HOT AIR FROM TURBO',(80,1188,319,1224),preferred=24,minimum=20,color=(224,163,114),medium=True)
    d.rounded_rectangle((730,1175,1018,1238),radius=16,fill=(22,44,51),outline=(62,136,156),width=2)
    fitted_text(d,'COOL AIR TO ENGINE',(744,1188,1004,1224),preferred=24,minimum=20,color=(120,232,242),medium=True)
    d.rounded_rectangle((357,480,726,548),radius=18,fill=(30,45,53),outline=(85,129,147),width=2)
    fitted_text(d,'INTERCOOLER CORE',(375,493,708,534),preferred=31,minimum=23,color=(178,228,242),bold=True)
    d.rounded_rectangle((382,1270,700,1336),radius=18,fill=(35,33,30),outline=(107,92,68),width=2)
    fitted_text(d,'HEAT TO FINS',(401,1287,682,1324),preferred=31,minimum=24,color=(217,206,174),bold=True)
    return im
BASE_SCENE=make_base_scene()

# Simple path for hot/cool charge stream
HOT_TOTAL=(LEFT_PIPE_X1-LEFT_PIPE_X0)+36+CHANNEL_LEN+(RIGHT_PIPE_X1-RIGHT_PIPE_X0)

def hot_pos(s, channel_idx=3):
    cy=channel_center(channel_idx)
    if s < (LEFT_PIPE_X1-LEFT_PIPE_X0):
        return LEFT_PIPE_X0+s, PIPE_Y
    s -= (LEFT_PIPE_X1-LEFT_PIPE_X0)
    if s < 36:
        return lerp(LEFT_PIPE_X1, CHANNEL_X0, s/36), lerp(PIPE_Y, cy, s/36)
    s -= 36
    if s < CHANNEL_LEN:
        return CHANNEL_X0+s, cy
    s -= CHANNEL_LEN
    if s < 36:
        return lerp(CHANNEL_X1, RIGHT_PIPE_X0, s/36), lerp(cy, PIPE_Y, s/36)
    s -= 36
    return RIGHT_PIPE_X0 + min(s,(RIGHT_PIPE_X1-RIGHT_PIPE_X0)), PIPE_Y

def draw_charge_flow(d,t,hot_focus,cool_focus,phase_i):
    # many particles across several channels to imply the whole core is flowing
    for ch in range(CHANNELS):
        ch_bias=0.06*math.sin(ch*0.8+t*0.7)
        for k in range(12):
            lead=(t*120 + k*(HOT_TOTAL/12) + ch*37) % HOT_TOTAL
            x,y=hot_pos(lead,ch)
            progress=clamp((x-CHANNEL_X0)/(CHANNEL_X1-CHANNEL_X0)) if CHANNEL_X1!=CHANNEL_X0 else 0
            # hotter on left, cooler on right; in later stages cooling becomes stronger
            cool_strength=0.25+0.70*cool_focus
            thermal=clamp(progress*cool_strength + ch_bias + (0.12 if phase_i>=4 else 0.0),0,1)
            col=mix(AMBER,TEAL,thermal)
            r=3.2 + (k%3)*0.7
            d.ellipse((x-r,y-r,x+r,y+r),fill=col)
            if k%4==0:
                d.ellipse((x-1.3,y-1.3,x+1.3,y+1.3),fill=(247,244,214))
    # subtle hot glow at the inlet tank and cool glow at outlet tank
    d.ellipse((150,790,300,970),fill=(*AMBER,int(12+hot_focus*32)))
    d.ellipse((782,790,930,970),fill=(*TEAL,int(10+cool_focus*28)))

def draw_ambient_air(d,t,focus):
    # vertical blue arrows sweeping through fins continuously
    for lane in range(10):
        x=284 + lane*56 + 8*math.sin(lane*0.7)
        for k in range(4):
            y=560 + ((t*145 + lane*22 + k*145) % 620)
            alpha=int(90+120*focus)
            col=(80,215,255)
            d.line([(x,y-22),(x,y+16)],fill=col,width=4)
            d.polygon([(x,y+24),(x-9,y+8),(x+9,y+8)],fill=col)
    if focus>0.55:
        # a few cool stream accents entering above the core
        for lane in range(5):
            x=335+lane*105
            y=610+7*math.sin(t*1.8+lane)
            d.line([(x,y-72),(x,y-22)],fill=BLUE2,width=6)
            d.polygon([(x,y-6),(x-10,y-26),(x+10,y-26)],fill=BLUE2)

def draw_heat_transfer(d,t,focus):
    # Warm highlight that moves from channels into fins.
    if focus<=0.05:
        return
    env=smoothstep(focus)
    for ch in range(CHANNELS):
        cy=channel_center(ch)
        x=360 + ((t*42 + ch*51) % 320)
        for i in range(5):
            xx=x+i*18
            d.line([(xx,cy-24),(xx,cy-56)],fill=(255,186,92,int(70*env)),width=3)
    # warm core pulse
    for xx in range(286,794,56):
        strength=0.45+0.55*math.sin(t*2.0+xx*0.03)
        col=(255,180,92) if strength>0 else (120,150,170)
        d.line([(xx,676),(xx,1084)],fill=col,width=2)

def frame(t):
    i,p=phase(t)
    im=BG_PANELS[i].copy().convert('RGBA')
    im.alpha_composite(BASE_SCENE)
    dyn=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(dyn)
    hot_focus=1.0 if i==1 else 0.72 if i in (2,5) else 0.38
    core_focus=1.0 if i==2 else 0.65 if i in (3,5) else 0.32
    air_focus=1.0 if i==3 else 0.55 if i in (4,5) else 0.20
    cool_focus=1.0 if i==4 else 0.70 if i==5 else 0.35
    draw_charge_flow(d,t,hot_focus,cool_focus,i)
    draw_heat_transfer(d,t,core_focus*(0.5+0.5*math.sin(t*1.1)**2))
    draw_ambient_air(d,t,air_focus)
    # stage progress fill in reserved tabs
    if 1 <= i <= 4:
        xx=55+(i-1)*244
        d.rounded_rectangle((xx+7,412,xx+7+216*p,422),radius=4,fill=TABS[i-1][1])
    # labels fit in their reserved areas and are checked before render
    if i in (1,4):
        col=AMBER if i==1 else TEAL
        text='HOTTER / LESS DENSE' if i==1 else 'COOLER / DENSER'
        d.rounded_rectangle((379,575,703,630),radius=16,fill=(29,34,40),outline=col,width=2)
        fitted_text(d,text,(395,588,686,617),preferred=24,minimum=20,color=col,medium=True)
    im.alpha_composite(dyn)
    return im.convert('RGB')

def audio_synth(path):
    sr=48000
    tt=np.arange(int(TOTAL*sr),dtype=np.float64)/sr
    rng=np.random.default_rng(113)
    noise=rng.standard_normal(tt.size)
    soft=np.convolve(noise,np.ones(121)/121,mode='same')
    whoosh=.08*soft
    fan=.05*np.sin(2*math.pi*82*tt)+.025*np.sin(2*math.pi*164*tt)
    tone=.03*np.sin(2*math.pi*(240+20*np.sin(tt*0.5))*tt)
    audio=whoosh+fan+tone
    for moment in CUTS[1:-1]:
        start=int((moment-.06)*sr)
        end=min(len(audio),start+int(.18*sr))
        if start<0: continue
        u=np.arange(end-start)/sr
        audio[start:end]+=0.07*np.sin(2*math.pi*320*u)*np.exp(-18*u)
    audio*=np.minimum(1,tt/.5)
    audio*=np.minimum(1,(TOTAL-tt)/.6)
    audio=np.clip(audio,-0.92,.92)
    pcm=(audio*32767).astype(np.int16)
    with wave.open(path,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())

def make_video(output,audio_path,limit=None):
    limit=limit or FRAMES
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',audio_path,'-map','0:v:0','-map','1:a:0','-c:a','aac','-b:a','160k','-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart','-t',str(limit/FPS),output]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for j in range(limit):
            proc.stdin.write(np.asarray(frame(j/FPS),dtype=np.uint8).tobytes())
        proc.stdin.close(); proc.stdin=None
        err=proc.communicate()[1]
        if proc.returncode!=0: raise RuntimeError(err.decode()[-2000:])
    except BaseException:
        proc.kill(); raise

def save_storyboard(path):
    times=(0.,4.8,9.6,15.2,20.7,24.8)
    ims=[frame(t).resize((180,320)) for t in times]
    canvas=Image.new('RGB',(580,670),(14,18,25))
    pos=[(10,10),(200,10),(390,10),(10,340),(200,340),(390,340)]
    for im,p in zip(ims,pos): canvas.paste(im,p)
    canvas.save(path,quality=92)

def check_layout():
    # Text spans were measured at scene construction; validate all stage-specific labels.
    assert len(TEXT_QA) >= 6*(4+3)+4, len(TEXT_QA)
    for q in TEXT_QA:
        b=q['bbox']; r=q['safe_rect']
        assert b[0]>=r[0] and b[1]>=r[1] and b[2]<=r[2] and b[3]<=r[3], q
    # Verify all dynamic callouts once in their actual frames.
    for t in (4.8,20.7):
        frame(t)
    return {'checked_labels':len(TEXT_QA),'minimum_font_px':min(x['font_px'] for x in TEXT_QA)}

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',default='/mnt/data/V9_0_Intercooler_Premium_2_5D_Ekrem_Gokberk_Iscan.mp4')
    ap.add_argument('--audio',default='/mnt/data/v90_intercooler_audio.wav')
    ap.add_argument('--stills',action='store_true')
    a=ap.parse_args()
    print('LAYOUT_QA_PASS',check_layout(),flush=True)
    if a.stills:
        save_storyboard(os.path.join(os.environ.get('EGI_OUTPUT_DIR','/tmp'),'EGI_Intercooler_Storyboard.jpg'))
    else:
        audio_synth(a.audio)
        make_video(a.output,a.audio)
        save_storyboard(os.path.join(os.environ.get('EGI_OUTPUT_DIR','/tmp'),'EGI_Intercooler_Storyboard.jpg'))