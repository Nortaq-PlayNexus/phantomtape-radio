"""Screenshot the live broadcast for embedding on the GitHub profile.

GitHub strips <iframe> from README markdown, so the only way to *show* the
player on the profile is a still image that links to the live page. This
grabs that still, plus a tight crop of the player deck.
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

URL = "https://nortaq-playnexus.github.io/phantomtape-radio/"
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
OUT.mkdir(parents=True, exist_ok=True)

LOCAL_BROWSERS = [
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

with sync_playwright() as p:
    # Playwright's bundled chromium is not installed here, so drive the
    # browser that is: Brave if present, else Edge.
    exe = next((b for b in LOCAL_BROWSERS if pathlib.Path(b).exists()), None)
    if exe:
        print(f"  browser        : {pathlib.Path(exe).name}")
        browser = p.chromium.launch(executable_path=exe, args=["--force-color-profile=srgb"])
    else:
        print("  browser        : playwright bundled chromium")
        browser = p.chromium.launch(args=["--force-color-profile=srgb"])
    # 1x at 1400px: GitHub's content column is ~1012px, so this is already
    # sharper than it will ever be displayed, at a third of the file size of a
    # 2x capture.
    page = browser.new_page(viewport={"width": 1400, "height": 950}, device_scale_factor=1)

    errors = []
    page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

    page.goto(URL, wait_until="networkidle", timeout=60000)

    # Dismiss the boot overlay, then let the first track's waveform settle.
    page.keyboard.press("Escape")
    page.wait_for_timeout(1500)

    # Start playback so the still shows the thing working: ON AIR, a lit
    # playhead on the waveform, and a non-zero clock.
    page.click("#btnPlay")
    page.wait_for_timeout(5000)
    page.evaluate("SC.Widget(document.getElementById('scWidget')).seekTo(42000)")
    page.wait_for_timeout(2500)

    # Confirm the page actually initialised before shooting anything.
    rows = page.eval_on_selector_all(".row", "els => els.length")
    title = page.inner_text("#npTitle")
    onair = page.inner_text("#onairLabel")
    clock = page.inner_text("#tNow")
    pos = page.evaluate(
        "new Promise(r => SC.Widget(document.getElementById('scWidget')).getPosition(p => r(p)))"
    )
    wave_drawn = page.evaluate(
        "() => { const c = document.getElementById('wave');"
        " const x = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;"
        " let n = 0; for (let i = 3; i < x.length; i += 4) if (x[i] > 0) n++; return n; }"
    )

    print(f"  rows rendered : {rows}")
    print(f"  now playing   : {title!r}")
    print(f"  on air        : {onair}  @ {clock}  ({pos:.0f} ms)")
    print(f"  waveform px   : {wave_drawn}")
    if errors:
        print("  console errors:")
        for e in errors[:8]:
            print(f"    {e}")
    else:
        print("  console       : clean")

    # Full page, for the README hero slot.
    page.screenshot(path=str(OUT / "broadcast-full.png"), full_page=True)

    # Tight crop of masthead + player deck, for a compact README embed.
    deck = page.query_selector(".deck")
    if deck:
        deck.screenshot(path=str(OUT / "broadcast-deck.png"))

    top = page.query_selector(".masthead")
    if top:
        top.screenshot(path=str(OUT / "broadcast-masthead.png"))

    browser.close()

for f in sorted(OUT.glob("broadcast-*.png")):
    print(f"  wrote {f.name}  {f.stat().st_size // 1024} KB")
