import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function ChatThread() {
  const { id } = useParams();
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const latestTimestamp = useRef(null);
  const bottomRef = useRef(null);

  async function poll() {
    try {
      const since = latestTimestamp.current || undefined;
      const fresh = await api.chatMessages(id, since);
      if (fresh.length) {
        // Dedupe by id: overlapping polls (or React dev double-invoke) can
        // otherwise fetch the same "since" window twice and duplicate messages.
        setMessages((prev) => {
          const seen = new Set(prev.map((m) => m.id));
          const toAdd = fresh.filter((m) => !seen.has(m.id));
          return toAdd.length ? [...prev, ...toAdd] : prev;
        });
        latestTimestamp.current = fresh[fresh.length - 1].created_at;
      }
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    poll();
    const interval = setInterval(poll, 5000);
    return () => clearInterval(interval);
  }, [id]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function send(e) {
    e.preventDefault();
    if (!text.trim()) return;
    try {
      const sent = await api.sendChatMessage(id, text.trim());
      setMessages((prev) => [...prev, sent]);
      latestTimestamp.current = sent.created_at;
      setText("");
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 640 }}>
        <h1 style={{ color: "var(--teal)" }}>Chat</h1>
        {error && <div className="banner banner-error" style={{ marginBottom: 12 }}>{error}</div>}
        <div className="card" style={{ padding: 16, height: 420, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8, marginBottom: 12 }}>
          {messages.map((m) => {
            const mine = m.sender_id === user?.id;
            return (
              <div key={m.id} style={{ alignSelf: mine ? "flex-end" : "flex-start", maxWidth: "75%" }}>
                <div style={{
                  background: mine ? "var(--teal)" : "var(--cream)", color: mine ? "var(--white)" : "var(--ink)",
                  padding: "8px 12px", borderRadius: 12, fontSize: 14,
                }}>
                  {m.body}
                </div>
                <div className="text-muted" style={{ fontSize: 11, marginTop: 2, textAlign: mine ? "right" : "left" }}>
                  {new Date(m.created_at).toLocaleTimeString()}
                </div>
              </div>
            );
          })}
          <div ref={bottomRef} />
        </div>
        <form onSubmit={send} style={{ display: "flex", gap: 8 }}>
          <input style={{ flex: 1, border: "1.5px solid var(--border)", borderRadius: 10, padding: "11px 13px", fontSize: 15 }}
            value={text} onChange={(e) => setText(e.target.value)} placeholder="Type a message…" />
          <button className="btn btn-primary" type="submit">Send</button>
        </form>
      </div>
    </div>
  );
}
