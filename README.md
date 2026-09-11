# 🤖 Chatbot00

Hugging Face LLM 기반의 실시간 풀스택 AI 챗봇 서비스입니다.  
FastAPI 백엔드와 React/Vite 프론트엔드로 구성되어 있으며, SQLite를 활용한 세션 관리 및 Render 무료 티어 슬립 방어(Keep-Alive) 메커니즘이 내장되어 있습니다.

---

## 📌 실측 성능 및 시스템 지표 (Actual Measured Values)

| 항목 | 구분 | 실측값 (Measured) | 비고 |
|---|---|---|---|
| **AI 모델 응답 시간** | `/chat` (Hugging Face) | **~1.32초 (1,325ms)** | `Qwen/Qwen3-4B-Instruct-2507` (max_tokens: 300) |
| **로컬 헬스체크 응답** | `GET /health` | **~10ms 미만 (웜 상태)** / 239ms (첫 요청) | FastAPI 초경량 엔드포인트 |
| **로컬 세션 목록 조회** | `GET /sessions` | **~8ms** | SQLite 인메모리 커넥션 풀 |
| **Render 프로덕션 조회** | `GET /sessions` | **~409ms** | Render 배포 환경 실측 |
| **프론트엔드 빌드 시간** | `vite build` | **~476ms** | Vite 8.2.2 + React Compiler 19 |
| **프론트엔드 번들 크기** | JS 번들 | **193.01 kB (Gzip: 60.93 kB)** | `dist/assets/index-*.js` |
| | CSS 번들 | **1.36 kB (Gzip: 0.58 kB)** | `dist/assets/index-*.css` |
| | HTML | **0.45 kB (Gzip: 0.29 kB)** | `dist/index.html` |
| **데이터베이스 용량** | `chat.db` (SQLite) | **28.67 KB** | 세션 16개 및 대화 메시지 보관 중 |
| **Render 슬립 방어 주기** | 백엔드 자체 핑 | **600초 (10분)** | Render 15분 절전(Spin-down) 원천 방어 |

---

## 🏗️ 시스템 아키텍처

```
[ Frontend: React 19 + Vite ] (Port 5173)
           │
           │ HTTP (REST API)
           ▼
[ Backend: FastAPI ] (Port 8000 / Render)
    ├── [ SQLite: chat.db ] (세션/메시지 영속화)
    ├── [ Keep-Alive Thread ] ──(10분 주기 자체 핑)──► [ GET /health ]
    └── [ Hugging Face Router API ] ──► Qwen3-4B-Instruct
```

---

## 🛠️ 기술 스택 (Tech Stack)

### Backend
- **Framework**: FastAPI `0.141.1`
- **ASGI Server**: Uvicorn `0.52.4`
- **Language**: Python `3.14.7`
- **Database**: SQLite3 (`backend/chat.db`)
- **LLM Engine**: Hugging Face Serverless Router (`Qwen/Qwen3-4B-Instruct-2507`)
- **HTTP Client**: Requests `2.34.2`
- **Deployment**: Render Web Service (`https://chatbot00-back.onrender.com`)

### Frontend
- **Framework**: React `19.2.8`
- **Build Tool**: Vite `8.2.2`
- **Compiler**: React Compiler (`babel-plugin-react-compiler` 1.0.0, Target: 19)
- **Styling**: CSS Modules / Custom Responsive Styles

---

## 🛡️ Render 슬립타임 방어 시스템 (Keep-Alive)

Render 무료 플랜은 **15분간 외부 인바운드 HTTP 요청이 없으면 서버를 절전 모드(Spin-down)**로 전환하여 이후 첫 접속 시 30~50초의 콜드 스타트 지연이 발생합니다.

Chatbot00은 외부 모니터링 도구 없이 **백엔드 자체 데몬 스레드**로 이를 원천 방어합니다:
1. 서버 부팅 시 `threading.Thread(target=keep_alive_worker, daemon=True)` 자동 가동
2. **10분(600초)** 주기로 자신의 공개 도메인(`https://chatbot00-back.onrender.com/health`)에 GET 요청 전송
3. Render 라우터가 인바운드 트래픽으로 인식하여 15분 슬립 타이머를 계속 0으로 리셋
4. 초경량 `/health` 엔드포인트 응답으로 월간 인스턴스 시간 및 서버 리소스 소모 최소화

---

## 📡 API 엔드포인트 명세

| Method | Endpoint | 설명 | 요청 본문 / 파라미터 | 응답 예시 |
|---|---|---|---|---|
| `GET` | `/` | 서버 상태 기본 확인 | - | `{"status": "ok", "message": "pong"}` |
| `GET` | `/health`, `/ping` | 슬립 방어 및 헬스체크 | - | `{"status": "ok", "message": "pong"}` |
| `GET` | `/sessions` | 대화 세션 목록 조회 | - | `[{"id": 1, "title": "새 대화", ...}]` |
| `POST` | `/sessions` | 새 대화 세션 생성 | - | `{"id": 18, "title": "새 대화"}` |
| `GET` | `/sessions/{id}/messages` | 특정 세션의 대화 내역 | `id: int` | `{"messages": [...]}` |
| `POST` | `/sessions/{id}/messages` | 메시지 전송 및 AI 응답 | `{"text": "안녕하세요"}` | `{"reply": "안녕하세요! 무엇을..."}` |
| `PUT` | `/sessions/{id}` | 세션 제목 변경 | `{"title": "새 제목"}` | `{"id": 1, "title": "새 제목"}` |
| `DELETE` | `/sessions/{id}` | 세션 삭제 | `id: int` | `{"deleted": 1}` |
| `POST` | `/chat` | 단발성 AI 질의 | `{"text": "질문"}` | `{"reply": "답변"}` |

---

## 🚀 로컬 실행 방법

### 1. 백엔드 (FastAPI)
```bash
cd backend

# 가상환경 활성화 (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# 환경 변수 설정 (.env)
# HF_TOKEN=your_huggingface_token

# 서버 실행 (포트 8000)
python -m uvicorn main:app --reload --port 8000
```
- Swagger API 문서: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. 프론트엔드 (React + Vite)
```bash
cd frontend

# 패키지 설치
npm install

# 개발 서버 실행 (포트 5173)
npm run dev

# 프로덕션 빌드
npm run build
```
- 브라우저 접속: [http://localhost:5173](http://localhost:5173)
