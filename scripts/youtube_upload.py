#!/usr/bin/env python3
import os,sys,json,urllib.parse,urllib.request,urllib.error
from pathlib import Path
TOKEN_URL="https://oauth2.googleapis.com/token"
UPLOAD_URL="https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status&uploadType=resumable"

def token():
 d=urllib.parse.urlencode({"client_id":os.environ["YOUTUBE_CLIENT_ID"],"client_secret":os.environ["YOUTUBE_CLIENT_SECRET"],"refresh_token":os.environ["YOUTUBE_REFRESH_TOKEN"],"grant_type":"refresh_token"}).encode()
 return json.load(urllib.request.urlopen(urllib.request.Request(TOKEN_URL,data=d,method="POST")))["access_token"]

def api(req):
 try:return urllib.request.urlopen(req)
 except urllib.error.HTTPError as e: raise RuntimeError("YouTube API HTTP %s: %s"%(e.code,e.read().decode("utf-8","replace")))

def upload(p,t,d,tags,m,pub):
 a=token()
 # OAuth token intentionally has youtube.upload only. Duplicate prevention is
 # handled by workflow concurrency/manifest markers instead of search.list,
 # which requires a broader read scope.
 d=d+"\n\n"+m
 s={"privacyStatus":"private" if pub else "public","selfDeclaredMadeForKids":False}
 if pub:s["publishAt"]=pub
 meta={"snippet":{"title":t,"description":d,"tags":tags,"categoryId":"24"},"status":s}
 req=urllib.request.Request(UPLOAD_URL,data=json.dumps(meta).encode(),method="POST",headers={"Authorization":"Bearer "+a,"Content-Type":"application/json; charset=UTF-8","X-Upload-Content-Type":"video/mp4","X-Upload-Content-Length":str(Path(p).stat().st_size)})
 with api(req) as r:loc=r.headers["Location"]
 with api(urllib.request.Request(loc,data=Path(p).read_bytes(),method="PUT",headers={"Authorization":"Bearer "+a,"Content-Type":"video/mp4"})) as r:res=json.load(r)
 print(json.dumps({"file":p,"videoId":res.get("id"),"title":t,"publishAt":pub}))

if __name__=="__main__":
 if len(sys.argv)<6:raise SystemExit("usage: VIDEO TITLE DESC MARKER PUBLISH_AT [TAGS...]")
 upload(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[6:],sys.argv[4],None if sys.argv[5]=="-" else sys.argv[5])
