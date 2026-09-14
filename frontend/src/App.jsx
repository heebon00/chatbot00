import { useState, useEffect } from "react";
import plusIcon from "./assets/icons/plus.svg";
import editIcon from "./assets/icons/edit.svg";
import sendIcon from "./assets/icons/send-button.svg";

const DEFAULT_API = "https://chatbot00-back.onrender.com";
const API = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:8002"
  : DEFAULT_API;

export default function App() {
  const [sessions, setSession] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [editId, setEditId] = useState(null);
  const [editTitle, setEditTitle] = useState("");

  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const request = async (url, options) => {
    const res = await fetch(url, options);
    if (!res.ok) {
      throw new Error(`서버 오류 (${res.status})`);
    }
    return res.json();
  };

  // func
  // 세션데이터 로드
  const loadSessions = async () => {
    const data = await request(`${API}/sessions`);
    const nextSessions = Array.isArray(data) ? data : data.sessions ?? [];
    setSession(nextSessions);
    return nextSessions;
  };

  //세션의 채팅기록 로드
  const loadMsg = async (id) => {
    if (!id) {
      setMsgs([]);
      return;
    }
    const data = await request(`${API}/sessions/${id}/messages`);
    setMsgs(Array.isArray(data) ? data : data.messages ?? []);
  };
  //선택된 세션 아이디 저장
  const openSession = (id) => {
    setSessionId(id);
    loadMsg(id);
  };

  //새로운 세션 추가
  const newSession = async () => {
    const data = await request(`${API}/sessions`, { method: "POST" });
    await loadSessions();
    setSessionId(data.id);
    setMsgs([]);
  };

  // 리액트 컴포넌트 상태에 따라 함수실행을 제어
  useEffect(() => {
    const initialize = async () => {
      try {
        const list = await loadSessions();
        if (list.length > 0) {
          setSessionId(list[0].id);
          await loadMsg(list[0].id);
        }
      } catch (requestError) {
        setError(`백엔드에 연결할 수 없습니다. ${requestError.message}`);
      }
    };

    void initialize();
  }, []);

  // 수정할 세션의 아이디, 타이틀로 선택
  const startRename = (s) => {
    setEditId(s.id);
    setEditTitle(s.title);
  };
  // 세션 타이틀 수정
  const saveTitle = async (id) => {
    await request(`${API}/sessions/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: editTitle }),
    });
    setEditId(null);
    await loadSessions();
  };
  // 세션삭제
  const removeSession = async (id) => {
    await request(`${API}/sessions/${id}`, { method: "DELETE" });
    const list = await loadSessions();
    const next = list.length > 0 ? list[0].id : null;
    setSessionId(next);
    loadMsg(next);
  };
  //사용자의 메시지를 서버로 전달후 응답결과 반환
  const send = async () => {
    if (!input.trim() || !sessionId) return;
    const text = input;
    setInput("");
    setLoading(true);
    try {
      await request(`${API}/sessions/${sessionId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      await loadMsg(sessionId);
      await loadSessions();
    } catch (requestError) {
      setError(`메시지를 보내지 못했습니다. ${requestError.message}`);
    } finally {
      setLoading(false);
    }
  };

  //엔터키 입력시 메시지 전송
  const onKey = (e) => {
    if (e.key === "Enter") send();
  };

  return (
    <div className="app">
      <aside className="side">
        <p className="logo">askai</p>
        <button className="new" onClick={newSession}>
          <img src={plusIcon} alt="" />
          새 대화
        </button>
        <ul className="session-list">
          {sessions.map((s) => (
            <li key={s.id} className={s.id === sessionId ? "session on" : "session"}>
              {editId === s.id ? (
                <span className="rename">
                  <input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
                  <button onClick={() => saveTitle(s.id)}>저장</button>
                </span>
              ) : (
                <>
                  <button className="session-title" onClick={() => openSession(s.id)}>
                    {s.title}
                  </button>
                  <span className="session-tools">
                    <button onClick={() => startRename(s)} aria-label="이름 바꾸기">
                      <img src={editIcon} alt="" />
                    </button>
                    <button onClick={() => removeSession(s.id)}>삭제</button>
                  </span>
                </>
              )}
            </li>
          ))}
        </ul>
      </aside>

      <main className="chat">
        {error && <p className="error">{error}</p>}
        <div className="box">
          {msgs.length === 0 && !loading && (
            <div className="empty">
              <p className="empty-mark">A</p>
              <p className="empty-text">ask ai anything</p>
            </div>
          )}
          {msgs.map((m) => (
            <div key={m.id} className={m.role}>
              <p>{m.text}</p>
            </div>
          ))}
          {loading && <p className="loading">생각 중...</p>}
        </div>
        <div className="input-row">
          <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={onKey} placeholder="메시지를 입력하세요" />
          <button onClick={send} aria-label="전송">
            <img src={sendIcon} alt="" />
          </button>
        </div>
      </main>
    </div>
  );
}
