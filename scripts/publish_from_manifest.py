#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=3))
m = json.load(open("manifest.json", encoding="utf-8"))
shorts = m.get("shorts", [])
if not 1 <= len(shorts) <= 5:
    raise SystemExit("manifest must contain between 1 and 5 shorts")

slot_map = {
    1: [(15, 0)],
    2: [(12, 0), (17, 0)],
    3: [(10, 0), (15, 0), (17, 0)],
    4: [(10, 0), (13, 0), (15, 0), (17, 0)],
    5: [(10, 0), (12, 0), (15, 0), (16, 0), (17, 0)],
}
slots = slot_map[len(shorts)]

cfg_path = Path("config/strategy_v7.json")
if m.get("strategy") == "premium-motion-v7" and cfg_path.exists():
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    raw_slots = cfg.get("publish_slots_istanbul", [])
    if len(raw_slots) == len(shorts):
        parsed = []
        for value in raw_slots:
            h, minute = map(int, value.split(":"))
            if not (0 <= h <= 23 and 0 <= minute <= 59):
                raise SystemExit("invalid publish slot: " + value)
            parsed.append((h, minute))
        slots = parsed
        print("Using V7 configured publish slots:", raw_slots, flush=True)

now = datetime.now(IST)
day = datetime.strptime(m["date"], "%Y-%m-%d").date()
targets = [datetime(day.year, day.month, day.day, h, minute, tzinfo=IST) for h, minute in slots]

safe = []
cursor = now + timedelta(minutes=10)
for target in targets:
    chosen = max(target, cursor)
    if chosen == cursor:
        add = (5 - (chosen.minute % 5)) % 5
        chosen = (chosen + timedelta(minutes=add)).replace(second=0, microsecond=0)
    safe.append(chosen)
    cursor = chosen + timedelta(minutes=60)

for i, (item, local_pub) in enumerate(zip(shorts, safe), 1):
    title = item["title"]
    desc = item.get(
        "description",
        "Solve the premium animated visual puzzle before the reveal. #visualpuzzle #brainteaser #shorts",
    )
    tags = item.get("tags", ["visual puzzle", "brain teaser", "shorts"])
    slot_marker = "AUTO-SHORT:%s:%s" % (m["date"], i)
    content_marker = "AUTO-SHA256:%s" % item["sha256"]
    marker = slot_marker + "\n" + content_marker
    pub = local_pub.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print("Scheduling", i, item.get("family", "unknown"), title, "for", local_pub.isoformat(), "(", pub, ")", flush=True)
    cmd = [sys.executable, "scripts/youtube_upload.py", item["file"], title, desc, marker, pub] + tags
    subprocess.run(cmd, check=True)
