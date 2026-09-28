"""Vet real contribution opportunities in the audio / DSP / local-AI niche.

Rather than fuzzy search (which mis-parses and returns noise), this walks a
hand-picked set of projects the account has demonstrable overlap with and
pulls genuinely open, genuinely unclaimed bugs.

Scoring favours work that is:
  * a real defect with a reproduction, not a wishlist item
  * not already claimed by a linked PR
  * in a repo with enough activity that maintainers will actually review
"""
import json
import re
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


# Projects that overlap with local-first tooling, DSP and audio work.
TARGETS = [
    "librosa/librosa",
    "scipy/scipy",
    "numpy/numpy",
    "xiph/flac",
    "ollama/ollama",
    "BerriAI/litellm",
    "pycairo?skip",  # placeholder removed below
]
TARGETS = [t for t in TARGETS if not t.endswith("?skip")]

# Words that mark an issue as a real, actionable defect.
BUGWORDS = re.compile(
    r"\b(crash|traceback|exception|error|wrong|incorrect|regression|"
    r"segfault|nan|inf value|race condition|deadlock|corrupt|silent(ly)?\s+fail|"
    r"off[- ]by[- ]one|buffer overflow|leak)\b", re.I
)
# Words that mean "someone is already on it" or "this is not a bug fix".
SKIPWORDS = re.compile(
    r"\b(feature request|proposal|discussion|question|documentation|docs:|"
    r"rfc|roadmap|benchmark)\b", re.I
)


def repo_meta(full):
    return gh("-X", "GET", f"repos/{full}") or {}


def open_bugs(full, limit=60):
    q = (f"repo:{full} is:issue is:open label:bug "
         f"-linked:pr sort:updated-desc")
    r = gh("-X", "GET", "search/issues", "-f", f"q={q}", "-f", f"per_page={limit}")
    return (r or {}).get("items") or []


print("  VETTED OPPORTUNITIES")
print("  " + 74 * "-")

out = []
for full in TARGETS:
    meta = repo_meta(full)
    if not meta:
        print(f"  {full}: could not read repo")
        continue
    stars = meta.get("stargazers_count", 0)
    pushed = (meta.get("pushed_at") or "")[:10]
    bugs = open_bugs(full)
    if not bugs:
        print(f"  {full} ({stars}*): no open labelled bugs without a linked PR")
        continue
    print(f"  {full}  ({stars}*  last push {pushed})  {len(bugs)} open bugs")
    for i in bugs[:4]:
        body = (i.get("body") or "")
        title = i.get("title") or ""
        signal = bool(BUGWORDS.search(title + " " + body[:400]))
        if SKIPWORDS.search(title):
            continue
        if not signal:
            continue
        out.append((full, stars, i["html_url"], title, i.get("comments", 0)))

print()
print("  WORTH A LOOK (real defect, unclaimed, no linked PR)")
print("  " + 74 * "-")
for full, stars, url, title, comments in out[:14]:
    print(f"  [{stars}*] {full}")
    print(f"        {title[:72]}")
    print(f"        {url}   comments: {comments}")
if not out:
    print("  nothing scored - the labelled queues in these repos are clean or")
    print("  everything open is already claimed")
