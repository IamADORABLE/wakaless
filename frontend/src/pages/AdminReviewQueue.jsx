import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function AdminReviewQueue() {
  const [queue, setQueue] = useState([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function load() {
    try {
      setQueue(await api.reviewQueue());
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function decide(id, approve) {
    setBusyId(id);
    try {
      const rejection_reason = approve ? undefined : window.prompt("Reason for rejection (shown to the landlord):") || "Did not pass review";
      await api.reviewListing(id, { approve, rejection_reason });
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="page">
      <div className="container">
        <h1 style={{ color: "var(--teal)" }}>Listing review queue</h1>
        <p className="text-muted">Manual review of ownership documents before a listing goes live (MVP scope).</p>

        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

        {queue.length === 0 ? (
          <p className="text-muted">Nothing waiting for review 🎉</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {queue.map((l) => (
              <div key={l.id} className="card" style={{ padding: 16, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                <div>
                  <strong>{l.title}</strong>
                  <div className="text-muted" style={{ fontSize: 13 }}>
                    {l.area} · ₦{l.rent_amount_ngn.toLocaleString("en-NG")}/{l.rent_duration_months}mo
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn btn-ghost" disabled={busyId === l.id} onClick={() => decide(l.id, false)}>Reject</button>
                  <button className="btn btn-secondary" disabled={busyId === l.id} onClick={() => decide(l.id, true)}>Approve</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
