import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export default function ChatThreads() {
  const [threads, setThreads] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => { api.chatThreads().then(setThreads).catch((e) => setError(e.message)); }, []);

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 640 }}>
        <h1 style={{ color: "var(--teal)" }}>Messages</h1>
        {error && <div className="banner banner-error">{error}</div>}
        {threads.length === 0 ? (
          <p className="text-muted">No conversations yet. They open once a rent payment goes through.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {threads.map((t) => (
              <Link key={t.rent_payment_id} to={`/chat/${t.rent_payment_id}`} className="card" style={{ padding: 16, display: "block" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <strong>{t.other_party_name}</strong>
                  {t.last_message_at && <span className="text-muted" style={{ fontSize: 12 }}>{new Date(t.last_message_at).toLocaleString()}</span>}
                </div>
                <div className="text-muted" style={{ fontSize: 13 }}>{t.listing_title}</div>
                {t.last_message_preview && <div style={{ fontSize: 14, marginTop: 4 }}>{t.last_message_preview}</div>}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
