"""Rank the account's own repos and expose the discoverability gaps.

68 repos with 10 watchers is a breadth problem. The question worth answering is
which two or three are actually worth pushing, and what cheap fixes are
missing everywhere else.
"""
import json
import subprocess

GH = ["gh", "api"]


def gh(*args):
    p = subprocess.run(GH + list(args), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        return None
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return None


repos = gh("-X", "GET", "users/Nortaq-PlayNexus/repos", "-f", "per_page=100") or []

# Niche keywords: what this account knows that a generic profile does not.
NICHE = ("audio", "dsp", "music", "sound", "waveform", "dj", "beat", "speech",
         "midi", "ollama", "local-ai", "local-first", "offline", "agent")

rows = []
for r in repos:
    blob = f"{r['name']} {r.get('description') or ''} {' '.join(r.get('topics') or [])}".lower()
    niche = sum(1 for k in NICHE if k in blob)
    rows.append({
        "name": r["name"],
        "stars": r["stargazers_count"],
        "forks": r["forks_count"],
        "issues": r["open_issues_count"],
        "pushed": (r["pushed_at"] or "")[:10],
        "fork": r["fork"],
        "topics": len(r.get("topics") or []),
        "homepage": bool(r.get("homepage")),
        "lang": r.get("language") or "-",
        "size": r.get("size", 0),
        "niche": niche,
        "desc": bool(r.get("description")),
    })

own = [r for r in rows if not r["fork"]]
forks = [r for r in rows if r["fork"]]

print(f"  {len(own)} own repos, {len(forks)} forks")
print()
print("  TOP BY NICHE FIT x RECENCY x EXISTING TRACTION")
print("  " + 72 * "-")
ranked = sorted(own, key=lambda r: (-r["niche"], -(r["stars"] * 5), r["pushed"]), reverse=False)
ranked.sort(key=lambda r: (-r["niche"], -r["stars"], r["pushed"]))
for r in ranked[:12]:
    flags = []
    if not r["homepage"]:
        flags.append("no-homepage")
    if r["topics"] < 2:
        flags.append("thin-topics")
    if not r["desc"]:
        flags.append("no-desc")
    print(f"  {r['name'][:34]:<34} {r['stars']:>2}* {r['forks']:>2}f  "
          f"{r['pushed']}  niche:{r['niche']:>2}  {r['lang'][:12]:<12} {' '.join(flags)}")

print()
print("  DISCOVERABILITY GAPS (all own repos)")
print("  " + 72 * "-")
print(f"  missing homepage      : {len([r for r in own if not r['homepage']])}/{len(own)}")
print(f"  <2 topics             : {len([r for r in own if r['topics'] < 2])}/{len(own)}")
print(f"  missing description   : {len([r for r in own if not r['desc']])}/{len(own)}")
print(f"  zero stars            : {len([r for r in own if r['stars'] == 0])}/{len(own)}")
print(f"  dormant >180d         : {len([r for r in own if r['pushed'] < '2026-03-31'])}/{len(own)}")
print()
print("  NOTE: a social preview image (og:image) is what shows when a repo is")
print("  linked from Reddit / X / HN. Zero of these will render a preview")
print("  unless one is committed and referenced in the README.")
