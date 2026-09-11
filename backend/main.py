from fastapi import FastAPI, HTTPException                         
from fastapi.middleware.cors import CORSMiddleware  
from pydantic import BaseModel                      
import requests, os                                 
from dotenv import load_dotenv    
import db

load_dotenv() #.env의 키를 추출하는 함수 
app = FastAPI()
db.init_db()
print(app)
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