#!/usr/bin/env python3
import os,json,urllib.parse,urllib.request,urllib.error

TOKEN_URL="https://oauth2.googleapis.com/token"

def token():
    data=urllib.parse.urlencode({
      "client_id":os.environ["YOUTUBE_CLIENT_ID"],
      "client_secret":os.environ["YOUTUBE_CLIENT_SECRET"],
      "refresh_token":os.environ["YOUTUBE_REFRESH_TOKEN"],
      "grant_type":"refresh_token"}).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request(TOKEN_URL,data=data,method="POST")))["access_token"]

def call(url,a,method="GET"):
    req=urllib.request.Request(url,method=method,headers={"Authorization":"Bearer "+a})
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r) if method=="GET" else None
    except urllib.error.HTTPError as e:
        raise RuntimeError("YouTube API HTTP %s: %s"%(e.code,e.read().decode("utf-8","replace")))

a=token()
# Delete only today's private/scheduled videos created by our automation marker.
q=urllib.parse.urlencode({"part":"snippet","forMine":"true","type":"video","order":"date","maxResults":"25"})
items=call("https://www.googleapis.com/youtube/v3/search?"+q,a).get("items",[])
ids=[x["id"]["videoId"] for x in items]
if not ids:
    print("No videos found"); raise SystemExit(0)
vq=urllib.parse.urlencode({"part":"snippet,status","id":",".join(ids)})
videos=call("https://www.googleapis.com/youtube/v3/videos?"+vq,a).get("items",[])
removed=[]
for v in videos:
    desc=v["snippet"].get("description","")
    status=v.get("status",{})
    if "AUTO-SHORT:2026-09-20:" in desc and status.get("privacyStatus")=="private":
        vid=v["id"]
        call("https://www.googleapis.com/youtube/v3/videos?"+urllib.parse.urlencode({"id":vid}),a,"DELETE")
        removed.append(vid)
        print("DELETED",vid,v["snippet"].get("title"))
print("REMOVED_COUNT",len(removed))
