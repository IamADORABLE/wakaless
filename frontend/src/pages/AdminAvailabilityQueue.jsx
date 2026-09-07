import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export default function AdminAvailabilityQueue() {
  const [queue, setQueue] = useState([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function load() {
    try {
      setQueue(await api.availabilityQueue());
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function decide(id, approve) {
    setBusyId(id);
    try {
      const rejection_reason = approve ? undefined : window.prompt("Reason for rejection (shown to the renter):") || "Landlord confirmed the property is no longer available.";
      await api.reviewAvailability(id, { approve, rejection_reason });
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
        <h1 style={{ color: "var(--teal)" }}>Availability requests</h1>
        <p className="text-muted">
          A renter wants to pay for one of these. Contact the landlord directly (they've also been emailed/texted), then confirm here.
        </p>

        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

        {queue.length === 0 ? (
          <p className="text-muted">Nothing waiting for review 🎉</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {queue.map((r) => (
              <div key={r.id} className="card" style={{ padding: 16, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
                <div>
                  <Link to={`/listings/${r.listing_id}`} style={{ fontWeight: 700 }}>{r.listing_title}</Link>
                  <div className="text-muted" style={{ fontSize: 13 }}>Renter: {r.renter_name} · {r.renter_phone}</div>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn btn-ghost" disabled={busyId === r.id} onClick={() => decide(r.id, false)}>Not available</button>
                  <button className="btn btn-secondary" disabled={busyId === r.id} onClick={() => decide(r.id, true)}>Confirmed available</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
