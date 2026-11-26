"""Offline eSpeak narration; align short cues to scene events, no external service."""
import subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np
RATE=24000
DURATION=16
CUES=[
    (0,3,"The wheels are turning."),
    (3,6,"Braking makes the motor a generator."),
    (6,10,"The rotating magnetic field induces alternating current."),
    (10,13,"Power electronics convert AC to DC."),
    (13,16,"Some energy returns to the battery."),
]
def run(*cmd):
    subprocess.run(cmd,check=True)
def main(visual,output):
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        mix=np.zeros(RATE*DURATION,dtype=np.float32)
        for i,(start,end,text) in enumerate(CUES):
            wav=root/f"{i}.wav"
            run("espeak-ng","-v","en-us","-s","175","-w",str(wav),text)
            with wave.open(str(wav),"rb") as f:
                duration=f.getnframes()/f.getframerate()
            available=end-start-.24
            tempo=max(1.,duration/available)
            raw=subprocess.check_output(["ffmpeg","-v","error","-i",str(wav),"-af",f"atempo={tempo:.5f}","-ar",str(RATE),"-ac","1","-f","s16le","-"])
            samples=np.frombuffer(raw,dtype="<i2").astype(np.float32)/32768
            assert len(samples)<=int((end-start-.1)*RATE),(text,len(samples)/RATE)
            pos=int((start+.1)*RATE)
            mix[pos:pos+len(samples)]+=samples*.74
            print(f"CUE {i+1}: {len(samples)/RATE:.2f}s / {end-start}s")
        with wave.open(str(root/"mix.wav"),"wb") as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE)
            f.writeframes((np.clip(mix,-1,1)*32767).astype("<i2").tobytes())
        run("ffmpeg","-y","-v","error","-i",visual,"-i",str(root/"mix.wav"),"-map","0:v","-map","1:a","-c:v","libx264","-crf","19","-preset","fast","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-movflags","+faststart","-t","16",output)
if __name__=="__main__":
    main(*sys.argv[1:])
