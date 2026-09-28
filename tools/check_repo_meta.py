import json, subprocess
def gh(*a):
    p = subprocess.run(["gh","api"]+list(a), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    try: return json.loads(p.stdout)
    except Exception: return None
r = gh("-X","GET","repos/Nortaq-PlayNexus/phantomtape-radio") or {}
print("  name       :", r.get("name"))
print("  description:", r.get("description"))
print("  homepage   :", r.get("homepage"))
print("  topics     :", ",".join(r.get("topics") or []))
print("  stars      :", r.get("stargazers_count"), " forks:", r.get("forks_count"),
      " watchers:", r.get("subscribers_count"))
print("  license    :", (r.get("license") or {}).get("spdx_id"))
print()
print("  description length:", len(r.get("description") or ""), "chars")
print("  card shows the description, so it is the preview copy that matters.")
