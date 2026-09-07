import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export default function AdminChats() {
  const [threads, setThreads] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => { api.adminChatThreads().then(setThreads).catch((e) => setError(e.message)); }, []);

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 640 }}>
        <h1 style={{ color: "var(--teal)" }}>Chats</h1>
        <p className="text-muted">Every renter-landlord conversation, for oversight. Read-only.</p>
        {error && <div className="banner banner-error">{error}</div>}
        {threads.length === 0 ? (
          <p className="text-muted">No conversations yet.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {threads.map((t) => (
              <Link key={t.rent_payment_id} to={`/admin/chats/${t.rent_payment_id}`} className="card" style={{ padding: 16, display: "block" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <strong>{t.renter_name} ↔ {t.landlord_name}</strong>
                  {t.last_message_at && <span className="text-muted" style={{ fontSize: 12 }}>{new Date(t.last_message_at).toLocaleString()}</span>}
                </div>
                <div className="text-muted" style={{ fontSize: 13 }}>{t.listing_title} · {t.message_count} messages</div>
                {t.last_message_preview && <div style={{ fontSize: 14, marginTop: 4 }}>{t.last_message_preview}</div>}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
