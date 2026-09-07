import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

function formatNaira(n) {
  return `₦${Number(n).toLocaleString("en-NG")}`;
}

function AvailabilityBadge({ request }) {
  if (request.status === "rejected") {
    return <span className="badge badge-status">Rejected</span>;
  }
  if (request.status === "pending") {
    return <span className="badge badge-status">Waiting for confirmation</span>;
  }
  // confirmed
  return request.listing_status === "live"
    ? <span className="badge badge-verified">Available, pay now</span>
    : <span className="badge badge-status">No longer available</span>;
}

export default function RenterPayments() {
  const [payments, setPayments] = useState([]);
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function load() {
    try {
      const [paymentsData, requestsData] = await Promise.all([
        api.myRentPayments(),
        api.myAvailabilityRequests(),
      ]);
      setPayments(paymentsData);
      // Requests that already turned into a rent payment are shown above instead.
      setRequests(requestsData.filter((r) => !r.consumed_at));
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

  async function confirmSatisfied(id) {
    if (!window.confirm("Confirm you've met the landlord, seen the house, and you're satisfied with it? This releases your payment to the landlord.")) return;
    setBusyId(id);
    setError("");
    try {
      await api.confirmInspection(id);
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

                {!p.is_renewal && (
                  p.inspection_confirmed_at ? (
                    <div className="banner banner-success" style={{ marginTop: 12 }}>
                      ✓ You confirmed this house on {new Date(p.inspection_confirmed_at).toLocaleDateString()}. Your payment has been released to the landlord.
                    </div>
                  ) : (
                    <div className="banner banner-info" style={{ marginTop: 12, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                      <span>Your payment is held until you confirm you've met the landlord, seen the house, and you're satisfied.</span>
                      <button className="btn btn-secondary" disabled={busyId === p.id} onClick={() => confirmSatisfied(p.id)}>
                        {busyId === p.id ? "Confirming…" : "Confirm the house is good"}
                      </button>
                    </div>
                  )
                )}

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

        <h2 style={{ color: "var(--teal)", marginTop: 32 }}>Availability requests</h2>
        <p className="text-muted">Houses you've asked about, and whether they're still available.</p>
        {requests.length === 0 ? (
          <p className="text-muted">No availability requests yet.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {requests.map((r) => (
              <div key={r.id} className="card" style={{ padding: 16, display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                <div>
                  <Link to={`/listings/${r.listing_id}`} style={{ fontWeight: 700 }}>{r.listing_title}</Link>
                  <div className="text-muted" style={{ fontSize: 13 }}>{r.listing_area}</div>
                  {r.status === "rejected" && r.rejection_reason && (
                    <div className="field-hint">{r.rejection_reason}</div>
                  )}
                </div>
                <AvailabilityBadge request={r} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
