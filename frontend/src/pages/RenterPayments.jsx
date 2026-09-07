import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

function formatNaira(n) {
  return `₦${Number(n).toLocaleString("en-NG")}`;
}

export default function RenterPayments() {
  const [payments, setPayments] = useState([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function load() {
    try {
      setPayments(await api.myRentPayments());
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function renew(id) {
    setBusyId(id);
    setError("");
    try {
      const initiated = await api.initiateRenewal(id);
      if (initiated.authorization_url) {
        window.location.href = initiated.authorization_url;
        return;
      }
      await api.verifyRenewal(id, initiated.reference);
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
        <h1 style={{ color: "var(--teal)" }}>My rentals</h1>
        <p className="text-muted">Properties you've paid rent on.</p>
        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}
        {payments.length === 0 ? (
          <p className="text-muted">No rentals yet.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {payments.map((p) => (
              <div key={p.id} className="card" style={{ padding: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                  <div>
                    <strong>{p.listing_title}</strong> · {p.landlord_name} ({p.landlord_phone})
                    <div className="text-muted" style={{ fontSize: 13 }}>{p.address}</div>
                    <div className="field-hint">
                      {p.status === "active"
                        ? `Tenancy runs until ${new Date(p.end_date).toLocaleDateString()}`
                        : `Tenancy ended ${new Date(p.end_date).toLocaleDateString()}`}
                    </div>
                  </div>
                  <span className={`badge ${p.status === "active" ? "badge-verified" : "badge-status"}`}>
                    {p.status === "active" ? "Active" : "Ended"}
                  </span>
                </div>
                <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                  <Link to={`/chat/${p.id}`} className="btn btn-secondary">Chat</Link>
                  <Link to={`/renter/payments/${p.id}/receipt`} className="btn btn-ghost">Receipt</Link>
                  {p.status === "active" && (
                    <button className="btn btn-ghost" disabled={busyId === p.id} onClick={() => renew(p.id)}>
                      {busyId === p.id ? "Processing…" : `Renew: ${formatNaira(p.rent_amount_ngn)} (rent only)`}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
