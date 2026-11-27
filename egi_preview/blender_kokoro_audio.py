"""CPU Kokoro narration and fixed-safe-area captions; no paid inference API."""
import json, subprocess, wave, os
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
from kokoro import KPipeline
from PIL import Image, ImageDraw, ImageFont
R=24000
CUES=[
(0,3,"Wheels keep the motor turning.","WHEELS KEEP TURNING"),
(3,6,"Braking makes it a generator.","MOTOR BECOMES GENERATOR"),
(6,10,"A rotating magnetic field induces alternating current.","THREE-PHASE AC"),
(10,13,"Power electronics convert A C to D C.","AC BECOMES DC"),
(13,16,"Some energy returns to the battery.","ENERGY RETURNS TO BATTERY")]
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
# Each original 3D frame is retained; captions stay in fixed mobile-safe bands.
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def center(draw,txt,y,size,col,font=bold):
    f=ImageFont.truetype(font,size)
    while draw.textlength(txt,font=f)>800:
        size-=1;f=ImageFont.truetype(font,size)
    draw.text((540,y),txt,font=f,fill=col,anchor='mm')
files=sorted(Path('frames').glob('f_*.png'));assert len(files)==192,len(files)
Path('composed').mkdir(exist_ok=True)
for i,p in enumerate(files):
    im=Image.open(p).convert('RGB').resize((1080,1920),Image.Resampling.LANCZOS)
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,1080,240),fill='#0b1624')
    d.rectangle((0,1620,1080,1920),fill='#0b1624')
    center(d,'EGI  /  CURIOSITY IN MOTION',70,30,'#64e0e0')
    center(d,'BRAKING THAT RECHARGES',151,56,'#f4f8fb')
    t=i/12
    j=next(k for k,(a,b,*_) in enumerate(CUES) if a<=t<b)
    center(d,CUES[j][3],1670,43,'#f4f8fb')
    center(d,'SIMPLIFIED 3D SCHEMATIC',1747,26,'#a7bfd0',regular)
    center(d,'Ekrem Gökberk İşcan',1804,25,'#a7bfd0',regular)
    im.save(f'composed/{i:04d}.png')
run('ffmpeg','-y','-v','error','-framerate','12','-i','composed/%04d.png','-i','preview/narration.wav','-vf','fps=24','-c:v','libx264','-crf','19','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart','-t','16','preview/EGI_Blender_Kokoro_Regenerative_Braking.mp4')
