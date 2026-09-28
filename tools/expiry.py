import json, time, urllib.parse, datetime, requests
d = json.load(open("data/catalogue.json", encoding="utf-8"))
u = d["tracks"][0]["stream"]
q = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
print("now (UTC)      :", datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
print("Epoch          :", int(time.time()))
for k in ("Expires", "expires", "Key-Pair-Id", "Signature"):
    if k in q:
        v = q[k][0]
        if k.lower() == "expires":
            print(f"{k:<15}:", v, "->", datetime.datetime.utcfromtimestamp(int(v)).strftime("%Y-%m-%d %H:%M:%S"))
        else:
            print(f"{k:<15}:", v[:40])
# when did the build run?
print("built          :", d["meta"]["built"])
