import { useEffect, useState } from "react";
import { api } from "../api/client";

function formatNaira(n) {
  return `₦${Number(n).toLocaleString("en-NG")}`;
}

export default function AdminPayouts() {
  const [queue, setQueue] = useState([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function load() {
    try {
      setQueue(await api.payoutsQueue());
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function markPaid(id) {
    setBusyId(id);
    try {
      const payout_reference = window.prompt("Payout reference (optional, e.g. bank transfer ref):") || undefined;
      await api.markPayoutPaid(id, { payout_reference });
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
        <h1 style={{ color: "var(--teal)" }}>Payouts</h1>
        <p className="text-muted">
          Send each landlord's share by bank transfer yourself, then mark it paid here.
        </p>

        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

        {queue.length === 0 ? (
          <p className="text-muted">Nothing awaiting payout 🎉</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {queue.map((p) => (
              <div key={p.rent_payment_id} className="card" style={{ padding: 16, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
                <div>
                  <strong>{p.listing_title}</strong> · {p.landlord_name}
                  <div className="text-muted" style={{ fontSize: 13 }}>
                    {p.bank_name ? `${p.bank_name} · ${p.bank_account_number} · ${p.bank_account_name}` : "No bank details on file yet"}
                  </div>
                  <div style={{ fontSize: 13, marginTop: 4 }}>
                    Rent {formatNaira(p.rent_amount_ngn)}
                    {p.agreement_fee_ngn > 0 && <> + agreement fee {formatNaira(p.agreement_fee_ngn)}</>}.{" "}
                    <strong>Pay landlord {formatNaira(p.landlord_payout_ngn)}</strong>
                    {p.commission_ngn > 0 && <span className="text-muted"> (commission {formatNaira(p.commission_ngn)} kept by Wakaless)</span>}
                  </div>
                </div>
                <button className="btn btn-secondary" disabled={busyId === p.rent_payment_id} onClick={() => markPaid(p.rent_payment_id)}>
                  Mark paid out
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
