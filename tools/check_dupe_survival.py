"""Confirm the dropped section titles now appear only as panels inside
section 08, not as their own sections."""
import io
import re
import sys

html = io.open(sys.argv[1], encoding="utf-8", errors="replace").read()

titles = ["SIGNAL WEATHER", "NIGHTLY INTELLIGENCE REPORT", "SYSTEM INTEGRITY",
          "CURRENT OBSESSION", "LANGUAGE EVOLUTION", "PROJECT LIFECYCLE",
          "WHILE YOU WERE AWAY"]

print("  title                              as a section?   occurrences")
for t in titles:
    as_section = bool(re.search(rf"// \d\d :: [^<]*{re.escape(t)}", html))
    n = html.count(t)
    print(f"  {t:<34} {'YES - still a section' if as_section else 'no':<16} {n}")

print()
print("  Each should read 'no' as a section: the panel survives once inside")
print("  section 08 instead of appearing twice.")
