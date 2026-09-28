import json, time, base64, urllib.parse, datetime, requests
CID = "pmagYZKQF6mRtNmtRzPkXSQJ76jYHLN8"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
S = requests.Session(); S.headers.update({"User-Agent": UA})

t = S.get("https://api-v2.soundcloud.com/users/1645780733/tracks",
          params={"client_id": CID, "limit": 1}).json()["collection"][0]
prog = [x for x in t["media"]["transcodings"] if x["format"]["protocol"] == "progressive"][0]
fresh = S.get(prog["url"], params={"client_id": CID}).json()["url"]

print("  fresh host      :", fresh.split("/")[2])
r = S.get(fresh, headers={"Range": "bytes=0-999"}, timeout=25)
print(f"  FRESH url       -> {r.status_code}  {len(r.content)} bytes")

old = json.load(open("data/catalogue.json", encoding="utf-8"))["tracks"][0]["stream"]
r2 = S.get(old, headers={"Range": "bytes=0-999"}, timeout=25)
print(f"  BAKED url       -> {r2.status_code}")

q = urllib.parse.parse_qs(urllib.parse.urlparse(fresh).query)
pol = q.get("Policy", [""])[0]
p = json.loads(base64.b64decode(pol + "=" * (-len(pol) % 4)))
cond = p["Statement"][0]["Condition"]
print("  policy keys     :", list(cond.keys()))
for k, v in cond.items():
    if "EpochTime" in str(v):
        for kk, vv in v.items():
            t2 = int(vv)
            delta = t2 - int(time.time())
            print(f"    {kk:<15} {t2}  {datetime.datetime.utcfromtimestamp(t2):%Y-%m-%d %H:%M:%S}  ({delta/3600:+.2f} h)")
