import requests
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
CID = "pmagYZKQF6mRtNmtRzPkXSQJ76jYHLN8"
O = "https://nortaq-playnexus.github.io"
cands = [
 ("v1 track        ", f"https://api.soundcloud.com/tracks/2408961174?client_id={CID}"),
 ("v1 resolve      ", f"https://api.soundcloud.com/resolve?url=https%3A%2F%2Fsoundcloud.com%2Fphantomtape%2Flonely-remix&client_id={CID}"),
 ("v1 user tracks  ", f"https://api.soundcloud.com/users/1645780733/tracks?client_id={CID}&limit=1"),
 ("v2 track        ", f"https://api-v2.soundcloud.com/tracks/2408961174?client_id={CID}"),
 ("widget host     ", "https://w.soundcloud.com/player/?url=https%3A%2F%2Fsoundcloud.com%2Fphantomtape"),
]
for name, u in cands:
    try:
        r = requests.get(u, headers={"Origin": O, "User-Agent": UA}, timeout=20)
        acao = r.headers.get("Access-Control-Allow-Origin", "(none)")
        print(f"  {name} -> {r.status_code}  ACAO={acao}")
    except Exception as e:
        print(f"  {name} -> ERR {str(e)[:60]}")
