import requests
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
CID = "pmagYZKQF6mRtNmtRzPkXSQJ76jYHLN8"
O = "https://nortaq-playnexus.github.io"
urls = [
  ("tracks list     ", f"https://api-v2.soundcloud.com/users/1645780733/tracks?client_id={CID}&limit=1"),
  ("transcode resolve", f"https://api-v2.soundcloud.com/media/soundcloud:tracks:2408961174/3b3f2e4d-1cdc-4829-90e3-cf50ef108a49/stream/progressive?client_id={CID}"),
  ("waveform        ", "https://wave.sndcdn.com/n6jO23j5xdI7_m.json"),
]
for name, u in urls:
    r = requests.get(u, headers={"Origin": O, "User-Agent": UA}, timeout=25)
    acao = r.headers.get("Access-Control-Allow-Origin", "(none)")
    acac = r.headers.get("Access-Control-Allow-Headers", "(none)")
    print(f"  {name} -> {r.status_code}  ACAO={acao}  ACAH={acac}")
# preflight, as a browser would send for a GET with a Range header
print("\n  preflight (OPTIONS):")
for name, u in [("api-v2  ", f"https://api-v2.soundcloud.com/media/soundcloud:tracks:2408961174/3b3f2e4d-1cdc-4829-90e3-cf50ef108a49/stream/progressive?client_id={CID}"),
                ("wave    ", "https://wave.sndcdn.com/n6jO23j5xdI7_m.json")]:
    r = requests.options(u, headers={"Origin": O, "Access-Control-Request-Method": "GET", "User-Agent": UA}, timeout=25)
    print(f"    {name} -> {r.status_code}  ACAO={r.headers.get('Access-Control-Allow-Origin','(none)')}")
