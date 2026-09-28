# PHANTOMTAPE // 103.7

```
╔══════════════════════════════════════════════════════════════╗
║  PIRATE DIGITAL BROADCAST :: ARCHIVE NODE 07 :: SIGNAL 07   ║
╚══════════════════════════════════════════════════════════════╝
```

A self-hosted music page for **DJ PHANTOMTAPE**, built to look like the
frequency it is named after. 60 public tracks off SoundCloud, streamed
straight from the source, rendered as real waveforms you can scrub.

Same palette, same terminal grammar, same dry humour as the GitHub profile —
this is what the `MUSIC ... [ OFF AIR — <PHANTOMTAPE_P-10> ]` slot points at.

---

## What it does

- **Real audio.** Not a mockup. Every track resolves to a live SoundCloud
  progressive MP3, with HTTP range requests, so seeking works.
- **Real waveforms.** 1800 amplitude samples per track from SoundCloud,
  max-pooled down to 600 points so transients survive the downsample.
- **Scrubbable.** Click anywhere on the waveform to jump. Arrow keys nudge
  5s, shift-arrow 30s.
- **Filter + sort.** Grep the archive, filter by genre, sort by newest, most
  played, A–Z or runtime.
- **Keyboard.** `space` play/pause, `j` next, `k` previous, `/` search.

## Run it

```bash
git clone https://github.com/Nortaq-PlayNexus/phantomtape-radio
cd phantomtape-radio

python -m pip install requests
python tools/build_catalogue.py      # resolve the catalogue

python -m http.server 8777
# open http://127.0.0.1:8777
```

A server is required — `fetch()` will not read `file://` paths.

## Deploy

Push to GitHub and turn Pages on for the branch. No build step, no bundler,
no framework. It is a static site.

## Rebuilding

SoundCloud's stream URLs are presigned and expire, so `data/catalogue.json`
goes stale. Refresh it with:

```bash
python tools/build_catalogue.py
```

`.github/workflows/rebroadcast.yml` does this nightly at 00:17 UTC and commits
the result, so the deployed page keeps working without you touching it.

## Layout

```
index.html               the page
assets/style.css         CRT palette, layout, responsive
assets/app.js            player, waveform renderer, rows, panels
data/catalogue.json      60 tracks: title, genre, duration, plays, artwork, stream
data/waveforms.json      60 waveform arrays, 600 points each
tools/build_catalogue.py the resolver
```

## The client id

`tools/build_catalogue.py` uses the unauthenticated client id SoundCloud ships
to every visitor of soundcloud.com in its own JavaScript bundle. It is public,
read-only, and needs no account, token or secret. The build only ever reads
public catalogue data for the artist's own profile.

## Licence

Code: MIT. Audio and artwork belong to DJ PHANTOMTAPE and stay on SoundCloud —
this page links and streams, it does not re-host.
