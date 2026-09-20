#!/usr/bin/env python3
import os,json,urllib.parse,urllib.request,datetime

def post(url,data):
    req=urllib.request.Request(url,data=urllib.parse.urlencode(data).encode())
    return json.load(urllib.request.urlopen(req))
def get(url,token):
    req=urllib.request.Request(url,headers={"Authorization":"Bearer "+token})
    return json.load(urllib.request.urlopen(req))
token=post("https://oauth2.googleapis.com/token",{
 "client_id":os.environ["YOUTUBE_CLIENT_ID"],"client_secret":os.environ["YOUTUBE_CLIENT_SECRET"],
 "refresh_token":os.environ["YOUTUBE_REFRESH_TOKEN"],"grant_type":"refresh_token"})["access_token"]

# Fresh Data API counters for the authenticated channel's newest videos.
search=get("https://www.googleapis.com/youtube/v3/search?"+urllib.parse.urlencode({
 "part":"snippet","forMine":"true","type":"video","order":"date","maxResults":"25"}),token)
ids=[x["id"]["videoId"] for x in search.get("items",[])]
videos=[]
if ids:
    vd=get("https://www.googleapis.com/youtube/v3/videos?"+urllib.parse.urlencode({
      "part":"snippet,statistics,contentDetails","id":",".join(ids)}),token)
    videos=vd.get("items",[])

# Analytics: ask per video for last 14 completed calendar days.
tz=datetime.timezone(datetime.timedelta(hours=3))
today=datetime.datetime.now(tz).date(); end=today-datetime.timedelta(days=1); start=end-datetime.timedelta(days=13)
metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained,subscribersLost"
q={"ids":"channel==MINE","startDate":str(start),"endDate":str(end),"metrics":metrics,
   "dimensions":"video","sort":"-views","maxResults":"50"}
an=get("https://youtubeanalytics.googleapis.com/v2/reports?"+urllib.parse.urlencode(q),token)
cols=[h["name"] for h in an.get("columnHeaders",[])]
arows={r[0]:dict(zip(cols,r)) for r in an.get("rows",[])}
print("FRESH_VIDEO_DATA")
for v in videos:
    vid=v["id"]; s=v["snippet"]; st=v.get("statistics",{})
    print(json.dumps({"videoId":vid,"title":s.get("title"),"publishedAt":s.get("publishedAt"),
      "views":st.get("viewCount"),"likes":st.get("likeCount"),"comments":st.get("commentCount"),
      "analytics":arows.get(vid)},ensure_ascii=False))
print("ANALYTICS_PERIOD",start,end,"ROWS",len(arows))
