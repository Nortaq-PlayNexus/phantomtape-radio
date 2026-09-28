/* ══════════════════════════════════════════���═══════════════════════════
   PHANTOMTAPE // 103.7  --  player
   ══════════════════════════════════════════════════════════════════════ */
(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);

  const el = {
    boot: $('boot'), bootLog: $('bootLog'), bootBar: $('bootBar'), bootSkip: $('bootSkip'),
    shell: $('shell'), clock: $('clock'), dialNeedle: $('dialNeedle'),
    onairLabel: $('onairLabel'),
    art: $('npArt'), eyebrow: $('npEyebrow'), title: $('npTitle'), meta: $('npMeta'),
    wave: $('wave'), cursor: $('waveCursor'), eq: $('eq'),
    play: $('btnPlay'), playGlyph: $('playGlyph'),
    prev: $('btnPrev'), next: $('btnNext'), sc: $('btnSC'),
    tNow: $('tNow'), tEnd: $('tEnd'), tLeft: $('tLeft'), vol: $('vol'),
    count: $('count'), rows: $('rows'), rowsEmpty: $('rowsEmpty'),
    search: $('search'), genres: $('genres'), sort: $('sort'),
    panelWeather: $('panelWeather'), panelGenome: $('panelGenome'),
    links: $('links'), colophon: $('colophon'),
    frame: $('scWidget'),
  };

  // Audio is owned by the SoundCloud Widget. Everything visual is ours, but
  // transport, position and duration all come across postMessage.
  const WIDGET_OPTS = {
    auto_play: false,
    buying: false,
    sharing: false,
    download: false,
    show_artwork: false,
    show_playcount: false,
    show_user: true,
    show_reposts: false,
    show_teaser: false,
    visual: false,
    hide_related: true,
    color: '#b8ff1e',
  };

  const state = {
    meta: null, tracks: [], waves: null,
    view: [], index: -1, filterGenre: null, query: '', sort: 'new',
    scrubbing: false, widgetReady: false, widgetPrimed: false, wantPlay: false,
    pos: 0, dur: 0, playing: false, widget: null, rafEq: 0,
  };

  const fmt = (s) => {
    if (!isFinite(s) || s < 0) s = 0;
    const m = Math.floor(s / 60);
    return `${m}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  };
  const pad = (n) => String(n).padStart(2, '0');
  const bar = (v, w = 22) => '█'.repeat(Math.round(v * w)).padEnd(w, '░');

  // ── widget bridge ──────────────────────────────────────────────────
  const msToS = (ms) => (isFinite(ms) ? ms / 1000 : 0);

  function widgetUrlFor(track) {
    // Widgets resolve plain permalinks server-side, so no API key and no
    // client_id ever reach the browser.
    return `https://w.soundcloud.com/player/?url=${encodeURIComponent(track.permalink)}`
         + '&color=%23b8ff1e&visual=false&hide_related=true&show_comments=false'
         + '&show_user=true&show_reposts=false&show_teaser=false';
  }

  function initWidget(track) {
    if (state.widget || typeof SC === 'undefined' || !SC.Widget) return !!state.widget;
    // The iframe must point at a real track *before* the widget binds, or the
    // player 404s and READY never arrives, which silently kills all transport.
    if (track) el.frame.src = widgetUrlFor(track);

    const w = SC.Widget(el.frame);
    const E = SC.Widget.Events;

    w.bind(E.READY, () => {
      state.widgetReady = true;
      w.getDuration((d) => {
        if (isFinite(d) && d > 0) {
          state.dur = d;
          const t = state.tracks[state.index];
          if (t && Math.abs(msToS(d) - t.duration) > 2) {
            t.duration = Math.round(msToS(d));
            buildRows();
          }
          el.tEnd.textContent = fmt(msToS(d));
          drawWave();
        }
        if (state.wantPlay) w.play();
      });
    });

    w.bind(E.PLAY,  () => { state.playing = true;  setPlayGlyph(true);  });
    w.bind(E.PAUSE, () => { state.playing = false; setPlayGlyph(false); });

    w.bind(E.PLAY_PROGRESS, (e) => {
      if (isFinite(e.currentPosition)) state.pos = e.currentPosition;
      if (isFinite(e.duration) && e.duration > 0 && e.duration !== state.dur) {
        state.dur = e.duration;
        el.tEnd.textContent = fmt(msToS(e.duration));
      }
      paintTime();
    });

    w.bind(E.SEEK, (e) => {
      if (isFinite(e.currentPosition)) state.pos = e.currentPosition;
      paintTime();
    });

    w.bind(E.FINISH, () => { state.playing = false; setPlayGlyph(false); next(); });

    w.bind(E.ERROR, () => {
      el.onairLabel.textContent = 'FAULT';
      el.eyebrow.textContent = '▲ UPLINK FAILED — TRACK UNAVAILABLE';
    });

    state.widget = w;
    return true;
  }

  const send = (fn, ...args) => {
    if (state.widget && state.widgetReady) {
      try { state.widget[fn](...args); return true; } catch (_) {}
    }
    return false;
  };

  /* ── boot sequence ───────────────────────────────────────────────── */
  const BOOT = [
    ['PHANTOMTAPE OS v7.4', 'ok', 0],
    ['KERNEL ............... ONLINE', 'ok', 120],
    ['AUDIO BUS ............ ONLINE', 'ok', 90],
    ['CATALOGUE ............ SCANNING', '', 110],
    ['WAVEFORM CACHE ....... LOADING', '', 90],
    ['UPLINK ............... 103.7 FM', 'ok', 100],
    ['ENCRYPTION ........... NONE (STAGED)', 'warn', 130],
    ['SIGNAL ............... LOCKED', 'ok', 120],
    ['', '', 60],
    ['> PRESS PLAY', 'ok', 200],
  ];

  function runBoot(done) {
    let i = 0, t = 0;
    const tick = () => {
      if (i >= BOOT.length || el.boot.hidden) return;
      const [line, cls, dur] = BOOT[i];
      if (line) {
        const sp = document.createElement('span');
        if (cls) sp.className = cls;
        sp.textContent = line + '\n';
        el.bootLog.appendChild(sp);
      }
      i++;
      t += dur;
      el.bootBar.style.width = `${(i / BOOT.length) * 100}%`;
      el.bootTimer = setTimeout(tick, dur);
    };
    el.bootDone = done;
    tick();
  }

  function endBoot() {
    clearTimeout(el.bootTimer);
    el.boot.hidden = true;
    el.shell.hidden = false;
    drawWave();
    tickClock();
    if (el.bootDone) { el.bootDone(); el.bootDone = null; }
  }

  el.bootSkip.addEventListener('click', endBoot);
  document.addEventListener('keydown', (e) => {
    if (!el.boot.hidden) { endBoot(); return; }
    if (e.target.matches('input, select, textarea')) return;
    if (e.code === 'Space') { e.preventDefault(); toggle(); }
    else if (e.key === 'j') next();
    else if (e.key === 'k') prev();
    else if (e.key === '/') { e.preventDefault(); el.search.focus(); }
  });

  /* ── clock + dial ────────────────────────────────────────────────── */
  function tickClock() {
    const d = new Date();
    el.clock.textContent = `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
  }
  setInterval(() => { tickClock(); if (el.shell.hidden === false) drawWave(); }, 1000);
  setInterval(tickClock, 1000);

  // 103.7 sits ~79% along the 87.5-108.0 band.
  el.dialNeedle.style.left = `${((103.7 - 87.5) / (108 - 87.5)) * 100}%`;

  /* ── waveform ────────────────────────────────────────────────────── */
  const WAVE_MAX = 255;
  let waveCache = null;

  function samples() {
    const t = state.tracks[state.index];
    if (!t) return null;
    if (!state.waves) return null;
    const w = state.waves[t.id];
    if (!w || !w.length) return null;
    if (!waveCache || waveCache.id !== t.id) {
      const max = Math.max(1, ...w);
      waveCache = { id: t.id, data: w.map((v) => (v / max) * WAVE_MAX) };
    }
    return waveCache.data;
  }

  function drawWave() {
    const c = el.wave;
    const ctx = c.getContext('2d');
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const cssW = c.clientWidth || 600;
    const cssH = 150;

    if (c.width !== Math.round(cssW * dpr) || c.height !== Math.round(cssH * dpr)) {
      c.width = Math.round(cssW * dpr);
      c.height = Math.round(cssH * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);

    const mid = cssH / 2;
    const data = samples();

    if (!data) {
      ctx.strokeStyle = '#1e2a42';
      ctx.beginPath(); ctx.moveTo(0, mid); ctx.lineTo(cssW, mid); ctx.stroke();
      ctx.fillStyle = '#46536b';
      ctx.font = '12px "Fira Code", monospace';
      ctx.fillText('NO WAVEFORM DATA', 12, mid - 10);
      return;
    }

    const dur = state.dur || (state.tracks[state.index].duration * 1000) || 1;
    const pos = state.scrubbing ? state.scrubPos : state.pos;
    const played = Math.max(0, Math.min(1, pos / dur));
    const isPlaying = state.playing;

    const bars = Math.max(48, Math.floor(cssW / 4));
    const step = cssW / bars;
    const bw = Math.max(1.4, step * 0.55);

    for (let i = 0; i < bars; i++) {
      const from = Math.floor((i / bars) * data.length);
      const to = Math.max(from + 1, Math.floor(((i + 1) / bars) * data.length));
      let peak = 0;
      for (let k = from; k < to && k < data.length; k++) peak = Math.max(peak, data[k]);

      const h = Math.max(2, (peak / WAVE_MAX) * (cssH - 16));
      const x = i * step + (step - bw) / 2;

      if (i / bars <= played) {
        ctx.fillStyle = isPlaying ? '#b8ff1e' : '#8fbf1a';
        ctx.shadowColor = 'rgba(184,255,30,.55)';
        ctx.shadowBlur = 7;
      } else {
        ctx.fillStyle = '#22304c';
        ctx.shadowBlur = 0;
      }
      ctx.fillRect(x, mid - h / 2, bw, h);
    }
    ctx.shadowBlur = 0;

    ctx.strokeStyle = '#1e2a42';
    ctx.beginPath(); ctx.moveTo(0, mid); ctx.lineTo(cssW, mid); ctx.stroke();

    ctx.strokeStyle = '#ff3b3b';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(played * cssW, 0); ctx.lineTo(played * cssW, cssH); ctx.stroke();
    ctx.lineWidth = 1;
  }

  function paintTime() {
    const dur = state.dur || (state.tracks[state.index]?.duration ?? 0) * 1000;
    el.tNow.textContent = fmt(msToS(state.pos));
    el.tEnd.textContent = fmt(msToS(dur));
    el.tLeft.textContent = fmt(Math.max(0, msToS(dur - state.pos)));
    if (dur > 0) {
      el.wave.setAttribute('aria-valuenow', String(Math.round((state.pos / dur) * 100)));
    }
  }

  /* ── seek ────────────────────────────────────────────────────────── */
  function posFromEvent(e) {
    const r = el.wave.getBoundingClientRect();
    const x = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
    return Math.max(0, Math.min(1, x / r.width));
  }

  const scrubStart = (e) => {
    const t = state.tracks[state.index];
    if (!t) return;
    e.preventDefault();
    state.scrubbing = true;
    const dur = state.dur || t.duration * 1000;
    state.scrubPos = posFromEvent(e) * dur;
    state.pos = state.scrubPos;
    drawWave();
    paintTime();
  };
  const scrubMove = (e) => {
    if (!state.scrubbing) return;
    e.preventDefault();
    const dur = state.dur || (state.tracks[state.index].duration * 1000);
    state.scrubPos = posFromEvent(e) * dur;
    state.pos = state.scrubPos;
    drawWave();
    paintTime();
  };
  const scrubEnd = (e) => {
    if (!state.scrubbing) return;
    e.preventDefault();
    state.scrubbing = false;
    send('seekTo', Math.round(state.scrubPos));
  };

  el.wave.addEventListener('mousedown', scrubStart);
  window.addEventListener('mousemove', scrubMove);
  window.addEventListener('mouseup', scrubEnd);
  el.wave.addEventListener('touchstart', scrubStart, { passive: false });
  el.wave.addEventListener('touchmove', scrubMove, { passive: false });
  el.wave.addEventListener('touchend', scrubEnd);

  el.wave.addEventListener('keydown', (e) => {
    const dur = state.dur || (state.tracks[state.index]?.duration ?? 0) * 1000;
    if (!dur) return;
    const stepMs = (e.shiftKey ? 30 : 5) * 1000;
    if (e.key === 'ArrowRight') { state.pos = Math.min(dur, state.pos + stepMs); send('seekTo', state.pos); paintTime(); drawWave(); e.preventDefault(); }
    if (e.key === 'ArrowLeft')  { state.pos = Math.max(0, state.pos - stepMs); send('seekTo', state.pos); paintTime(); drawWave(); e.preventDefault(); }
  });

  /* ── equaliser ───────────────────────────────────────────────────── */
  // No Web Audio: the stream lives inside a cross-origin widget iframe, so it
  // cannot be tapped. The bars are driven by the real waveform windowed around
  // the playhead, which is honest about being a visualisation, not an analyser.
  function buildEq() {
    el.eq.innerHTML = '';
    state.eqBars = Array.from({ length: 24 }, () => {
      const b = document.createElement('i');
      el.eq.appendChild(b);
      return b;
    });
  }

  function drawEq() {
    state.rafEq = requestAnimationFrame(drawEq);
    if (!state.eqBars) return;
    const w = samples();
    const dur = state.dur || (state.tracks[state.index]?.duration ?? 0) * 1000;
    const p = dur ? state.pos / dur : 0;

    for (let i = 0; i < state.eqBars.length; i++) {
      let v;
      if (!state.playing || !w) {
        v = 0.05 + Math.random() * 0.03;
      } else {
        const centre = p * w.length + (i - state.eqBars.length / 2) * 2.2;
        const k = Math.floor(centre);
        v = k >= 0 && k < w.length ? w[k] / WAVE_MAX : 0;
        v *= 0.55 + 0.45 * Math.abs(Math.sin(Date.now() / 90 + i));
      }
      state.eqBars[i].style.height = `${Math.max(6, Math.min(100, v * 100))}%`;
    }
  }

  /* ── transport ───────────────────────────────────────────────────── */
  function load(i, autoplay) {
    if (i < 0 || i >= state.tracks.length) return;
    state.index = i;
    const t = state.tracks[i];

    waveCache = null;
    state.pos = 0;
    state.dur = t.duration * 1000;
    state.playing = false;
    state.widgetReady = false;
    state.wantPlay = !!autoplay;
    setPlayGlyph(false);

    el.art.src = t.artwork || '';
    el.art.alt = t.title;
    el.eyebrow.textContent = `▲ ON AIR — TRANSMISSION ${String(t.n).padStart(3, '0')} / ${state.meta.track_count}`;
    el.title.textContent = t.title;
    el.meta.innerHTML =
      `<span class="chip" style="--tint:${t.tint}">${t.genre}</span> · ${fmt(t.duration)} · ` +
      `${t.plays.toLocaleString()} plays · ${t.likes.toLocaleString()} likes · ${t.released}`;
    el.sc.href = t.permalink;
    el.onairLabel.textContent = 'TUNING';
    el.tEnd.textContent = fmt(t.duration);

    markRow();
    drawWave();
    paintTime();

    if (!initWidget(t)) {
      el.eyebrow.textContent = '▲ WIDGET API UNAVAILABLE — RELOAD TO RESTORE UPLINK';
      el.onairLabel.textContent = 'FAULT';
      return;
    }

    // load() re-points the same iframe, so bound listeners survive. Skipping it
    // on the very first call avoids reloading the src initWidget() just set.
    if (state.widgetPrimed) {
      // load() takes the *item* URL, not a widget URL - handing it a widget
      // URL makes it wrap the whole thing again and the player 404s.
      state.widget.load(t.permalink, {
        ...WIDGET_OPTS,
        auto_play: !!autoplay,
        callback: () => {
          state.widgetReady = true;
          if (state.wantPlay) state.widget.play();
        },
      });
    } else {
      state.widgetPrimed = true;
      if (autoplay) {
        const go = () => { state.widgetReady = true; state.widget.play(); };
        el.frame.addEventListener('load', go, { once: true });
      }
    }
  }

  function toggle() {
    if (state.index < 0) { load(0, true); return; }
    if (state.playing) {
      state.wantPlay = false;
      send('pause');
    } else {
      state.wantPlay = true;
      send('play');
    }
  }

  function next() { load((state.index + 1) % state.tracks.length, true); }

  function prev() {
    // Restart the track first, like a record deck, before stepping back.
    if (state.pos > 3000) { state.pos = 0; send('seekTo', 0); paintTime(); drawWave(); return; }
    load((state.index - 1 + state.tracks.length) % state.tracks.length, true);
  }

  function setPlayGlyph(playing) {
    el.playGlyph.innerHTML = playing ? '&#10073;&#10073;' : '&#9654;';
    el.play.setAttribute('aria-label', playing ? 'Pause' : 'Play');
    document.body.classList.toggle('playing', playing);
    if (state.index >= 0) el.onairLabel.textContent = playing ? 'ON AIR' : 'STANDBY';
  }

  el.play.addEventListener('click', toggle);
  el.next.addEventListener('click', next);
  el.prev.addEventListener('click', prev);
  el.vol.addEventListener('input', () => send('setVolume', Number(el.vol.value)));

  /* ── render loop ─────────────────────────────────────────────────── */
  function frame() {
    requestAnimationFrame(frame);
    if (state.index < 0) return;
    drawWave();
  }

  /* ── rows ────────────────────────────────────────────────────────── */
  function markRow() {
    [...el.rows.children].forEach((r, i) => {
      const isCur = i === state.index && state.view[i] && state.view[i].id === state.tracks[state.index]?.id;
      r.classList.toggle('is-playing', !!isCur);
    });
  }

  function buildRows() {
    const q = state.query.trim().toLowerCase();
    let rows = state.tracks.filter((t) => {
      if (state.filterGenre && t.genre !== state.filterGenre) return false;
      if (q && !(`${t.title} ${t.genre}`.toLowerCase().includes(q))) return false;
      return true;
    });

    const cmp = {
      new:  (a, b) => b.released.localeCompare(a.released) || b.id - a.id,
      old:  (a, b) => a.released.localeCompare(b.released) || a.id - b.id,
      plays:(a, b) => b.plays - a.plays,
      title:(a, b) => a.title.localeCompare(b.title),
      long: (a, b) => b.duration - a.duration,
    }[state.sort];
    rows = rows.sort(cmp);
    state.view = rows;

    el.count.textContent = String(rows.length);
    el.rowsEmpty.hidden = rows.length > 0;
    el.rows.innerHTML = '';

    const frag = document.createDocumentFragment();
    for (const t of rows) {
      const r = document.createElement('div');
      r.className = 'row';
      r.tabIndex = 0;
      r.style.setProperty('--tint', t.tint);
      r.innerHTML =
        `<span class="row__n">${String(t.n).padStart(3, '0')}</span>` +
        `<span class="row__title"></span>` +
        `<span class="row__g">${t.genre.toUpperCase()}</span>` +
        `<span class="row__d">${fmt(t.duration)}</span>` +
        `<span class="row__p">${t.plays.toLocaleString()}</span>` +
        `<span class="row__eq"><i></i><i></i><i></i></span>`;
      r.querySelector('.row__title').textContent = t.title;   // textContent: no HTML injection
      r.title = `${t.title} — ${t.genre}`;
      const pick = () => load(state.tracks.indexOf(t), true);
      r.addEventListener('click', pick);
      r.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.code === 'Space') { e.preventDefault(); pick(); }
      });
      frag.appendChild(r);
    }
    el.rows.appendChild(frag);
    markRow();
  }

  function buildGenres() {
    const counts = new Map();
    for (const t of state.tracks) counts.set(t.genre, (counts.get(t.genre) || 0) + 1);
    el.genres.innerHTML = '';
    const all = document.createElement('button');
    all.type = 'button';
    all.className = 'chip';
    all.setAttribute('aria-pressed', String(!state.filterGenre));
    all.textContent = `ALL${state.tracks.length}`;
    all.addEventListener('click', () => { state.filterGenre = null; buildGenres(); buildRows(); });
    el.genres.appendChild(all);

    for (const [g, n] of [...counts].sort((a, b) => b[1] - a[1])) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'chip';
      const tint = state.tracks.find((t) => t.genre === g).tint;
      b.style.setProperty('--tint', tint);
      b.setAttribute('aria-pressed', String(state.filterGenre === g));
      b.innerHTML = `${g.toUpperCase()}<span class="chip__n">${n}</span>`;
      b.addEventListener('click', () => {
        state.filterGenre = state.filterGenre === g ? null : g;
        buildGenres(); buildRows();
      });
      el.genres.appendChild(b);
    }
  }

  el.search.addEventListener('input', () => { state.query = el.search.value; buildRows(); });
  el.sort.addEventListener('change', () => { state.sort = el.sort.value; buildRows(); });

  /* ── stats panels ────────────────────────────────────────────────── */
  function buildPanels() {
    const m = state.meta;
    const hours = m.total_ms / 3600000;
    const totalPlays = state.tracks.reduce((a, t) => a + t.plays, 0);

    const genreCount = new Map();
    for (const t of state.tracks) genreCount.set(t.genre, (genreCount.get(t.genre) || 0) + 1);
    const maxG = Math.max(...genreCount.values());
    const top = [...state.tracks].sort((a, b) => b.plays - a.plays).slice(0, 3);

    const w = 30;
    const box = (title, body) => {
      const pad = ' ' + title + ' ';
      const side = Math.max(0, Math.floor((w - pad.length - 2) / 2));
      return '╔' + '═'.repeat(side) + pad + '═'.repeat(w - side - pad.length) + '╗\n' +
             body.replace(/^/gm, '║').replace(/$/gm, '║') + '\n' +
             '╚' + '═'.repeat(w + 1) + '╝';
    };

    el.panelWeather.textContent = box('PHANTOMTAPE SIGNAL WEATHER', [
      ' TRANSMISSIONS ......... ' + String(state.tracks.length).padStart(4),
      ' RUNTIME ............... ' + hours.toFixed(2) + ' HRS',
      ' TOTAL PLAYS ........... ' + totalPlays.toLocaleString().padStart(4),
      ' LISTENERS ............. ' + String(m.followers).padStart(4),
      '',
      ' ACTIVITY       ' + bar(0.82) + ' 82%',
      ' CHAOS INDEX    ' + bar(0.97) + ' 97%',
      '',
      ' FORECAST',
      '   [~] ALL SYSTEMS NOMINAL',
      '   [+] SIGNAL HELD SINCE 2026-05-23',
    ].join('\n'));

    el.panelGenome.textContent = box('TRANSMISSION GENOME', [
      ...[...genreCount].sort((a, b) => b[1] - a[1])
        .map(([g, n]) => ` ${g.padEnd(14)} ${bar(n / maxG, 14)} ${String(n).padStart(2)}`),
      '',
      ' HEAVY ROTATION',
      ...top.map((t, i) => `   ${i + 1}. ${t.title.slice(0, 20)}`),
    ].join('\n'));
  }

  function buildFooter() {
    const m = state.meta;
    el.links.innerHTML =
      'GITHUB ..... <b>@Nortaq-PlayNexus</b>   <a href="https://github.com/Nortaq-PlayNexus" target="_blank" rel="noopener">github.com/Nortaq-PlayNexus</a>\n' +
      'SOUNDCLOUD .. <b>DJ PHANTOMTAPE</b>      <a href="https://soundcloud.com/phantomtape" target="_blank" rel="noopener">soundcloud.com/phantomtape</a>\n' +
      'RELAY ...... <b>this broadcast</b>      ' + window.location.host + '\n' +
      'DISCORD .... <b>[ OFF AIR — <PHANTOMTAPE_P-10> ]</b>\n' +
      'YOUTUBE .... <b>[ OFF AIR — <PHANTOMTAPE_P-10> ]</b>';

    el.colophon.textContent =
      `${m.artist} · ${state.tracks.length} transmissions · ${m.followers} listeners · catalogue built ${m.built} · signal 103.7 FM`;
  }

  /* ── boot the whole thing ────────────────────────────────────────── */
  async function init() {
    try {
      const [cat, waves] = await Promise.all([
        fetch('data/catalogue.json').then((r) => r.json()),
        fetch('data/waveforms.json').then((r) => r.json()),
      ]);
      state.meta = cat.meta;
      state.tracks = cat.tracks;
      state.waves = waves;
    } catch (err) {
      el.bootLog.textContent = 'CATALOGUE LOAD FAILED — run: python tools/build_catalogue.py';
      return;
    }

    buildEq();
    drawEq();
    buildGenres();
    buildRows();
    buildPanels();
    buildFooter();
    markRow();

    // Arm the first track so the player is ready before you press play.
    load(0, false);
    state.ready = true;
    requestAnimationFrame(frame);
  }

  runBoot();
  init();
})();
