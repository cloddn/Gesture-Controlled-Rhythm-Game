// stream/static/stream/js/audio.js
// API (이벤트 작성자용)
//   await AudioManager.enable();                 // 유저 제스처 안에서 1회
//   AudioManager.playBgm("stage1", { fadeMs: 300 });
//   AudioManager.stopBgm({ fadeMs: 200 });
//   AudioManager.playSfx("hit");
//   AudioManager.playSfx("perfect", { volume: 1.0, rate: 1.05 });
//   AudioManager.setMasterVolume(1.0);
//   AudioManager.setBgmVolume(0.35);
//   AudioManager.setSfxVolume(0.9);

window.AudioManager = (() => {
  let ctx = null;

  // Gain graph: [master] -> destination
  let masterGain = null;
  let bgmGain = null;
  let sfxGain = null;

  // registry: name -> url
  const bgmRegistry = new Map();
  const sfxRegistry = new Map();

  // decoded buffers: name -> AudioBuffer
  const bgmBuffers = new Map();
  const sfxBuffers = new Map();

  let enabled = false;
  let loadingPromise = null;

  // Current BGM
  let bgmSource = null;
  let bgmName = null;

  function clamp01(x) {
    x = Number(x);
    if (Number.isNaN(x)) return 0;
    return Math.max(0, Math.min(1, x));
  }

  function now() {
    return ctx ? ctx.currentTime : 0;
  }

  async function fetchBuffer(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load audio: " + url);
    const arr = await res.arrayBuffer();
    return await ctx.decodeAudioData(arr);
  }

  function registerBgm(name, url) {
    bgmRegistry.set(name, url);
  }

  function registerSfx(name, url) {
    sfxRegistry.set(name, url);
  }

  function registerAll({ bgm = {}, sfx = {} }) {
    Object.entries(bgm).forEach(([k, v]) => registerBgm(k, v));
    Object.entries(sfx).forEach(([k, v]) => registerSfx(k, v));
  }

  async function loadBgm(name) {
    if (!bgmRegistry.has(name)) {
      throw new Error(`BGM '${name}' not registered`);
    }
    if (bgmBuffers.has(name)) return;
    const buf = await fetchBuffer(bgmRegistry.get(name));
    bgmBuffers.set(name, buf);
  }

  async function loadSfx(name) {
    if (!sfxRegistry.has(name)) {
      throw new Error(`SFX '${name}' not registered`);
    }
    if (sfxBuffers.has(name)) return;
    const buf = await fetchBuffer(sfxRegistry.get(name));
    sfxBuffers.set(name, buf);
  }

  async function preload({ bgm = [], sfx = [] } = {}) {
    // 지정한 것만 미리 로드 (초기 로딩 최적화)
    for (const b of bgm) await loadBgm(b);
    for (const s of sfx) await loadSfx(s);
  }

  async function enable() {
    if (enabled) return true;
    if (loadingPromise) return loadingPromise;

    loadingPromise = (async () => {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      if (ctx.state === "suspended") await ctx.resume();

      masterGain = ctx.createGain();
      bgmGain = ctx.createGain();
      sfxGain = ctx.createGain();

      masterGain.gain.value = 1.0;
      bgmGain.gain.value = 0.35;
      sfxGain.gain.value = 0.9;

      // route: bgm -> master -> destination, sfx -> master -> destination
      bgmGain.connect(masterGain);
      sfxGain.connect(masterGain);
      masterGain.connect(ctx.destination);

      enabled = true;
      return true;
    })();

    return loadingPromise;
  }

  function ensureEnabled() {
    if (!enabled || !ctx) {
      console.warn("AudioManager not enabled yet. Call await AudioManager.enable() inside a user gesture.");
      return false;
    }
    return true;
  }

  function _fadeGain(gainNode, target, fadeMs) {
    if (!gainNode || !ctx) return;
    const t = now();
    const fadeSec = Math.max(0, (fadeMs || 0) / 1000);
    const current = gainNode.gain.value;

    // 부드럽게: 현재값에서 target으로
    gainNode.gain.cancelScheduledValues(t);
    gainNode.gain.setValueAtTime(current, t);
    gainNode.gain.linearRampToValueAtTime(target, t + fadeSec);
  }

  async function playBgm(name, { loop = true, fadeMs = 250, restart = false } = {}) {
    if (!ensureEnabled()) return;
    if (!restart && bgmName === name && bgmSource) return; // 이미 같은 트랙 재생 중이면 무시

    await loadBgm(name);
    const buf = bgmBuffers.get(name);

    // 페이드 아웃 후 교체
    if (bgmSource) {
      // 현재 bgmGain을 0으로 페이드
      _fadeGain(bgmGain, 0.0, fadeMs);
      const old = bgmSource;
      setTimeout(() => {
        try { old.stop(0); } catch (e) {}
        try { old.disconnect(); } catch (e) {}
      }, fadeMs + 30);
    }

    // 새 트랙 시작 전에 gain 복구 스케줄
    _fadeGain(bgmGain, clamp01(bgmGain.gain.value), 0); // 현재 값 기준 정리
    // 바로 0에서 시작해서 fade-in
    const prevVol = bgmGain.gain.value;
    bgmGain.gain.value = 0.0;

    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.loop = loop;
    src.connect(bgmGain);
    src.start(0);

    bgmSource = src;
    bgmName = name;

    // fade-in
    _fadeGain(bgmGain, prevVol === 0 ? 0.35 : prevVol, fadeMs);

    src.onended = () => {
      // 루프가 false면 끝났을 때 정리
      if (bgmSource === src) {
        try { src.disconnect(); } catch (e) {}
        bgmSource = null;
        bgmName = null;
      }
    };
  }

  function stopBgm({ fadeMs = 200 } = {}) {
    if (!ensureEnabled()) return;
    if (!bgmSource) return;

    const src = bgmSource;
    bgmSource = null;
    bgmName = null;

    _fadeGain(bgmGain, 0.0, fadeMs);
    setTimeout(() => {
      try { src.stop(0); } catch (e) {}
      try { src.disconnect(); } catch (e) {}
      // 볼륨은 원래대로 복구(다음 재생 대비)
      // (사용자가 setBgmVolume로 바꾼 값을 유지해야 해서 gain.value 자체는 건드리지 않음)
    }, fadeMs + 30);
  }

  async function playSfx(name, { volume = 1.0, rate = 1.0 } = {}) {
    if (!ensureEnabled()) return;
    await loadSfx(name);

    const buf = sfxBuffers.get(name);
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = Math.max(0.25, Math.min(4.0, Number(rate) || 1.0));

    // per-sfx volume node
    const g = ctx.createGain();
    g.gain.value = clamp01(volume);

    src.connect(g);
    g.connect(sfxGain);

    src.start(0);
    src.onended = () => {
      try { src.disconnect(); } catch (e) {}
      try { g.disconnect(); } catch (e) {}
    };
  }

  // Volume controls
  function setMasterVolume(v) {
    if (!masterGain) return;
    masterGain.gain.value = clamp01(v);
  }
  function setBgmVolume(v) {
    if (!bgmGain) return;
    // 현재 페이드 스케줄이 있으면 즉시 반영되게 cancel 후 설정
    const t = now();
    bgmGain.gain.cancelScheduledValues(t);
    bgmGain.gain.setValueAtTime(clamp01(v), t);
  }
  function setSfxVolume(v) {
    if (!sfxGain) return;
    const t = now();
    sfxGain.gain.cancelScheduledValues(t);
    sfxGain.gain.setValueAtTime(clamp01(v), t);
  }

  function listBgm() { return Array.from(bgmRegistry.keys()); }
  function listSfx() { return Array.from(sfxRegistry.keys()); }

  return {
    enable,

    registerBgm,
    registerSfx,
    registerAll,

    preload,       // 선택 로드
    loadBgm,
    loadSfx,

    playBgm,
    stopBgm,
    playSfx,

    setMasterVolume,
    setBgmVolume,
    setSfxVolume,

    listBgm,
    listSfx,
  };
})();
