#!/usr/bin/env python3
"""Consume only independently reviewed exact media from this repository.
No YouTube credentials or uploads here. Never replace an archived approved asset.
"""
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

REPO = "hammersnow/youtube-auto-render"
RENDERER = "premium-approved-v2"
SAFE_ID = re.compile(r"egi-[a-z0-9]+(?:-[a-z0-9]+)*")
SAFE_MP4 = re.compile(r"EGI_[A-Za-z0-9_]+\.mp4")
SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
SHA = re.compile(r"[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
GATES = ("full_visual_review", "full_audio_review", "technical_accuracy",
         "mobile_readability", "originality", "rights_cleared",
         "no_p0_p1", "premium_v2_or_better")

def validate_entry(e):
    a = e["approved_asset"]
    assert isinstance(e["id"], str) and SAFE_ID.fullmatch(e["id"])
    assert a["tag"] == "egi-approved-" + e["id"]
    assert isinstance(a["file"], str) and SAFE_MP4.fullmatch(a["file"])
    assert isinstance(a["sha256"], str) and SHA.fullmatch(a["sha256"])
    assert isinstance(a["source_commit"], str) and COMMIT.fullmatch(a["source_commit"])
    assert type(a["source_run"]) is int and a["source_run"] > 0
    assert type(a["source_artifact"]) is int and a["source_artifact"] > 0
    assert isinstance(a["artifact_name"], str) and SAFE_NAME.fullmatch(a["artifact_name"])
    assert type(a["duration_seconds"]) is int and 5 <= a["duration_seconds"] <= 180
    assert a["fps"] == 30
    assert a["width"] == 1080 and a["height"] == 1920
    assert a["native_frames"] == a["duration_seconds"] * 30
    rev = a["review"]
    assert rev["status"] == "approved"
    assert rev["authority"] in ("user", "reviewer-integrator")
    assert rev["reviewed_sha256"] == a["sha256"]
    assert rev["source_commit"] == a["source_commit"]
    assert all(rev.get(k) is True for k in GATES)
    assert isinstance(rev["evidence"], str) and len(rev["evidence"].strip()) >= 40
    return a

def run(*args):
    subprocess.run(args, check=True)

def gh_json(*args):
    return json.loads(subprocess.check_output(["gh", *args], text=True))

def verify_file(path, a):
    assert path.is_file() and path.stat().st_size > 200000, path
    with path.open("rb") as f:
        assert hashlib.file_digest(f, "sha256").hexdigest() == a["sha256"], "approved SHA mismatch"
    p = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_format",
                                           "-show_streams", "-of", "json", str(path)], text=True))
    v = [s for s in p["streams"] if s["codec_type"] == "video"]
    au = [s for s in p["streams"] if s["codec_type"] == "audio"]
    assert len(v) == len(au) == 1
    v = v[0]
    assert (v["codec_name"], v["width"], v["height"], v["avg_frame_rate"],
            v["r_frame_rate"], int(v["nb_frames"])) == ("h264", 1080, 1920,
                                                       "30/1", "30/1", a["native_frames"])
    assert au[0]["codec_name"] == "aac"
    assert abs(float(p["format"]["duration"]) - a["duration_seconds"]) < .17
    run("ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-")
    return {"seconds": float(p["format"]["duration"]), "frame_rate": "30/1", "audio": "aac"}

def archive_and_get(e, target):
    a = validate_entry(e)
    # A previously archived exact release is reusable after the short-lived artifact expires.
    # Distinguish missing release (HTTP 404) from other API errors.
    q = subprocess.run(["gh", "api", f"repos/{REPO}/releases/tags/{a['tag']}"],
                       text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if q.returncode == 0:
        rel = json.loads(q.stdout)
        assert not rel["draft"] and rel["tag_name"] == a["tag"]
        assert [x["name"] for x in rel["assets"]] == [a["file"]], "unexpected archive contents"
        run("gh", "release", "download", a["tag"], "--repo", REPO,
            "--pattern", a["file"], "--output", str(target))
        return verify_file(target, a)
    if "HTTP 404" not in q.stderr:
        raise RuntimeError("Archive lookup failed: " + q.stderr.strip())
    # First archival must bind artifact ID, successful run and exact source commit.
    r = gh_json("api", f"repos/{REPO}/actions/runs/{a['source_run']}")
    assert r["head_sha"] == a["source_commit"] and r["conclusion"] == "success"
    art = gh_json("api", f"repos/{REPO}/actions/artifacts/{a['source_artifact']}")
    assert art["name"] == a["artifact_name"] and art["expired"] is False
    assert art["workflow_run"]["id"] == a["source_run"]
    assert art["workflow_run"]["head_sha"] == a["source_commit"]
    # gh run download selects by exact name within the pinned successful run.
    with tempfile.TemporaryDirectory(prefix="egi-approved-") as d:
        run("gh", "run", "download", str(a["source_run"]), "--repo", REPO,
            "--name", a["artifact_name"], "--dir", d)
        p = Path(d) / a["file"]
        media = verify_file(p, a)
        # Release is immutable by policy: no clobber, no deletion, no replacing assets.
        run("gh", "release", "create", a["tag"], str(p), "--repo", REPO,
            "--target", a["source_commit"], "--latest=false",
            "--title", "EGI approved " + e["id"],
            "--notes", "Exact reviewed SHA256: " + a["sha256"] +
            "\nSource run: " + str(a["source_run"]) + "\n" + a["review"]["evidence"])
        # Source has already passed full decode; copy bytes unchanged.
        import shutil
        shutil.copyfile(p, target)
        assert target.read_bytes() == p.read_bytes()
        return media
