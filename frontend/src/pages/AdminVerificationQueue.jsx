import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function AdminVerificationQueue() {
  const [queue, setQueue] = useState([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [selected, setSelected] = useState(null);

  async function load() {
    try {
      setQueue(await api.verificationQueue());
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  useEffect(() => {
    if (!selected) return;
    function onKey(e) { if (e.key === "Escape") setSelected(null); }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected]);

  async function decide(id, approve) {
    setBusyId(id);
    try {
      const rejection_reason = approve ? undefined : window.prompt("Reason for rejection (shown to the landlord):") || "Photo did not pass review.";
      await api.reviewVerification(id, { approve, rejection_reason });
      setSelected(null);
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
        <h1 style={{ color: "var(--teal)" }}>Landlord verification queue</h1>
        <p className="text-muted">
          There's no automated identity check. Review the landlord's photo below before approving.
        </p>

        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

        {queue.length === 0 ? (
          <p className="text-muted">Nothing waiting for review 🎉</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {queue.map((v) => (
              <div key={v.id} className="card" style={{ padding: 16, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
                <div
                  onClick={() => setSelected(v)}
                  style={{ display: "flex", alignItems: "center", gap: 16, cursor: "pointer", flex: 1 }}
                >
                  {v.photo_url && (
                    <img
                      src={api.fileUrl(v.photo_url)}
                      alt={`Photo submitted by ${v.full_name}`}
                      style={{ width: 72, height: 72, objectFit: "cover", borderRadius: 10, border: "1px solid var(--border)" }}
                    />
                  )}
                  <div>
                    <strong>{v.full_name}</strong>
                    <div className="text-muted" style={{ fontSize: 13 }}>{v.phone}</div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn btn-ghost" disabled={busyId === v.id} onClick={() => decide(v.id, false)}>Reject</button>
                  <button className="btn btn-secondary" disabled={busyId === v.id} onClick={() => decide(v.id, true)}>Approve</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selected && (
        <div
          onClick={() => setSelected(null)}
          style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)", zIndex: 300, display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="card"
            style={{ maxWidth: 480, width: "100%", maxHeight: "90vh", overflowY: "auto", padding: 24, position: "relative" }}
          >
            <button
              aria-label="Close"
              onClick={() => setSelected(null)}
              className="btn btn-ghost"
              style={{ position: "absolute", top: 12, right: 12, padding: "6px 12px", fontSize: 18, lineHeight: 1 }}
            >
              ✕
            </button>

            <h2 style={{ color: "var(--teal)", marginBottom: 4 }}>{selected.full_name}</h2>
            <div className="text-muted" style={{ marginBottom: 16 }}>
              {selected.phone} · {selected.email}
              {selected.submitted_at && <> · Submitted {new Date(selected.submitted_at).toLocaleString()}</>}
            </div>

            {selected.photo_url ? (
              <a href={api.fileUrl(selected.photo_url)} target="_blank" rel="noreferrer">
                <img
                  src={api.fileUrl(selected.photo_url)}
                  alt={`Photo submitted by ${selected.full_name}`}
                  style={{ width: "100%", maxHeight: 420, objectFit: "contain", borderRadius: 10, border: "1px solid var(--border)", background: "var(--bg)" }}
                />
              </a>
            ) : (
              <p className="text-muted">No photo was uploaded.</p>
            )}
            <p className="text-muted" style={{ fontSize: 13, marginTop: 8 }}>Click the photo to open it full size.</p>

            <div style={{ display: "flex", gap: 8, marginTop: 20 }}>
              <button className="btn btn-ghost btn-block" disabled={busyId === selected.id} onClick={() => decide(selected.id, false)}>Reject</button>
              <button className="btn btn-secondary btn-block" disabled={busyId === selected.id} onClick={() => decide(selected.id, true)}>Approve</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
