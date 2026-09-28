"""Check the rendered GitHub profile reflects the trimmed README."""
import io
import re
import sys

html = io.open(sys.argv[1], encoding="utf-8", errors="replace").read()

heads = re.findall(r"// (\d{2}) :: ([A-Z0-9 \.\-&]+)", html)
seen, order = set(), []
for n, t in heads:
    if n not in seen:
        seen.add(n)
        order.append((n, t.strip()))

print(f"  rendered sections: {len(order)}")
for n, t in order:
    print(f"    // {n}  {t[:46]}")

gone = ["SIGNAL WEATHER", "NIGHTLY INTELLIGENCE REPORT", "SYSTEM INTEGRITY",
        "CURRENT OBSESSION", "LANGUAGE EVOLUTION", "PROJECT LIFECYCLE",
        "WHILE YOU WERE AWAY"]
still = [g for g in gone if g in html]
print()
print(f"  dropped sections still rendered: {still or 'none - clean'}")
print(f"  PHNT-007 present               : {'PHNT-007' in html}")
print(f"  U+FFFD corruption              : {'YES' if chr(0xFFFD) in html else 'none'}")
