/* ══════════════════════════════════════════���═══════════════════════════
   PHANTOMTAPE // 103.7  --  player
   ══════════════════════════════════════════════════════════════════════ */
(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const audio = $('audio');

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
  };

  const state = {
    meta: null, tracks: [], waves: null,
    view: [], index: -1, filterGenre: null, query: '', sort: 'new',
    scrubbing: false, ready: false, ctx: null, analyser: null, srcNode: null,
    useWebAudio: false, rafEq: 0,
  };

  const fmt = (s) => {
    if (!isFinite(s) || s < 0) s = 0;
    const m = Math.floor(s / 60);
    return `${m}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  };
  const pad = (n) => String(n).padStart(2, '0');
  const bar = (v, w = 22) => '█'.repeat(Math.round(v * w)).padEnd(w, '░');

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
      const norm = w.map((v) => (v / max) * WAVE_MAX);
      waveCache = { id: t.id, data: norm };
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

    const dur = state.tracks[state.index].duration || 1;
    const pos = state.scrubbing ? state.scrubPos : audio.currentTime;
    const played = Math.max(0, Math.min(1, pos / dur));

    const bars = Math.max(48, Math.floor(cssW / 4));
    const step = cssW / bars;
    const bw = Math.max(1.4, step * 0.55);
    const isPlaying = !audio.paused && !audio.ended;

    for (let i = 0; i < bars; i++) {
      const from = Math.floor((i / bars) * data.length);
      const to = Math.max(from + 1, Math.floor(((i + 1) / bars) * data.length));
      let peak = 0;
      for (let k = from; k < to && k < data.length; k++) peak = Math.max(peak, data[k]);

      const h = Math.max(2, (peak / WAVE_MAX) * (cssH - 16));
      const x = i * step + (step - bw) / 2;
      const y = mid - h / 2;

      const t = i / bars;
      if (t <= played) {
        ctx.fillStyle = isPlaying ? '#b8ff1e' : '#8fbf1a';
        ctx.shadowColor = 'rgba(184,255,30,.55)';
        ctx.shadowBlur = 7;
      } else {
        ctx.fillStyle = '#22304c';
        ctx.shadowBlur = 0;
      }
      ctx.fillRect(x, y, bw, h);
    }
    ctx.shadowBlur = 0;

    ctx.strokeStyle = '#1e2a42';
    ctx.beginPath(); ctx.moveTo(0, mid); ctx.lineTo(cssW, mid); ctx.stroke();

    const px = played * cssW;
    ctx.strokeStyle = '#ff3b3b';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(px, 0); ctx.lineTo(px, cssH); ctx.stroke();
    ctx.lineWidth = 1;
  }

  /* ── seek ────────────────────────────────────────────────────────── */
  function posFromEvent(e) {
    const r = el.wave.getBoundingClientRect();
    const x = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
    return Math.max(0, Math.min(1, x / r.width));
  }

  const scrubStart = (e) => {
    if (state.index < 0 || !audio.duration) return;
    e.preventDefault();
    state.scrubbing = true;
    state.scrubPos = posFromEvent(e) * audio.duration;
    drawWave();
  };
  const scrubMove = (e) => {
    if (!state.scrubbing) return;
    e.preventDefault();
    state.scrubPos = posFromEvent(e) * audio.duration;
    drawWave();
  };
  const scrubEnd = (e) => {
    if (!state.scrubbing) return;
    e.preventDefault();
    state.scrubbing = false;
    const t = state.tracks[state.index];
    if (t && isFinite(state.scrubPos)) audio.currentTime = state.scrubPos;
  };

  el.wave.addEventListener('mousedown', scrubStart);
  window.addEventListener('mousemove', scrubMove);
  window.addEventListener('mouseup', scrubEnd);
  el.wave.addEventListener('touchstart', scrubStart, { passive: false });
  el.wave.addEventListener('touchmove', scrubMove, { passive: false });
  el.wave.addEventListener('touchend', scrubEnd);

  el.wave.addEventListener('keydown', (e) => {
    if (!isFinite(audio.duration)) return;
    const stepT = e.shiftKey ? 30 : 5;
    if (e.key === 'ArrowRight') { audio.currentTime = Math.min(audio.duration, audio.currentTime + stepT); e.preventDefault(); }
    if (e.key === 'ArrowLeft')  { audio.currentTime = Math.max(0, audio.currentTime - stepT); e.preventDefault(); }
  });

  /* ── web audio analyser (best effort) ────────────────────────────── */
  // Routing a media element through Web Audio is what powers the live EQ, but
  // it also means the browser now requires CORS on the stream: if a future
  // CDN host omits the header, the element goes silent instead of playing.
  // So pre-flight one byte per host before ever attaching the graph.
  const corsCache = new Map();

  async function corsOk(url) {
    const host = new URL(url).host;
    if (corsCache.has(host)) return corsCache.get(host);
    let ok = false;
    try {
      const r = await fetch(url, { headers: { Range: 'bytes=0-0' }, mode: 'cors' });
      ok = r.ok || r.status === 206;
      if (r.status === 206) { try { await r.arrayBuffer(); } catch (_) {} }
    } catch (_) {
      ok = false;
    }
    corsCache.set(host, ok);
    return ok;
  }

  async function initWebAudio(track) {
    if (state.ctx || !track) return;
    if (!(await corsOk(track.stream))) return;   // leave the element alone
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      state.ctx = new Ctx();
      state.srcNode = state.ctx.createMediaElementSource(audio);
      state.analyser = state.ctx.createAnalyser();
      state.analyser.fftSize = 128;
      state.analyser.smoothingTimeConstant = 0.72;
      state.srcNode.connect(state.analyser);
      state.analyser.connect(state.ctx.destination);
      state.freq = new Uint8Array(state.analyser.frequencyBinCount);
      state.useWebAudio = true;
    } catch (err) {
      state.analyser = null;
      state.useWebAudio = false;
    }
  }

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
    const playing = !audio.paused && !audio.ended && state.index >= 0;

    let data = null;
    if (playing && state.useWebAudio && state.analyser) {
      state.analyser.getByteFrequencyData(state.freq);
      data = state.freq;
    }

    const w = samples();
    for (let i = 0; i < state.eqBars.length; i++) {
      let v;
      if (!playing) {
        v = 0.05 + Math.random() * 0.03;
      } else if (data && data.some((n) => n > 0)) {
        const lo = Math.floor((i / state.eqBars.length) * data.length);
        const hi = Math.max(lo + 1, Math.floor(((i + 1) / state.eqBars.length) * data.length));
        let m = 0;
        for (let k = lo; k < hi; k++) m = Math.max(m, data[k]);
        v = m / 255;
      } else {
        // CORS blocked the analyser - drive the bars off the real waveform
        // window around the playhead instead of showing a dead display.
        const p = audio.currentTime / (state.tracks[state.index].duration || 1);
        const centre = Math.floor(p * w.length);
        const span = 40;
        const k = centre + (i - state.eqBars.length / 2) * 2.2;
        v = k >= 0 && k < w.length ? w[Math.floor(k)] / WAVE_MAX : 0;
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
    audio.src = t.stream;
    audio.load();
    initWebAudio(t);

    el.art.src = t.artwork || '';
    el.art.alt = t.title;
    el.eyebrow.textContent = `▲ ON AIR — TRANSMISSION ${String(t.n).padStart(3, '0')} / ${state.meta.track_count}`;
    el.title.textContent = t.title;
    el.meta.innerHTML =
      `<span class="chip" style="--tint:${t.tint}">${t.genre}</span> · ${fmt(t.duration)} · ` +
      `${t.plays.toLocaleString()} plays · ${t.likes.toLocaleString()} likes · ${t.released}`;
    el.sc.href = t.permalink;
    el.onairLabel.textContent = 'LOCKED';
    el.tEnd.textContent = fmt(t.duration);

    markRow();
    drawWave();

    if (autoplay) {
      const p = audio.play();
      if (p && p.catch) p.catch(() => setPlayGlyph(false));
    }
  }

  function toggle() {
    if (state.index < 0) { load(0, true); return; }
    if (audio.paused) {
      if (state.ctx && state.ctx.state === 'suspended') state.ctx.resume();
      audio.play().catch(() => setPlayGlyph(false));
    } else {
      audio.pause();
    }
  }

  function next() { load((state.index + 1) % state.tracks.length, true); }
  function prev() {
    if (audio.currentTime > 3) { audio.currentTime = 0; return; }
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
  el.vol.addEventListener('input', () => { audio.volume = el.vol.value / 100; });

  /* ── audio events ────────────────────────────────────────────────── */
  audio.addEventListener('play',  () => setPlayGlyph(true));
  audio.addEventListener('pause', () => setPlayGlyph(false));
  audio.addEventListener('ended', next);
  audio.addEventListener('loadedmetadata', () => {
    const t = state.tracks[state.index];
    if (t && isFinite(audio.duration) && Math.abs(audio.duration - t.duration) > 2) {
      t.duration = Math.round(audio.duration);
      el.tEnd.textContent = fmt(t.duration);
    }
    drawWave();
  });
  audio.addEventListener('error', () => {
    el.eyebrow.textContent = '▲ STREAM UNAVAILABLE — PRESIGNED URL EXPIRED, REBUILD CATALOGUE';
    el.onairLabel.textContent = 'FAULT';
  });

  /* ── render loop ─────────────────────────────────────────────────── */
  function frame() {
    requestAnimationFrame(frame);
    if (state.index < 0) return;
    const d = audio.duration;
    if (state.scrubbing) return;
    el.tNow.textContent = fmt(audio.currentTime);
    el.tLeft.textContent = fmt((isFinite(d) ? d : 0) - audio.currentTime);
    if (isFinite(d) && d > 0) {
      const p = Math.min(100, (audio.currentTime / d) * 100);
      el.wave.setAttribute('aria-valuenow', String(Math.round(p)));
    }
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

    audio.volume = el.vol.value / 100;
    buildEq();
    drawEq();
    buildGenres();
    buildRows();
    buildPanels();
    buildFooter();
    markRow();

    // Preload the first track so the player is armed before you press play.
    load(0, false);
    state.ready = true;
    requestAnimationFrame(frame);
  }

  runBoot();
  init();
})();
