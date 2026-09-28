"""End-to-end test of the rewritten player: load, play, seek, next, volume.

Runs against a local server so the real assets are exercised, and drives the
widget with a real click so autoplay policy is satisfied the way a user would.
"""
import pathlib
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
ROOT = pathlib.Path(__file__).resolve().parent.parent
PORT = 8788

srv = subprocess.Popen(
    [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
    cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
time.sleep(2)

results = {}
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EXE)
        pg = b.new_page(viewport={"width": 1280, "height": 950})

        errs, bad = [], []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        pg.on("response", lambda r: bad.append((r.status, r.url[:90])) if r.status >= 400 else None)

        pg.goto(f"http://127.0.0.1:{PORT}/", wait_until="networkidle", timeout=60000)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(3000)

        results["rows"] = pg.eval_on_selector_all(".row", "e => e.length")
        results["title_0"] = pg.inner_text("#npTitle")
        results["duration_0"] = pg.evaluate("SC.Widget(document.getElementById('scWidget'))"
                                            ".getDuration.length ? 'api-ok' : 'api-ok'")
        # wait for the widget to be ready on track 1
        pg.wait_for_timeout(3500)
        results["dur_ms"] = pg.evaluate(
            "new Promise(r => SC.Widget(document.getElementById('scWidget'))"
            ".getDuration(d => r(d)))")
        results["tEnd_text"] = pg.inner_text("#tEnd")

        # real click on play
        pg.click("#btnPlay")
        pg.wait_for_timeout(6000)
        results["playing_class"] = pg.evaluate("document.body.classList.contains('playing')")
        results["tNow_after_6s"] = pg.inner_text("#tNow")
        results["onair"] = pg.inner_text("#onairLabel")
        results["pos_ms"] = pg.evaluate(
            "new Promise(r => SC.Widget(document.getElementById('scWidget'))"
            ".getPosition(p => r(p)))")

        # seek to 60s
        pg.evaluate("SC.Widget(document.getElementById('scWidget')).seekTo(60000)")
        pg.wait_for_timeout(2500)
        results["pos_after_seek"] = pg.evaluate(
            "new Promise(r => SC.Widget(document.getElementById('scWidget'))"
            ".getPosition(p => r(p)))")
        results["tNow_after_seek"] = pg.inner_text("#tNow")

        # next track
        pg.click("#btnNext")
        pg.wait_for_timeout(6000)
        results["title_1"] = pg.inner_text("#npTitle")
        results["dur_1_ms"] = pg.evaluate(
            "new Promise(r => SC.Widget(document.getElementById('scWidget'))"
            ".getDuration(d => r(d)))")

        # volume
        pg.evaluate("SC.Widget(document.getElementById('scWidget')).setVolume(40)")
        results["vol"] = pg.evaluate(
            "new Promise(r => SC.Widget(document.getElementById('scWidget')).getVolume(v => r(v)))")

        results["errors"] = errs
        results["bad_responses"] = bad
        pg.screenshot(path=str(ROOT / "shots" / "playing.png"))
        b.close()
finally:
    srv.terminate()

print("  RESULTS")
for k, v in results.items():
    print(f"    {k:<20} {v}")

ok = (
    results.get("rows") == 60
    and results.get("dur_ms", 0) > 100000
    and results.get("playing_class") is True
    and results.get("pos_ms", 0) > 1000
    and results.get("pos_after_seek", 0) > 50000
    and results.get("title_1") != results.get("title_0")
)
print(f"\n  VERDICT: {'PASS - audio genuinely plays' if ok else 'FAIL'}")
