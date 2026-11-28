"""CPU Kokoro narration and fixed-safe-area captions; no paid inference API."""
import json, subprocess, wave, os
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
from kokoro import KPipeline
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R=24000
CUES=[
(0,3,"A laser sends light into a glass fiber.","ELECTRIC SIGNAL TO LIGHT"),
(3,6,"The core has a higher refractive index than the cladding.","CORE AND CLADDING"),
(6,10,"At a grazing angle, total internal reflection keeps light inside.","TOTAL INTERNAL REFLECTION"),
(10,13,"Light pulses carry information through the fiber.","LIGHT PULSES CARRY DATA"),
(13,16,"A photodiode turns the light back into an electrical signal.","LIGHT TO ELECTRIC SIGNAL")]
def run(*args):subprocess.run(args,check=True)
torch.set_num_threads(min(4,os.cpu_count() or 1))
pipe=KPipeline(lang_code='a',device='cpu',repo_id='hexgrad/Kokoro-82M')
mix=np.zeros(R*16,dtype=np.float32);meta=[]
for i,(start,end,words,caption) in enumerate(CUES):
    chunks=[np.asarray(a.detach().cpu() if hasattr(a,'detach') else a,dtype=np.float32) for _,_,a in pipe(words,voice='af_heart',speed=1.)]
    assert chunks,words
    y=np.concatenate(chunks)
    available=end-start-.20
    if len(y)>available*R:
        sf.write(f'preview/cue-{i}.wav',y,R)
        tempo=len(y)/R/available
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',f'preview/cue-{i}.wav','-af',f'atempo={tempo:.6f}','-f','f32le','-ar',str(R),'-ac','1','-'])
        y=np.frombuffer(raw,dtype='<f4')
    assert len(y)<=(end-start-.08)*R,(words,len(y)/R)
    assert np.max(np.abs(y))>.01,words
    pos=int((start+.05)*R)
    mix[pos:pos+len(y)]+=y*.87
    meta.append({'start':start,'end':end,'speech_seconds':len(y)/R,'text':words})
sf.write('preview/narration.wav',np.clip(mix,-1,1),R)
Path('preview/narration.json').write_text(json.dumps(meta,indent=2))
# Tracked screen-space labels use the actual camera/world projection.
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def center(d,txt,y,size,col,font=bold):
    f=ImageFont.truetype(font,size)
    while d.textlength(txt,font=f)>820:
        size-=1;f=ImageFont.truetype(font,size)
    d.text((510,y),txt,font=f,fill=col,anchor='mm')
font=ImageFont.truetype(bold,35)
def tag(d,text,anchor,y,align):
    ax,ay=anchor
    w=int(d.textlength(text,font=font))+40;h=62
    x=54 if align=='left' else 954-w
    cy=y+h//2
    edge=x+w if ax>x+w else x if ax<x else max(x+12,min(x+w-12,ax))
    sy=cy if ax<x or ax>x+w else (y+h if ay>cy else y)
    joint=(edge+(18 if ax>edge else -18),sy)
    pts=[(edge,sy),joint,(ax,ay)]
    d.line(pts,fill='#08131f',width=9,joint='curve')
    d.line(pts,fill='#75e6e5',width=3,joint='curve')
    d.ellipse((ax-8,ay-8,ax+8,ay+8),fill='#0b1624',outline='#75e6e5',width=3)
    d.rounded_rectangle((x,y,x+w,y+h),radius=13,fill='#142b3c',outline='#75e6e5',width=2)
    d.text((x+20,cy),text,font=font,fill='#f3fbfc',anchor='lm')
frames=sorted(Path('frames').glob('f_*.png'))
preflight=os.environ.get('EGI_RENDER_MODE','preflight')=='preflight'
assert len(frames)==(5 if preflight else 480),len(frames)
data=json.loads(Path('preview/anchors.json').read_text())
Path('composed').mkdir(exist_ok=True)
for p in frames:
    frame=int(p.stem.split('_')[1])
    info=data[str(frame)]
    im=Image.open(p).convert('RGB')
    assert im.size==(1080,1920),im.size
    box=info['focus'];mask=Image.new('L',im.size,65)
    dm=ImageDraw.Draw(mask)
    dm.rounded_rectangle((max(0,box[0]-100),max(0,box[1]-100),min(1080,box[2]+100),min(1920,box[3]+100)),radius=110,fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(115))
    darker=Image.blend(im,Image.new('RGB',im.size,'#091523'),.34)
    im=Image.composite(im,darker,mask)
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,1080,180),fill='#0b1624')
    d.rectangle((0,1530,1080,1920),fill='#0b1624')
    center(d,'EGI  /  CURIOSITY IN MOTION',62,28,'#64e0e0')
    center(d,'HOW FIBER OPTICS WORK',126,51,'#f4f8fb')
    if info['settled']:
        for k,item in enumerate(sorted(info['labels'],key=lambda x:x['point'][1])):
            tag(d,item['text'],item['point'],220 if k==0 else 1410,'left' if k==0 else 'right')
    center(d,CUES[info['shot']][3],1592,40,'#f4f8fb')
    center(d,'SIMPLIFIED 3D SCHEMATIC',1660,26,'#a7bfd0',regular)
    center(d,'Ekrem Gökberk İşcan',1712,25,'#a7bfd0',regular)
    if preflight:im.save(f'preview/v2-frame-{frame:04d}.jpg',quality=96)
    else:im.save(f'composed/{frame-1:04d}.png')
if not preflight:
    run('ffmpeg','-y','-v','error','-framerate','30','-i','composed/%04d.png','-i','preview/narration.wav','-c:v','libx264','-crf','17','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-t','16','preview/EGI_Fiber_Optics_V2.mp4')
