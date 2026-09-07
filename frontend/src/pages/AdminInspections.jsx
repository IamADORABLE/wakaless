import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function AdminInspections() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.adminInspections().then(setRows).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="page">
      <div className="container">
        <h1 style={{ color: "var(--teal)" }}>Inspections</h1>
        <p className="text-muted">
          Renters confirm they've met the landlord and seen the house before their payment is released.
          A payout can't be marked paid until that happens here.
        </p>

        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

        {rows.length === 0 ? (
          <p className="text-muted">No first-time tenancies yet.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {rows.map((r) => (
              <div key={r.id} className="card" style={{ padding: 16, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
                <div>
                  <strong>{r.listing_title}</strong> · {r.renter_name} ({r.renter_phone})
                  <div className="text-muted" style={{ fontSize: 13 }}>
                    Landlord: {r.landlord_name} · Paid {new Date(r.paid_at).toLocaleDateString()}
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
                  <span className={`badge ${r.inspection_confirmed_at ? "badge-verified" : "badge-status"}`}>
                    {r.inspection_confirmed_at
                      ? `Satisfied ${new Date(r.inspection_confirmed_at).toLocaleDateString()}`
                      : "Awaiting confirmation"}
                  </span>
                  {r.payout_status === "paid_out" && <span className="text-muted" style={{ fontSize: 12 }}>Paid out</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
