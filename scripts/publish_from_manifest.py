#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone,timedelta

IST=timezone(timedelta(hours=3))
m=json.load(open("manifest.json"))
shorts=m.get("shorts",[])
if len(shorts)!=5: raise SystemExit("manifest must contain exactly 5 shorts")

# Desired Istanbul slots. If a slot is already past, move it forward while
# preserving spacing instead of sending an invalid/past publishAt.
slots=[(10,0),(12,0),(15,0),(16,0),(17,0)]
now=datetime.now(IST)
day=datetime.strptime(m["date"],"%Y-%m-%d").date()
targets=[datetime(day.year,day.month,day.day,h,minute,tzinfo=IST) for h,minute in slots]

safe=[]
cursor=now+timedelta(minutes=10)
for target in targets:
    chosen=max(target,cursor)
    # round catch-up times to the next 5-minute boundary
    if chosen==cursor:
        add=(5-(chosen.minute%5))%5
        chosen=(chosen+timedelta(minutes=add)).replace(second=0,microsecond=0)
    safe.append(chosen)
    cursor=chosen+timedelta(minutes=60)

for i,(item,local_pub) in enumerate(zip(shorts,safe),1):
    title=item["title"]
    desc=item.get("description","Solve the visual puzzle before the reveal. #visualpuzzle #brainteaser #shorts")
    tags=item.get("tags",["visual puzzle","brain teaser","shorts"])
    slot_marker="AUTO-SHORT:%s:%s"%(m["date"],i)
    content_marker="AUTO-SHA256:%s"%item["sha256"]
    marker=slot_marker+"\n"+content_marker
    pub=local_pub.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print("Scheduling",i,title,"for",local_pub.isoformat(),"(",pub,")",flush=True)
    cmd=[sys.executable,"scripts/youtube_upload.py",item["file"],title,desc,marker,pub]+tags
    subprocess.run(cmd,check=True)
