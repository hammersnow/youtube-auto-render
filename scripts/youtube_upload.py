#!/usr/bin/env python3
import os, sys, json, urllib.parse, urllib.request
from pathlib import Path

TOKEN_URL="https://oauth2.googleapis.com/token"
UPLOAD_URL="https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status&uploadType=resumable"

def token():
    data=urllib.parse.urlencode({
      "client_id":os.environ["YOUTUBE_CLIENT_ID"],
      "client_secret":os.environ["YOUTUBE_CLIENT_SECRET"],
      "refresh_token":os.environ["YOUTUBE_REFRESH_TOKEN"],
      "grant_type":"refresh_token"}).encode()
    req=urllib.request.Request(TOKEN_URL,data=data,method="POST")
    return json.load(urllib.request.urlopen(req))["access_token"]

def upload(path,title,description,tags):
    access=token()
    meta={"snippet":{"title":title,"description":description,"tags":tags,"categoryId":"24"},
          "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False}}
    body=json.dumps(meta).encode()
    req=urllib.request.Request(UPLOAD_URL,data=body,method="POST",headers={
      "Authorization":"Bearer "+access,"Content-Type":"application/json; charset=UTF-8",
      "X-Upload-Content-Type":"video/mp4","X-Upload-Content-Length":str(Path(path).stat().st_size)})
    with urllib.request.urlopen(req) as r: location=r.headers["Location"]
    data=Path(path).read_bytes()
    req=urllib.request.Request(location,data=data,method="PUT",headers={"Authorization":"Bearer "+access,"Content-Type":"video/mp4"})
    with urllib.request.urlopen(req) as r: result=json.load(r)
    print(json.dumps({"file":path,"videoId":result.get("id"),"title":title}))
    return result.get("id")

if __name__=="__main__":
    if len(sys.argv)<4: raise SystemExit("usage: youtube_upload.py VIDEO TITLE DESCRIPTION [TAGS...]")
    upload(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4:])
