#!/usr/bin/env python3
"""Read-only gate for EGI's early cron + fallback. Never calls YouTube/GitHub itself.

release exit 0: today's exact approved batch is already uploaded to GitHub Releases.
publisher exit 0: no successful or pending publisher run exists today; safe to dispatch
the existing duplicate-marker-protected publisher once (in GitHub's serial runner).
Other exit codes mean no action; invalid catalog/IO raises and fails CI closed.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=3))
SHA256 = re.compile(r"[0-9a-f]{64}")
SAFE_MP4 = re.compile(r"EGI_[A-Za-z0-9_]+\.mp4")


def release_ready(day, catalog, manifest, assets):
    if not isinstance(catalog, dict) or not isinstance(manifest, dict):
        return False
    episodes = catalog.get("schedule", {}).get(day)
    if not episodes or not 1 <= len(episodes) <= 2:
        return False
    if any(manifest.get(k) != v for k, v in {
        "brand": "EGI",
        "strategy": "egi-premium-v16",
        "publish_enabled": True,
        "date": day,
        "timezone": "Europe/Istanbul",
    }.items()):
        return False
    shorts = manifest.get("shorts")
    if not isinstance(shorts, list) or len(shorts) != len(episodes):
        return False
    if [x.get("episode_id") for x in shorts] != [x.get("id") for x in episodes]:
        return False
    if len({x.get("episode_id") for x in shorts}) != len(shorts):
        return False
    if len({x.get("sha256") for x in shorts}) != len(shorts):
        return False
    files = []
    for row, proposed in zip(shorts, episodes):
        name = row.get("file", "")
        sha = row.get("sha256", "")
        if not isinstance(name, str) or not SAFE_MP4.fullmatch(name):
            return False
        if not isinstance(sha, str) or not SHA256.fullmatch(sha):
            return False
        if row.get("title") != proposed.get("title"):
            return False
        files.append(name)
    if len(set(files)) != len(files):
        return False
    raw_assets = assets.get("assets") if isinstance(assets, dict) else None
    if not isinstance(raw_assets, list):
        return False
    # No orphan assets, missing uploads, or zero-byte videos.
    available = {a.get("name"): a.get("size", 0) for a in raw_assets
                 if isinstance(a, dict)}
    required = set(files + ["manifest.json"])
    if set(available) != required:
        return False
    if available.get("manifest.json", 0) < 150:
        return False
    return all(isinstance(available.get(f), int) and
               available[f] > 200000 for f in files)


def publisher_retry_needed(day, runs):
    """No second dispatch if this day's publisher succeeded or is still running."""
    if not isinstance(runs, list):
        raise ValueError("Invalid GitHub publisher run list")
    for run in runs:
        if not isinstance(run, dict):
            continue
        created = run.get("createdAt")
        if not created:
            continue
        at = datetime.fromisoformat(created.replace("Z", "+00:00"))
        if at.astimezone(IST).date().isoformat() != day:
            continue
        if run.get("conclusion") == "success":
            return False
        if run.get("status") in ("queued", "in_progress", "pending", "requested",
                                 "waiting"):
            return False
    return True


def self_test():
    day = "2026-11-21"
    id1 = "egi-test-unique"
    name = "EGI_Sample_Only.mp4"
    cat = {"schedule": {day: [{"id": id1, "title": "EGI test #Shorts"}]}}
    man = {"date": day, "brand": "EGI", "strategy": "egi-premium-v16",
           "publish_enabled": True, "timezone": "Europe/Istanbul",
           "shorts": [{"episode_id": id1, "file": name,
                       "sha256": "a"*64, "title": "EGI test #Shorts"}]}
    assets = {"assets": [{"name": name, "size": 500000},
                         {"name": "manifest.json", "size": 1200}]}
    assert release_ready(day, cat, man, assets)
    assert not release_ready("2026-11-22", cat, man, assets)
    assert not release_ready(day, cat, dict(man, date="2026-11-20"), assets)
    assert not release_ready(day, cat, dict(man, shorts=[]), assets)
    assert not release_ready(day, cat, man, {"assets": assets["assets"][:1]})
    assert not release_ready(day, cat, man, {"assets": [
        {"name": name, "size": 0}, {"name": "manifest.json", "size": 1200}]})
    assert publisher_retry_needed(day, [])
    today = "2026-11-21T01:00:00Z"  # 04:00 Istanbul
    prev = "2026-11-20T19:00:00Z"   # 22:00 on prior local day
    assert not publisher_retry_needed(day, [
        {"createdAt": today, "conclusion": "success", "status": "completed"}])
    assert not publisher_retry_needed(day, [
        {"createdAt": today, "conclusion": None, "status": "in_progress"}])
    assert publisher_retry_needed(day, [
        {"createdAt": today, "conclusion": "failure", "status": "completed"}])
    assert publisher_retry_needed(day, [
        {"createdAt": prev, "conclusion": "success", "status": "completed"}])
    print("EGI_RELEASE_GATE_SELF_TEST_PASS")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("release")
    r.add_argument("--day", required=True)
    r.add_argument("--catalog", required=True)
    r.add_argument("--manifest", required=True)
    r.add_argument("--assets", required=True)
    u = sub.add_parser("publisher")
    u.add_argument("--day", required=True)
    u.add_argument("--runs", required=True)
    sub.add_parser("self-test")
    args = p.parse_args()
    if args.command == "self-test":
        self_test()
        return 0
    if args.command == "release":
        good = release_ready(args.day,
                             json.loads(Path(args.catalog).read_text()),
                             json.loads(Path(args.manifest).read_text()),
                             json.loads(Path(args.assets).read_text()))
        print("EGI_RELEASE_READY" if good else "EGI_RELEASE_INCOMPLETE_OR_STALE")
        return 0 if good else 1
    due = publisher_retry_needed(args.day, json.loads(Path(args.runs).read_text()))
    print("EGI_PUBLISH_RETRY_NEEDED" if due else "EGI_PUBLISH_ALREADY_OK_OR_RUNNING")
    return 0 if due else 1


if __name__ == "__main__":
    sys.exit(main())
