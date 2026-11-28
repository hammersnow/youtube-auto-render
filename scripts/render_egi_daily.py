#!/usr/bin/env python3
"""EGI release renderer: curated unique original episodes, no quota filler."""
import argparse, hashlib, json, os, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config/egi_episode_catalog.json"
OUT = ROOT / "outputs/egi_daily"
IST = timezone(timedelta(hours=3))
STRATEGY = "egi-premium-v16"
from egi_approved_assets import RENDERER, validate_entry, archive_and_get
FILES = {
    "v16-software": "EGI_V16_Software_HTML_CSS_JavaScript_Rich_Animation.mp4",
    "v16-technology": "EGI_V16_Technology_One_Event_One_Callout.mp4",
    "turbo": "EGI_Turbo_Premium_2_5D.mp4",
    "intercooler": "EGI_Intercooler_TextFit_2_5D.mp4",
    "premium-ssd": "EGI_SSD_Wear_Leveling_V16.mp4",
    "premium-heat": "EGI_Heat_Pipe_Phase_Change_V16.mp4",
    "diff-v12": "EGI_V12_Mechanics_Open_Differential_Microanimations.mp4",
    "engine-v88": "EGI_Engine_Four_Stroke_V88.mp4",
    "blender-prebuilt-v2": "EGI_Blender_Kokoro_V2.mp4",
}
DURATIONS = {"v16-software":36, "v16-technology":36, "turbo":26, "intercooler":26, "premium-ssd":32, "premium-heat":32, "diff-v12":36, "engine-v88":26, "blender-prebuilt-v2":16}
FPS = {"v16-software":"30/1","v16-technology":"30/1","turbo":"24/1","intercooler":"24/1", "premium-ssd":"30/1", "premium-heat":"30/1", "diff-v12":"24/1", "engine-v88":"24/1", "blender-prebuilt-v2":"30/1"}

def check_catalog(cat):
    assert cat.get("strategy") == STRATEGY
    assert cat.get("brand") == "EGI"
    assert cat.get("publish_enabled") is True
    assert cat.get("max_daily_shorts") == 2
    seen = set()
    asset_hashes = set()
    for date, episodes in cat["schedule"].items():
        datetime.strptime(date, "%Y-%m-%d")
        assert 1 <= len(episodes) <= 2, (date,len(episodes))
        for e in episodes:
            assert e["renderer"] in FILES or e["renderer"] == RENDERER, e
            assert e["id"] not in seen, "Duplicate episode ID: "+e["id"]
            seen.add(e["id"])
            assert e["title"].endswith("#Shorts")
            assert "#EGI" in e["description"]
            assert len(e["title"]) <= 100
            if e["renderer"] == "blender-prebuilt-v2":
                a=e["approved_asset"]
                assert a["user_approved"] is True and a["tag"] == "egi-approved-regenerative-braking-v2"
                assert a["file"] == FILES[e["renderer"]]
                assert a["sha256"] == "6a1f92a8c5336fe8003de97d70b0403a1a0061f00452d605dd8801eeddef451f"
                assert a["source_commit"] == "0eaa4d08bb2886ebc3d714b98845927033977394"
            elif e["renderer"] == RENDERER:
                a = validate_entry(e)
            if e["renderer"] in ("blender-prebuilt-v2", RENDERER):
                assert a["sha256"] not in asset_hashes, "Repeated approved asset hash"
                asset_hashes.add(a["sha256"])
        names = [e["approved_asset"]["file"] if e["renderer"] == RENDERER else FILES[e["renderer"]] for e in episodes]
        assert len(names) == len(set(names)), "Duplicate daily output filename"
    return seen

def command(e, target):
    renderer = e["renderer"]
    if renderer.startswith("v16-"):
        mode = "software" if renderer.endswith("software") else "technology"
        return [sys.executable, str(ROOT/"egi_preview/egi_v16_rich_resources.py"),
                "--mode", mode]
    if renderer in ("premium-ssd", "premium-heat"):
        return [sys.executable, str(ROOT/"egi_preview/egi_rd_premium_v16.py"),
                "--kind", "ssd" if renderer == "premium-ssd" else "heat",
                "--out", str(OUT)]
    if renderer == "diff-v12":
        return [sys.executable,str(ROOT/"egi_preview/egi_v12_tech_mechanics_connected.py"),
                "--mode","mechanical"]
    if renderer == "engine-v88":
        return [sys.executable,str(ROOT/"egi_preview/egi_engine_v88.py"),
                "--video",str(target),"--audio",str(OUT/"egi_engine_v88.wav")]
    source = "egi_turbo.py" if renderer=="turbo" else "egi_intercooler.py"
    audio = OUT / (renderer+"_original_audio.wav")
    return [sys.executable,str(ROOT/"egi_preview"/source),
            "--output",str(target),"--audio",str(audio)]

def probe(path, renderer):
    raw = subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(path)])
    obj = json.loads(raw)
    videos=[s for s in obj["streams"] if s["codec_type"]=="video"]
    audios=[s for s in obj["streams"] if s["codec_type"]=="audio"]
    assert len(videos)==1 and len(audios)==1, (str(path),len(videos),len(audios))
    v,a=videos[0],audios[0]
    assert (v["codec_name"],v["width"],v["height"],v["r_frame_rate"]) == ("h264",1080,1920,FPS[renderer]),v
    assert a["codec_name"]=="aac",a
    duration=float(obj["format"]["duration"])
    assert abs(duration-DURATIONS[renderer])<=0.17,(str(path),duration)
    assert path.stat().st_size>200000,(str(path),path.stat().st_size)
    return {"seconds":duration,"frame_rate":FPS[renderer],"audio":"aac"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--day",default=datetime.now(IST).strftime("%Y-%m-%d"))
    p.add_argument("--check-only",action="store_true")
    args=p.parse_args()
    cat=json.loads(CATALOG.read_text(encoding="utf-8"))
    check_catalog(cat)
    episodes=cat["schedule"].get(args.day,[])
    if not episodes:
        print("EGI_NO_NEW_EPISODE: "+args.day+"; no repeat uploads")
        return 3
    if args.check_only:
        print("EGI_PLAN_OK",args.day,[e["id"] for e in episodes])
        return 0

    OUT.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ)
    env["EGI_OUTPUT_DIR"]=str(OUT)
    shorts=[]
    for e in episodes:
        target = OUT / (e["approved_asset"]["file"] if e["renderer"] == RENDERER else FILES[e["renderer"]])
        if target.exists(): target.unlink()
        if e["renderer"] == RENDERER:
            m = archive_and_get(e, target)
        elif e["renderer"] == "blender-prebuilt-v2":
            a=e["approved_asset"]
            url="https://github.com/hammersnow/youtube-auto-render/releases/download/"+a["tag"]+"/"+a["file"]
            subprocess.run(["curl","-fL","--retry","4","-o",str(target),url],check=True)
            assert hashlib.sha256(target.read_bytes()).hexdigest()==a["sha256"], "Approved asset hash mismatch"
            subprocess.run(["ffmpeg","-v","error","-i",str(target),"-f","null","-"],check=True)
        else:
            subprocess.run(command(e,target),cwd=ROOT,env=env,check=True)
        if e["renderer"] in ("premium-ssd", "premium-heat"):
            original=OUT/("ssd_premium.mp4" if e["renderer"]=="premium-ssd" else "heat_premium.mp4")
            assert original.is_file(),original
            original.replace(target)
        assert target.is_file(),target
        if e["renderer"] != RENDERER:
            m=probe(target,e["renderer"])
        checksum=hashlib.sha256(target.read_bytes()).hexdigest()
        shorts.append({
           "episode_id":e["id"],"family":e["category"],"file":target.name,
           "title":e["title"],"description":e["description"],
           "tags":e["tags"],"sha256":checksum,
           "duration":round(m["seconds"],3),"video_codec":"h264","audio_codec":"aac",
           "quality_tier":"EGI-Premium-V2-reviewed" if e["renderer"] in (RENDERER,"blender-prebuilt-v2") else "EGI-V16-reviewed","language":"en","watermark":"Ekrem Gökberk İşcan"
        })
    assert len(set(x["sha256"] for x in shorts))==len(shorts),"Same video duplicated"
    manifest={"date":args.day,"brand":"EGI","strategy":STRATEGY,
              "publish_enabled":True,"timezone":"Europe/Istanbul","shorts":shorts}
    (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("EGI_RENDER_OK:",args.day,[(x["episode_id"],x["sha256"][:12]) for x in shorts])
    return 0

if __name__=="__main__":
    sys.exit(main())
