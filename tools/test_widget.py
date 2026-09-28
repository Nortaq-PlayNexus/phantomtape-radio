"""Prove SC.Widget works headlessly before rewriting the player around it.

Checks: api.js loads, SC.Widget is exposed, load() accepts a public permalink,
READY fires, and getDuration returns real milliseconds.
"""
import pathlib
import time

from playwright.sync_api import sync_playwright

EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
OUT = pathlib.Path(__file__).resolve().parent.parent / "shots"
OUT.mkdir(exist_ok=True)
PAGE = (OUT / "_widgettest.html")

PAGE.write_text("""<!doctype html><meta charset=utf-8>
<body style="background:#0a0e1a;color:#b8ff1e;font:14px monospace">
<div id=log>booting</div>
<iframe id=w width="100%" height="166" allow="autoplay"
  src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/2408961174&color=%23b8ff1e&theme=black&visual=false&hide_related=true&show_comments=false&show_user=true&show_reposts=false&show_teaser=false"></iframe>
<script src="https://w.soundcloud.com/player/api.js"></script>
<script>
const log = (m) => { document.getElementById('log').textContent += "\\n" + m; };
window.__result = { ready:false, duration:null, events:[] };
try {
  log("api.js loaded, SC=" + (typeof SC));
  const wdg = SC.Widget(document.getElementById('w'));
  log("SC.Widget ok");
  wdg.bind(SC.Widget.Events.READY, () => {
    log("READY");
    window.__result.ready = true;
    wdg.getDuration((d) => { log("getDuration=" + d); window.__result.duration = d; });
  });
  wdg.bind(SC.Widget.Events.PLAY, () => { log("PLAY"); window.__result.events.push("play"); });
  wdg.bind(SC.Widget.Events.ERROR, (e) => { log("ERROR " + JSON.stringify(e)); window.__result.events.push("error"); });
} catch (e) { log("THREW: " + e); window.__result.error = String(e); }
</script>
""", encoding="utf-8")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE, args=["--autoplay-policy=no-user-gesture-required"])
    pg = b.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(PAGE.as_uri())
    pg.wait_for_timeout(9000)
    print("  log:")
    for line in pg.inner_text("#log").splitlines():
        print(f"    {line}")
    print(f"  result : {pg.evaluate('window.__result')}")
    print(f"  errors : {errs or 'none'}")
    b.close()
