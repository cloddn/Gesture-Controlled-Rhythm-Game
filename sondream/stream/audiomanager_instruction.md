# AudioManager JS API Instruction

## 개요
`AudioManager`는 브라우저에서 **배경음악(BGM)** 과 **효과음(SFX)** 을 저지연으로 재생하기 위한 전역 오디오 매니저입니다.

- BGM: 한 번에 **1개 트랙** 재생 (루프 가능), 트랙 전환 시 **페이드 지원**
- SFX: **여러 개 동시/연타 재생 가능**
- 오디오 리소스는 **이름(name) 기반**으로 등록 후 호출
- WebAudio API 기반

> ⚠️ 브라우저 자동재생 정책으로 인해  
> **최초 1회는 반드시 사용자 제스처(클릭/키입력) 안에서 `enable()` 호출이 필요**합니다.

---

## 빠른 시작 (권장 패턴)

```js
AudioManager.registerAll({
  bgm: {
    menu: "/static/stream/audio/bgm/menu.mp3",
    stage1: "/static/stream/audio/bgm/stage1.mp3",
  },
  sfx: {
    hit: "/static/stream/audio/sfx/hit.wav",
    miss: "/static/stream/audio/sfx/miss.wav",
    click: "/static/stream/audio/sfx/click.wav",
  }
});

await AudioManager.enable();

await AudioManager.preload({
  bgm: ["menu"],
  sfx: ["hit", "miss", "click"]
});

AudioManager.playBgm("menu", { fadeMs: 250 });
AudioManager.playSfx("hit");
```

---

## 핵심 개념
- 등록(Registry): 이름 기반 리소스 매핑
- 로드(Decode): fetch + decodeAudioData
- preload로 초기 지연 최소화

---

## 주요 API

### enable()
```js
await AudioManager.enable();
```

### registerAll()
```js
AudioManager.registerAll({ bgm, sfx });
```

### preload()
```js
await AudioManager.preload({ bgm: [], sfx: [] });
```

### playBgm()
```js
AudioManager.playBgm("stage1", { fadeMs: 400 });
```

### stopBgm()
```js
AudioManager.stopBgm({ fadeMs: 300 });
```

### playSfx()
```js
AudioManager.playSfx("hit", { rate: 1.02 });
```

### setVolume
```js
AudioManager.setBgmVolume(0.35);
AudioManager.setSfxVolume(0.9);
```

---

## 권장 사용 규칙
1. registerAll은 페이지 로딩 시 1회
2. enable은 유저 제스처 안에서 1회
3. preload는 게임 시작 전에
4. 이벤트 코드는 play 함수만 호출

---
