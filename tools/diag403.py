"""Identify which network requests 403 on the live broadcast."""
import pathlib
from playwright.sync_api import sync_playwright

URL = "https://nortaq-playnexus.github.io/phantomtape-radio/"
EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

bad, ok = [], 0

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=EXE)
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    def on_resp(r):
        global ok
        if r.status >= 400:
            bad.append((r.status, r.url))
        elif "sndcdn" in r.url:
            ok += 1

    page.on("response", on_resp)
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.keyboard.press("Escape")
    page.wait_for_timeout(2500)

    art = page.eval_on_selector("#npArt", "el => ({src: el.src, w: el.naturalWidth, h: el.naturalHeight})")
    browser.close()

print(f"  sndcdn responses ok : {ok}")
print(f"  failed requests     : {len(bad)}")
for s, u in bad:
    print(f"    {s}  {u[:110]}")
print(f"  artwork element     : {art}")
