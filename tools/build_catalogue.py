"""
PHANTOMTAPE // 103.7  --  catalogue builder

Pulls the public DJ PHANTOMTAPE catalogue off SoundCloud and bakes it into
static JSON the site can play from. Run it, commit the output, deploy.

    python tools/build_catalogue.py

Design notes
------------
* Uses the same unauthenticated public client id that SoundCloud ships to every
  visitor of soundcloud.com. Read-only, no account, no token, nothing secret.
* Stream URLs from SoundCloud are presigned and expire, so they are resolved
  fresh on every build. `.github/workflows/refresh.yml` re-runs this nightly.
* Waveforms come back as 1800 samples per track; we downsample to WAVEFORM_POINTS
  and round to ints so the payload stays small enough to ship as plain JSON.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

import requests

SOUNDCLOUD_USER_ID = "1645780733"          # phantomtape
SOUNDCLOUD_HANDLE = "phantomtape"
CLIENT_ID = "pmagYZKQF6mRtNmtRzPkXSQJ76jYHLN8"   # public, shipped to all visitors
API = "https://api-v2.soundcloud.com"

WAVEFORM_POINTS = 600
WAVEFORM_MAX = 255

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Terminal/CRT palette from the PHANTOMTAPE profile, reused for genre tinting.
GENRE_TINT = {
    "Dance & EDM": "#B8FF1E",
    "Techno": "#00E5FF",
    "Hip-hop & Rap": "#FF4D00",
    "Dubstep": "#FF3B3B",
}


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/json"})
    return s


def get_json(s: requests.Session, url: str, **kw):
    r = s.get(url, timeout=30, **kw)
    r.raise_for_status()
    return r.json()


def fetch_tracks(s: requests.Session) -> list[dict]:
    """Every public track on the profile, newest first, following pagination."""
    out: list[dict] = []
    url = f"{API}/users/{SOUNDCLOUD_USER_ID}/tracks"
    params = {"client_id": CLIENT_ID, "limit": 200}

    while url:
        page = get_json(s, url, params=params)
        out.extend(page.get("collection") or [])
        # next_href carries the offset cursor but drops the client id, so
        # re-attach it on every hop or the second page comes back 401.
        url = page.get("next_href")
        params = {"client_id": CLIENT_ID}
        time.sleep(0.15)

    # De-dupe on id, newest first.
    seen, tracks = set(), []
    for t in out:
        if t["id"] in seen:
            continue
        seen.add(t["id"])
        tracks.append(t)
    return tracks


def downsample(samples: list[int], points: int) -> list[int]:
    """Peak-preserving downsample: max-pool, so transients survive."""
    if not samples:
        return [0] * points
    if len(samples) <= points:
        return [int(s) for s in samples] + [0] * (points - len(samples))
    out, n, chunk = [], len(samples), len(samples) / points
    for i in range(points):
        lo, hi = int(i * chunk), max(int((i + 1) * chunk), int(i * chunk) + 1)
        window = samples[lo:hi]
        out.append(int(max(window)) if window else 0)
    return out


def pick_artwork(track: dict) -> str | None:
    """Prefer a large enough crop, fall back to whatever exists."""
    art = track.get("artwork_url")
    if not art:
        return None
    for token in ("-t500x500.", "-large.", "-t67x67."):
        if token in art:
            return art.replace(token, "-t500x500.")
    return art


def resolve_stream(s: requests.Session, track: dict) -> dict | None:
    """Resolve a fresh presigned progressive MP3 URL.

    Progressive first (a single range-requestable file, which is what a
    scrubbable waveform player wants), then HLS as a fallback.
    """
    transcodings = ((track.get("media") or {}).get("transcodings")) or []
    ordered = sorted(
        transcodings,
        key=lambda t: 0 if t.get("format", {}).get("protocol") == "progressive" else 1,
    )

    for t in ordered:
        proto = t.get("format", {}).get("protocol")
        try:
            payload = get_json(s, t["url"], params={"client_id": CLIENT_ID})
        except Exception:
            continue
        url = payload.get("url")
        if not url:
            continue
        return {"url": url, "protocol": proto}
    return None


def main() -> int:
    s = session()
    tracks = fetch_tracks(s)
    if not tracks:
        print("no tracks returned - aborting without touching existing data", file=sys.stderr)
        return 1

    print(f"fetched {len(tracks)} tracks")

    catalogue, waveforms = [], {}
    failed = []

    for i, t in enumerate(tracks, 1):
        tid = t["id"]
        label = f"[{i:>2}/{len(tracks)}] {t['title'][:44]}"

        stream = resolve_stream(s, t)
        if not stream:
            failed.append(tid)
            print(f"  !! {label}  no stream")
            continue

        wf: list[int] = []
        wf_url = t.get("waveform_url")
        if wf_url:
            try:
                raw = get_json(s, wf_url)
                wf = downsample(raw.get("samples") or [], WAVEFORM_POINTS)
            except Exception as exc:
                print(f"  ~~ {label}  waveform failed: {exc}")
        if wf:
            waveforms[str(tid)] = wf

        genre = t.get("genre") or "Unclassified"
        catalogue.append(
            {
                "id": tid,
                "n": i,
                "title": t["title"],
                "duration": round((t.get("full_duration") or t["duration"]) / 1000),
                "genre": genre,
                "tint": GENRE_TINT.get(genre, "#FFC430"),
                "plays": t.get("playback_count", 0),
                "likes": t.get("likes_count", 0),
                "reposts": t.get("reposts_count", 0),
                "released": (t.get("display_date") or t.get("created_at") or "")[:10],
                "artwork": pick_artwork(t),
                "permalink": t.get("permalink_url"),
                "stream": stream["url"],
                "protocol": stream["protocol"],
            }
        )
        print(f"  ok {label}  {catalogue[-1]['duration']}s  {stream['protocol']}")

    if not catalogue:
        print("resolved zero streams - aborting", file=sys.stderr)
        return 1

    profile = get_json(
        s,
        f"{API}/users/{SOUNDCLOUD_USER_ID}",
        params={"client_id": CLIENT_ID},
    )
    # Continuous-mix station is a nice-to-have; some accounts do not have one.
    station: dict = {}
    for candidate in (
        f"{API}/users/{SOUNDCLOUD_USER_ID}/station",
        f"{API}/stream/users/{SOUNDCLOUD_USER_ID}",
    ):
        try:
            station = get_json(s, candidate, params={"client_id": CLIENT_ID})
            break
        except Exception:
            continue

    meta = {
        "artist": profile.get("full_name") or "DJ PHANTOMTAPE",
        "handle": SOUNDCLOUD_HANDLE,
        "city": profile.get("city"),
        "country": profile.get("country_code"),
        "followers": profile.get("followers_count", 0),
        "following": profile.get("followings_count", 0),
        "avatar": profile.get("avatar_url"),
        "permalink": profile.get("permalink_url"),
        "description": profile.get("description"),
        "station": station,
        "frequency": "103.7",
        "track_count": len(catalogue),
        "total_ms": sum(t["duration"] for t in catalogue) * 1000,
        "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "catalogue.json").write_text(
        json.dumps({"meta": meta, "tracks": catalogue}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    (DATA / "waveforms.json").write_text(
        json.dumps(waveforms, separators=(",", ":")), encoding="utf-8"
    )

    size = lambda p: f"{p.stat().st_size / 1024:.0f} KB"
    print(f"\nmeta      {profile.get('followers_count')} followers, {len(catalogue)} tracks")
    print(f"tracks    {len(catalogue)} ({len(failed)} failed)")
    print(f"waveforms {len(waveforms)}")
    print(f"wrote     data/catalogue.json  {size(DATA / 'catalogue.json')}")
    print(f"wrote     data/waveforms.json  {size(DATA / 'waveforms.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
