import json, requests
d = json.load(open("data/catalogue.json", encoding="utf-8"))
u = d["tracks"][0]["stream"]
H = {"Range": "bytes=0-100"}
tests = {
  "no origin                ": {},
  "Origin: pages            ": {"Origin": "https://nortaq-playnexus.github.io"},
  "Origin: localhost        ": {"Origin": "http://127.0.0.1:8777"},
  "Referer: pages           ": {"Referer": "https://nortaq-playnexus.github.io/phantomtape-radio/"},
  "Origin+Referer: pages    ": {"Origin": "https://nortaq-playnexus.github.io",
                                 "Referer": "https://nortaq-playnexus.github.io/phantomtape-radio/"},
}
for name, extra in tests.items():
    r = requests.get(u, headers=H | extra, timeout=25)
    acao = r.headers.get("Access-Control-Allow-Origin", "-")
    print(f"  {name} -> {r.status_code}  ACAO={acao}")
