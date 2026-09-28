# PHANTOMTAPE // 103.7

```
╔══════════════════════════════════════════════════════════════╗
║  PIRATE DIGITAL BROADCAST :: ARCHIVE NODE 07 :: SIGNAL 07   ║
╚══════════════════════════════════════════════════════════════╝
```

A self-hosted music page for **DJ PHANTOMTAPE**, built to look like the
frequency it is named after. 60 public tracks off SoundCloud with real
waveforms you can scrub.

Live: **<https://nortaq-playnexus.github.io/phantomtape-radio/>**

Same palette, same terminal grammar, same dry humour as the GitHub profile —
this is what the `MUSIC ... [ OFF AIR — <PHANTOMTAPE_P-10> ]` slot points at.

---

## How the audio works

**It does not store stream URLs, and that is deliberate.**

The first version resolved CloudFront presigned MP3 links at build time and
wrote them into `catalogue.json`. It looked perfect and was completely broken:
those links die about **20 minutes** after SoundCloud issues them. Verified
directly — a freshly resolved URL returned `206`, the one baked twenty minutes
earlier returned `403`. A nightly rebuild could never keep up.

So audio is served live by the official **SoundCloud Widget API**. The page
embeds a widget iframe, keeps every visible control to itself, and drives the
widget over `postMessage`:

| Ours | Widget |
|---|---|
| artwork, waveform, rows, filters, stats, CRT styling | the actual audio stream |
| play / pause / next / prev / seek / volume UI | `play()`, `pause()`, `seekTo()`, `setVolume()` |
| waveform playhead and time readout | `PLAY_PROGRESS`, `getPosition()`, `getDuration()` |

This also means **no API key, no OAuth token, no client_id and no backend**.
The widget resolves each track from its public permalink on demand, and it is
the attribution-compliant way to play someone else's audio.

The equaliser bars are driven by the real waveform windowed around the
playhead, not a Web Audio analyser — the stream lives inside a cross-origin
iframe and cannot be tapped. Honest about being a visualiser.

## What it does

- **60 tracks, 3.2 hours**, all public, straight from the SoundCloud profile
- **Real waveforms.** 1800 amplitude samples per track, max-pooled to 600
  points so transients survive the downsample
- **Scrubbable.** Click the waveform to jump, or focus it and use arrow keys
  (5s, shift-arrow 30s)
- **Filter and sort.** Grep the archive, filter by genre, sort by newest, most
  played, A–Z or runtime
- **Keyboard.** `space` play/pause, `j` next, `k` previous, `/` search

## Run it

```bash
git clone https://github.com/Nortaq-PlayNexus/phantomtape-radio
cd phantomtape-radio

python -m pip install requests
python tools/build_catalogue.py      # refresh metadata + waveforms

python -m http.server 8777
# open http://127.0.0.1:8777
```

A server is required — `fetch()` will not read `file://` paths.

## Deploy

Push to GitHub and turn Pages on for the branch. No build step, no bundler, no
framework, no secrets. It is a static site.

## Layout

```
index.html               the page
assets/style.css         CRT palette, layout, responsive
assets/app.js            widget bridge, waveform renderer, rows, panels
data/catalogue.json      60 tracks: title, genre, duration, plays, artwork, permalink
data/waveforms.json      60 waveform arrays, 600 points each
tools/build_catalogue.py the resolver
tools/test_player.py     end-to-end playback test (real click, asserts position moves)
tools/shoot.py           screenshot for the profile embed
```

## Refreshing the catalogue

Only metadata, play counts and waveforms change. SoundCloud's own endpoints
are unauthenticated for this data.

```bash
python tools/build_catalogue.py
```

`.github/workflows/rebroadcast.yml` runs it nightly at 00:17 UTC and commits
the result. Nothing about playback depends on it — the widget always resolves a
live stream.

## Testing

```bash
python tools/test_player.py
```

Launches a real browser, clicks play, and asserts the position actually
advances, that `seekTo` lands, that the next track resolves its own duration,
and that the console stays empty. If the console is dirty, audio is broken.

## Credits

Audio and artwork belong to DJ PHANTOMTAPE and stay on SoundCloud. Playback is
the official SoundCloud widget, per their
[attribution guidelines](https://developers.soundcloud.com/docs/api/buttons-logos).
This page links and streams; it does not re-host.
