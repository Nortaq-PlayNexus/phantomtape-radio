"""Verify the repo's social preview card is the hero, not the fallback.

Extracts og:image, downloads it, and reports dimensions plus whether the
pixel signature matches the Octocat fallback (a large white circle centred
on a dark field) or something with real content in it.
"""
import io
import pathlib
import re
import sys
import urllib.request

from PIL import Image

page = pathlib.Path(sys.argv[1])
cache = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "og_check.png")

h = io.open(page, encoding="utf-8", errors="replace").read()


def meta(prop):
    m = re.search(rf'<meta[^>]+(?:property|name)="{prop}"[^>]+content="([^"]*)"', h)
    if not m:
        m = re.search(rf'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="{prop}"', h)
    return m.group(1) if m else None


og = meta("og:image")
print(f"  og:image  {og}")
if not og:
    raise SystemExit("  no og:image on the page")

req = urllib.request.Request(og, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    raw = r.read()
cache.write_bytes(raw)

im = Image.open(io.BytesIO(raw)).convert("RGB")
print(f"  size      {im.width}x{im.height}  {len(raw) // 1024} KB")

# The Octocat fallback is a single dominant white disc on near-black. Sample a
# grid and measure how much of the card is that white circle.
px = im.load()
tot = white = dark = 0
for y in range(0, im.height, 7):
    for x in range(0, im.width, 7):
        r, g, b = px[x, y]
        tot += 1
        if r > 200 and g > 200 and b > 200:
            white += 1
        if r < 60 and g < 70 and b < 90:
            dark += 1
wr, dr = white / tot, dark / tot
print(f"  white {wr:.1%}   dark {dr:.1%}")
if wr > 0.25 and dr > 0.35:
    print("  VERDICT: still the default Octocat fallback")
elif dr > 0.6 and wr < 0.05:
    print("  VERDICT: hero card in use (dark, no fallback disc)")
else:
    print("  VERDICT: inconclusive - inspect the image")
