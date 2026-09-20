#!/usr/bin/env python3
import os,json,urllib.parse,urllib.request,datetime

def post(url,data):
    req=urllib.request.Request(url,data=urllib.parse.urlencode(data).encode())
    return json.load(urllib.request.urlopen(req))
def get(url,token):
    req=urllib.request.Request(url,headers={"Authorization":"Bearer "+token})
    return json.load(urllib.request.urlopen(req))
tok=post("https://oauth2.googleapis.com/token",{
 "client_id":os.environ["YOUTUBE_CLIENT_ID"],"client_secret":os.environ["YOUTUBE_CLIENT_SECRET"],
 "refresh_token":os.environ["YOUTUBE_REFRESH_TOKEN"],"grant_type":"refresh_token"})["access_token"]
today=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).date()
end=today-datetime.timedelta(days=1); start=end-datetime.timedelta(days=6)
metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained,subscribersLost"
params={"ids":"channel==MINE","startDate":str(start),"endDate":str(end),"metrics":metrics,"dimensions":"video","sort":"-views","maxResults":"50"}
url="https://youtubeanalytics.googleapis.com/v2/reports?"+urllib.parse.urlencode(params)
d=get(url,tok)
cols=[x["name"] for x in d.get("columnHeaders",[])]
rows=[dict(zip(cols,r)) for r in d.get("rows",[])]
out={"period":{"start":str(start),"end":str(end)},"rows":rows}
json.dump(out,open("analytics_preflight.json","w"),indent=2)
print("ANALYTICS_PREFLIGHT_OK",str(start),str(end),"videos",len(rows))
for r in rows[:10]: print(json.dumps(r,ensure_ascii=False))
