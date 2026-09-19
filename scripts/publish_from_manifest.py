#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone,timedelta
m=json.load(open("manifest.json"))
shorts=m.get("shorts",[])
if len(shorts)!=5: raise SystemExit("manifest must contain exactly 5 shorts")
# 10:00,12:00,15:00,16:00,17:00 Istanbul = UTC+3
hours=[7,9,12,13,14]
day=m["date"]
for i,(item,h) in enumerate(zip(shorts,hours),1):
    title=item["title"]
    desc=item.get("description","Solve the visual puzzle before the reveal. #visualpuzzle #brainteaser #shorts")
    tags=item.get("tags",["visual puzzle","brain teaser","shorts"])
    marker="AUTO-SHORT:%s:%s:%s"%(day,i,item.get("variant","v"))
    pub="%sT%02d:00:00Z"%(day,h)
    cmd=[sys.executable,"scripts/youtube_upload.py",item["file"],title,desc,marker,pub]+tags
    print("Scheduling",i,title,"for",pub,flush=True)
    subprocess.run(cmd,check=True)
