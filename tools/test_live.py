import pathlib
from playwright.sync_api import sync_playwright
EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
URL = "https://nortaq-playnexus.github.io/phantomtape-radio/"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    pg = b.new_page(viewport={"width": 1280, "height": 950})
    errs, bad = [], []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("response", lambda r: bad.append((r.status, r.url[:80])) if r.status >= 400 else None)
    pg.goto(URL, wait_until="networkidle", timeout=60000)
    pg.keyboard.press("Escape"); pg.wait_for_timeout(3500)
    rows = pg.eval_on_selector_all(".row", "e => e.length")
    pg.click("#btnPlay"); pg.wait_for_timeout(7000)
    pos = pg.evaluate("new Promise(r => SC.Widget(document.getElementById('scWidget')).getPosition(p => r(p)))")
    onair = pg.inner_text("#onairLabel")
    tnow = pg.inner_text("#tNow")
    print(f"  DEPLOYED SITE")
    print(f"    rows        : {rows}")
    print(f"    onair       : {onair}")
    print(f"    position ms : {pos}")
    print(f"    tNow        : {tnow}")
    print(f"    console err : {errs or 'none'}")
    print(f"    bad requests: {bad or 'none'}")
    print(f"\n  VERDICT: {'PASS - playing on the live site' if pos and pos > 1000 and not errs else 'FAIL'}")
    b.close()
