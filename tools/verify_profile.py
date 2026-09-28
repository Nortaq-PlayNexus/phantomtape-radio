"""Verify the live profile README picked up the PHNT-007 changes."""
import io
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = io.open(path, encoding="utf-8").read()

print(f"  fetched chars : {len(text)}")

checks = [
    ("PHNT-007", "PHNT-007"),
    ("103.7 BROADCAST", "103.7 BROADCAST"),
    ("broadcast link", "phantomtape-radio"),
    ("P-09 closed", "PHANTOMTAPE_P-09> CLOSED"),
    ("TUNE IN block", "TUNE IN"),
    ("--tune flag", "--tune"),
]
for label, needle in checks:
    print(f"  {label:<20} {'present' if needle in text else 'MISSING'}")

stale = "MUSIC ...... [ OFF AIR"
print(f"  {'MUSIC slot':<20} {'STILL OFF AIR' if stale in text else 'filled'}")

print(f"  {'u+fffd corruption':<20} {'CLEAN' if '\ufffd' not in text else 'CORRUPT'}")
