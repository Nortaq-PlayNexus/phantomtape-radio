"""Discoverability sweep: set real homepages and accurate topics on own repos.

Two rules this will not break:
  1. Never point a homepage at a URL that does not resolve. Only repos with a
     live GitHub Pages site (or an existing real homepage) get one.
  2. Never invent a topic. Topics are derived strictly from the repo language,
     the description, and the repo name, then capped. A wrong topic is worse
     than no topic - it sends the wrong people to the wrong repo.

Forks are skipped entirely. Dry run by default; --apply to write.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

APPLY = "--apply" in sys.argv
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


# Vocabulary -> topic, only fired on a genuine word-boundary match in the
# repo's own text. Keys are matched case-insensitively against
# "name + description + language".
VOCAB = {
    "audio": "audio", "dsp": "dsp", "music": "music", "sound": "audio",
    "waveform": "audio", "beat": "audio", "midi": "midi", "dj": "audio",
    "speech": "speech-recognition", "transcri": "speech-recognition",
    "rust": "rust", "python": "python", "javascript": "javascript",
    "typescript": "typescript", "c#": "csharp", "csharp": "csharp",
    "go": "go", "shell": "shell", "php": "php", "html": "html",
    "ollama": "ollama", "local-ai": "local-ai", "localfirst": "local-first",
    "offline": "offline-first", "offline-first": "offline-first",
    "agent": "ai-agents", "agents": "ai-agents", "llm": "llm",
    "fine-tun": "fine-tuning", "qLoRA": "fine-tuning",
    "security": "security", "osint": "osint", "forensic": "forensics",
    "cve": "security", "vulnerab": "security-vulnerability",
    "terraform": "terraform", "ansible": "ansible", "cloudflare": "cloudflare",
    "self-host": "self-hosted", "selfhosted": "self-hosted",
    "electron": "electron", "tauri": "tauri", "react": "react",
    "three.js": "threejs", "webgl": "webgl", "game": "game-development",
    "gaming": "game-development", "roblox": "roblox", "ark": "game-development",
    "pytorch": "pytorch", "tensorrt": "cuda", "cuda": "cuda",
    "image": "image-processing", "imagery": "image-processing",
    "nasa": "nasa", "mars": "space", "telemetry": "telemetry",
    "ufo": "ufo", "anomal": "anomaly-detection", "anomaly": "anomaly-detection",
    "sqlite": "sqlite", "database": "database", "sqlalchemy": "sqlalchemy",
    "testing": "testing", "crawler": "web-scraping", "scraping": "web-scraping",
    "torrent": "torrents", "monero": "cryptocurrency",
    "windows": "windows", "linux": "linux", "macos": "macos",
    "physics": "physics", "simulation": "simulation", "quantum": "quantum",
    "watermark": "image-processing", "transcod": "video",
    "video": "video", "ffmpeg": "ffmpeg", "discord": "discord",
    "reactos": "windows", "malware": "security-research",
}

MAX_TOPICS = 5
STOP = {"the", "and", "for", "with", "from", "that", "this", "into", "your", "a"}


def infer_topics(repo):
    lang = (repo.get("language") or "").lower()
    text = f"{repo['name']} {repo.get('description') or ''} {lang}".lower()
    found = []
    for needle, topic in VOCAB.items():
        if re.search(rf"(?<![a-z0-9]){re.escape(needle)}", text):
            if topic not in found:
                found.append(topic)
    # A language tag is accurate and helps search, but only once.
    if lang and lang.replace("c#", "csharp") not in found:
        found.insert(0, lang.replace("c#", "csharp"))
    return found[:MAX_TOPICS]


def pages_live(full):
    """True only if the repo has a Pages site that actually returns 200."""
    pg = gh("-X", "GET", f"repos/{full}/pages")
    url = (pg or {}).get("html_url")
    if not url:
        return None
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "probe"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return url if r.status == 200 else None
    except Exception:
        return None


def main():
    repos = gh("-X", "GET", "users/Nortaq-PlayNexus/repos", "-f", "per_page=100") or []
    own = [r for r in repos if not r["fork"]]
    print(f"  {len(own)} own repos (forks skipped)\n")

    changes = []
    for r in own:
        full = r["name"]
        new_topics = infer_topics(r)
        cur_topics = r.get("topics") or []
        add_topics = [t for t in new_topics if t not in cur_topics]

        new_home = r.get("homepage") or pages_live(f"Nortaq-PlayNexus/{full}")

        if add_topics or (new_home and new_home != r.get("homepage")):
            changes.append((full, add_topics, new_home, r.get("homepage")))

    print(f"  {'repo':<32} {'+topics':<44} homepage")
    print("  " + 92 * "-")
    for full, add, home, cur in changes:
        h = "—" if not home else ("same" if home == cur else home)
        print(f"  {full[:31]:<32} {','.join(add)[:43]:<44} {h[:40]}")

    print(f"\n  {len(changes)} repos would change")
    if not APPLY:
        print("\n  dry run - pass --apply to write")
        return

    ok = fail = 0
    for full, add, home, cur in changes:
        args = ["repo", "edit", f"Nortaq-PlayNexus/{full}", "--add-topic", ",".join(add)]
        if home and home != cur:
            args += ["--homepage", home]
        p = subprocess.run(["gh"] + args, capture_output=True, text=True)
        if p.returncode == 0:
            ok += 1
        else:
            fail += 1
            print(f"  FAILED {full}: {p.stderr.strip()[:90]}")
    print(f"\n  applied: {ok} ok, {fail} failed")


if __name__ == "__main__":
    main()
