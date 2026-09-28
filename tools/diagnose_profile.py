"""Diagnostic: what is actually on Nortaq-PlayNexus's GitHub record today?

Views come from a handful of specific things. Measure before optimising.
"""
import json
import subprocess
import sys

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


def search(q, n=20):
    return gh("-X", "GET", "search/issues",
              "-f", f"q={q}", "-f", f"per_page={n}") or {}


print("  Nortaq-PlayNexus contribution record")
print("  " + "-" * 58)

prs = search("author:Nortaq-PlayNexus is:pr", 30)
print(f"  pull requests opened : {prs.get('total_count', '?')}")
for i in (prs.get("items") or [])[:8]:
    merged = bool(i.get("pull_request", {}).get("merged_at"))
    flag = "MERGED" if merged else i["state"].upper()
    print(f"    [{flag:<7}] {i['title'][:52]}")
    print(f"             {i['html_url']}")

iss = search("author:Nortaq-PlayNexus is:issue", 20)
print(f"\n  issues opened        : {iss.get('total_count', '?')}")

com = search("commenter:Nortaq-PlayNexus", 20)
print(f"  issues commented on  : {com.get('total_count', '?')}")

# Where are their stars coming from?
user = gh("-X", "GET", "users/Nortaq-PlayNexus") or {}
print(f"\n  followers            : {user.get('followers_count')}")
print(f"  public repos         : {user.get('public_repos')}")
print(f"  account created      : {user.get('created_at', '')[:10]}")

repos = gh("-X", "GET", "users/Nortaq-PlayNexus/repos",
           "-f", "per_page=100", "-f", "sort=updated") or []
if isinstance(repos, dict):
    repos = []
total_forks = sum(r.get("forks_count", 0) for r in repos)
total_watch = sum(r.get("watchers_count", 0) for r in repos)
total_issues = sum(r.get("open_issues_count", 0) for r in repos)
print(f"  total forks          : {total_forks}")
print(f"  total watchers       : {total_watch}")
print(f"  open issues (own)    : {total_issues}")

top = sorted(repos, key=lambda r: -(r.get("stargazers_count", 0)))[:6]
print(f"\n  top starred repos:")
for r in top:
    print(f"    {r['stargazers_count']:>3} *  {r['name'][:40]:<40} {(r.get('description') or '')[:44]}")

# Do their repos have any outside traffic at all?
print(f"\n  repos with a topic (searchable / discoverable):")
withtopics = [r for r in repos if r.get("topics")]
print(f"    {len(withtopics)} of {len(repos)}")
print(f"  repos with a homepage set:")
print(f"    {len([r for r in repos if r.get('homepage')])} of {len(repos)}")
print(f"  repos with a description:")
print(f"    {len([r for r in repos if r.get('description')])} of {len(repos)}")
