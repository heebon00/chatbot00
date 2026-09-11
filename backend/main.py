import threading
import time
import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import db

load_dotenv() # .env의 키를 추출하는 함수
db.init_db()

# Render 슬립타임 방어 설정 (백엔드 자체 실행)
# Render는 15분 동안 외부 인바운드 요청이 없으면 슬립(Spin-down)에 들어갑니다.
# 백엔드 서버 자체가 10분(600초)마다 자신의 /health 엔드포인트를 호출하여 슬립을 원천 방어합니다.
RENDER_EXTERNAL_URL = (
    os.getenv("RENDER_EXTERNAL_URL")
    or os.getenv("KEEP_ALIVE_URL")
    or "https://chatbot00-back.onrender.com"
)
PING_INTERVAL = int(os.getenv("PING_INTERVAL", "600"))  # 기본 10분 (600초)

def keep_alive_worker():
    """외부 서비스 없이 백엔드 자체적으로 10분마다 핑을 보내 슬립을 막는 데몬 스레드"""
    time.sleep(5)  # 서버 부팅 대기
    health_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/health"
    print(f"[Keep-Alive] 백엔드 자체 슬립 방어 스레드 가동: {health_url} (간격: {PING_INTERVAL}초)", flush=True)

    while True:
        try:
            res = requests.get(health_url, timeout=30)
            print(f"[Keep-Alive] 자체 핑 성공 ({res.status_code}): {health_url}", flush=True)
        except Exception as e:
            print(f"[Keep-Alive] 자체 핑 전송 실패 (다음 주기 재시도): {e}", flush=True)
        time.sleep(PING_INTERVAL)

# 백엔드 프로세스 시작 시 백그라운드 데몬 스레드로 즉시 실행 (서버 종료 시 함께 종료)
threading.Thread(target=keep_alive_worker, daemon=True).start()

app = FastAPI()
app.add_middleware(                                 
    CORSMiddleware,                                 
    allow_origins=["*"],                           
    allow_methods=["*"],                            
    allow_headers=["*"],                            
)                                                   


class Msg(BaseModel):                               
    text: str     

class Title(BaseModel):
    title: str

HF_URL = "https://router.huggingface.co/v1/chat/completions"
HF_MODEL = "Qwen/Qwen3-4B-Instruct-2507"

def ask_ai(messages_or_text) -> str:
    token = os.getenv("HF_TOKEN")
    if isinstance(messages_or_text, str):
        messages = [{"role": "user", "content": messages_or_text}]
    else:
        messages = messages_or_text

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "model": HF_MODEL,
        "messages": messages,
        "max_tokens": 300,
    }
    res = requests.post(HF_URL, headers=headers, json=payload, timeout=60)
    if not res.ok:
        raise RuntimeError(f"HF API error: {res.status_code} {res.text}")
    data = res.json()
    if "choices" not in data or not data["choices"]:
        raise RuntimeError(f"HF API returned unexpected payload: {data}")
    return data["choices"][0]["message"]["content"]

def build_history(session_id):
    rows = db.read_messages(session_id)
    return [
        {"role": "user" if r["role"] == "user" else "assistant", "content": r["text"]}
        for r in rows
    ]

@app.get("/")
@app.get("/health")
@app.get("/ping")
def health_check():
    """Render 슬립 방지 및 서버 상태 확인 엔드포인트"""
    return {"status": "ok", "message": "pong"}

@app.post("/chat")
def chat(msg: Msg):
    reply = ask_ai([{"role": "user", "content": msg.text}])
    return {"reply": reply}

@app.get("/sessions")
def list_sessions():
    return db.read_sessions()

@app.post("/sessions")
def new_session():
    session_id = db.create_session()
    return {"id": session_id, "title": "새 대화"}

#Read
@app.get("/sessions/{session_id}/messages")
def read_messages(session_id: int):
    messages = db.read_messages(session_id)
    return {"messages": messages}


@app.get("/sessions/{session_id}/massages")
def read_messages(session_id: int):
    messages = db.read_messages(session_id)
    return {"messages": messages}

@app.post("/sessions/{session_id}/messages")
def send_message(session_id: int, msg: Msg):
    first = db.count_messages(session_id) == 0
    db.create_message(session_id, "user", msg.text)
    if first:
        db.update_session(session_id, msg.text[:20])
    reply = ask_ai(build_history(session_id))
    db.create_message(session_id, "bot", reply)
    return {"reply": reply}

#Update
@app.put("/sessions/{session_id}")
def rename_session(session_id: int, body: Title):
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="제목이 비어 있습니다")
    if db.update_session(session_id, title) == 0:
        raise HTTPException(status_code=404, detail="해당 대화가 없습니다")
    return {"id": session_id, "title": title}

#Delete
@app.delete("/sessions/{session_id}")
def remove_session(session_id: int):
    if db.delete_session(session_id) == 0:
        raise HTTPException(status_code=404, detail="해당 대화가 없습니다")
    return {"deleted": session_id}