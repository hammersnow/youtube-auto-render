#!/usr/bin/env python3
"""Upload only verified EGI videos; never fall back to visual-puzzle content."""
import hashlib, json, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

IST=timezone(timedelta(hours=3))
m=json.loads(Path("manifest.json").read_text(encoding="utf-8"))
if m.get("brand")!="EGI" or m.get("strategy")!="egi-premium-v16" or m.get("publish_enabled") is not True:
    raise SystemExit("Refusing non-EGI or disabled manifest")
day=datetime.strptime(m["date"],"%Y-%m-%d").date()
now=datetime.now(IST)
if day!=now.date(): raise SystemExit("Refusing stale/future EGI manifest")
episodes=m.get("shorts",[])
if not 1<=len(episodes)<=2: raise SystemExit("EGI allows 1..2 unique Shorts/day")
if len(set(x.get("episode_id") for x in episodes))!=len(episodes): raise SystemExit("Repeated episode ID")
if len(set(x.get("sha256") for x in episodes))!=len(episodes): raise SystemExit("Identical video files")
slots=[(15,0)] if len(episodes)==1 else [(12,0),(17,0)]
cursor=now+timedelta(minutes=15)
for idx,(item,(hour,minute)) in enumerate(zip(episodes,slots),1):
    path=Path(item["file"])
    if not path.is_file() or path.suffix!=".mp4": raise SystemExit("Missing MP4 "+str(path))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item["sha256"]: raise SystemExit("MP4 checksum mismatch "+str(path))
    slot=datetime(day.year,day.month,day.day,hour,minute,tzinfo=IST)
    pub=max(slot,cursor)
    if pub==cursor:
        pub=(pub+timedelta(minutes=(-pub.minute)%5)).replace(second=0,microsecond=0)
    cursor=pub+timedelta(minutes=60)
    marker="EGI-EPISODE:"+item["episode_id"]+"\nAUTO-SHA256:"+item["sha256"]
    pub_utc=pub.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print("EGI_PUBLISH_SCHEDULE:",item["episode_id"],pub.isoformat(),flush=True)
    subprocess.run([sys.executable,"scripts/youtube_upload.py",str(path),item["title"],item["description"],marker,pub_utc,*item["tags"]],check=True)
