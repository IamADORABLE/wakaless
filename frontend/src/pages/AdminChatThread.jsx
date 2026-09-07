import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";

export default function AdminChatThread() {
  const { id } = useParams();
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => { api.adminChatMessages(id).then(setMessages).catch((e) => setError(e.message)); }, [id]);

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 640 }}>
        <h1 style={{ color: "var(--teal)" }}>Chat (read-only)</h1>
        {error && <div className="banner banner-error" style={{ marginBottom: 12 }}>{error}</div>}
        <div className="card" style={{ padding: 16, display: "flex", flexDirection: "column", gap: 8 }}>
          {messages.length === 0 ? (
            <p className="text-muted">No messages yet.</p>
          ) : messages.map((m) => (
            <div key={m.id} style={{ alignSelf: m.sender_role === "landlord" ? "flex-end" : "flex-start", maxWidth: "75%" }}>
              <div style={{
                background: m.sender_role === "landlord" ? "var(--teal)" : "var(--cream)",
                color: m.sender_role === "landlord" ? "var(--white)" : "var(--ink)",
                padding: "8px 12px", borderRadius: 12, fontSize: 14,
              }}>
                {m.body}
              </div>
              <div className="text-muted" style={{ fontSize: 11, marginTop: 2, textAlign: m.sender_role === "landlord" ? "right" : "left" }}>
                {m.sender_role} · {new Date(m.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
