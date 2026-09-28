"""Produce a README image GitHub will actually accept for the social preview.

GitHub auto-builds a repo's og:image from the first eligible README image.
Eligibility is size-bounded, and a hero that is too wide is silently ignored,
leaving the default Octocat fallback - which is what happened at 1400px.

This resizes the capture into the accepted band and reports the result so the
claim can be checked rather than assumed.
"""
import pathlib
import sys

from PIL import Image

SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "shots/hero.png")
DST = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "assets/hero.png")

# GitHub's auto social card is 1200x630 and only picks a README image that sits
# inside these bounds. 1000x357 is comfortably inside on both axes and keeps a
# wide, banner-ish crop rather than being squashed to a square.
TARGET_W = 1000
MAX_BYTES = 900 * 1024

img = Image.open(SRC).convert("RGB")
w, h = img.size
new_h = max(320, round(h * TARGET_W / w))
out = img.resize((TARGET_W, new_h), Image.LANCZOS)

DST.parent.mkdir(parents=True, exist_ok=True)
out.save(DST, "PNG", optimize=True)

size = DST.stat().st_size
print(f"  source : {w}x{h}  {SRC.stat().st_size // 1024} KB")
print(f"  hero   : {TARGET_W}x{new_h}  {size // 1024} KB  -> {DST}")
print(f"  within 1024px max dimension : {max(TARGET_W, new_h) <= 1024}")
print(f"  at least 320px tall         : {new_h >= 320}")
print(f"  under 1 MB                  : {size < MAX_BYTES}")
print(f"  aspect ratio                : {TARGET_W / new_h:.2f}:1  (card is 1.90:1)")
