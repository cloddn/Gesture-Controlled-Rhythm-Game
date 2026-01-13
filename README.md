# 🎮 Gesture Controlled Rhythm Game 🎮

손 제스처 인식을 이용한 리듬 게임 프로젝트입니다.

---

## 🛠️ 세팅 방법 (Setup)

### 1️⃣ 가상환경 생성
Repository를 저장할 폴더에서 Git Bash 혹은 다른 shell을 열고 Python 가상환경을 생성합니다.

```bash
python -m venv venv
```

> 가상환경 이름(`venv`, 가장 뒤 venv만)은 원하는 이름으로 변경해도 됩니다.

---

### 2️⃣ Repository 클론
본인 계정으로 fork하고 하셔야 충돌 안 납니다.

```bash
git clone '  '
```

---

### 3️⃣ 가상환경 실행

**bash**
```bash
source venv/Scripts/activate
```

**Windows PowerShell**
```powershell
.\venv\Scripts\activate
```

---

### 4️⃣ 의존성 패키지 설치

```bash
cd Gesture-Controlled-Rhythm-Game
pip install -r requirements.txt
```

---

### 5️⃣ VS Code에서 작업
VS Code에서 해당 폴더를 열고 원하는 작업을 진행합니다.

---

### 6️⃣ 서버 실행

```bash
python manage.py runserver
```

브라우저 접속:
```
http://127.0.0.1:8000/
```

---

### 7️⃣ requirements.txt 갱신 (필수)

```bash
pip freeze > requirements.txt
```

---

### 8️⃣ 가상환경 종료

```bash
deactivate
```

### 새로운 앱과 URL 페이지를 추가한 경우
새로운 기능과 URL페이지를 추가한 경우 아래에 예시와 같은 형식으로 추가해주시면 감사하겠습니다.
ai 친구들에게 쟝고로 하고 있고, 기능추가하고 싶다라고 이야기하면 어떤 파일에 어떤 컴포넌트를 추가해야하는지 잘 이야기해 줍니다.

---

## 🎮 사용 방법 (How to Use)

자세한 사용 방법은 아래 블로그를 참고해주세요.

https://velog.io/@dltmdgus9661/series/Django
---

## 현재 존재하는 url page

http://127.0.0.1:8000/ #mainpage
http://127.0.0.1:8000/video_feed #video streaming


## 📌 Notes
- 협업 시 `requirements.txt` 동기화를 꼭 확인해주세요.
- 문제가 생기면 가상환경을 새로 생성하는 것을 권장합니다.
