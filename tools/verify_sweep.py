import json, subprocess
def gh(*a):
    p = subprocess.run(["gh","api"]+list(a), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    try: return json.loads(p.stdout)
    except Exception: return None
repos = gh("-X","GET","users/Nortaq-PlayNexus/repos","-f","per_page=100") or []
own=[r for r in repos if not r["fork"]]
print(f"  repos checked: {len(own)}")
print(f"  <2 topics still : {len([r for r in own if len(r.get('topics') or [])<2])}")
print(f"  missing homepage: {len([r for r in own if not r.get('homepage')])}")
print()
print("  literal 'comma' topic bugs:", [r["name"] for r in own
      if any("," in t for t in (r.get("topics") or []))] or "none")
print()
print("  topics per repo, min 5 shown:")
for r in sorted(own, key=lambda x: len(x.get("topics") or []))[:6]:
    print(f"    {r['name'][:30]:<30} {len(r.get('topics') or [])}  {','.join((r.get('topics') or [])[:6])}")
