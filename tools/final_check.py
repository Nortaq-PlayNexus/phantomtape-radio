import json, subprocess
def gh(*a):
    p = subprocess.run(["gh","api"]+list(a), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    try: return json.loads(p.stdout)
    except Exception: return None
repos = gh("-X","GET","users/Nortaq-PlayNexus/repos","-f","per_page=100") or []
own=[r for r in repos if not r["fork"]]
thin=[r["name"] for r in own if len(r.get("topics") or [])<2]
print(f"  own repos            : {len(own)}")
print(f"  with <2 topics       : {len(thin)}  (was 17)")
print(f"  with a homepage      : {len([r for r in own if r.get('homepage')])}")
print(f"  missing description  : {len([r for r in own if not r.get('description')])}")
print(f"  detected MIT         : {len([r for r in own if (r.get('license') or {}).get('spdx_id')=='MIT'])}")
