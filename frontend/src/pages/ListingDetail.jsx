import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import VerifiedBadge from "../components/VerifiedBadge";

function formatNaira(n) {
  return `₦${Number(n).toLocaleString("en-NG")}`;
}

const STATUS_BANNER = {
  rented: "This property has already been rented.",
  expired: "This listing is temporarily unavailable. The landlord is confirming it's still up for rent.",
  pending_review: "This listing is still awaiting admin review.",
  rejected: "This listing did not pass admin review.",
};

export default function ListingDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [listing, setListing] = useState(null);
  const [availability, setAvailability] = useState(null);
  const [payment, setPayment] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getListing(id).then(setListing).catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => {
    if (user?.role !== "renter") return;
    api.myRentPayments().then((rows) => {
      const active = rows.find((rp) => rp.listing_id === id && rp.status === "active");
      if (active) setPayment(active);
    }).catch(() => {});
    api.getAvailabilityStatus(id).then(setAvailability).catch(() => {});
  }, [id, user]);

  async function handleRequestAvailability() {
    setError("");
    setBusy(true);
    try {
      const result = await api.requestAvailability(id);
      setAvailability(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function handlePay() {
    setError("");
    setBusy(true);
    try {
      const initiated = await api.initiateRentPayment(id);
      if (initiated.authorization_url) {
        window.location.href = initiated.authorization_url;
        return;
      }
      const result = await api.verifyRentPayment(initiated.reference);
      setPayment(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (error && !listing) return <div className="page"><div className="container"><div className="banner banner-error">{error}</div></div></div>;
  if (!listing) return <div className="page"><div className="container"><p className="text-muted">Loading…</p></div></div>;

  return (
    <div className="page">
      <div className="container" style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 32 }}>
        <div>
          <div style={{ aspectRatio: "16/10", background: "#eee2c9", borderRadius: 12, overflow: "hidden", marginBottom: 16 }}>
            {listing.photos?.[0] ? (
              <img src={api.fileUrl(listing.photos[0])} alt={listing.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--muted)" }}>No photo yet</div>
            )}
          </div>
          <h1 style={{ margin: "0 0 6px" }}>{listing.title}</h1>
          <div style={{ marginBottom: 10 }}><VerifiedBadge verified={listing.verified_landlord} /></div>
          <p className="text-muted">{listing.area}</p>
          {listing.description && <p>{listing.description}</p>}
        </div>

        <div>
          <div className="card" style={{ padding: 20, marginBottom: 16, position: "sticky", top: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
              <span className="text-muted">Rent ({listing.rent_duration_months} months)</span>
              <strong className="money">{formatNaira(listing.rent_amount_ngn)}</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
              <span className="text-muted">Agreement fee</span>
              <strong className="money">{formatNaira(listing.agreement_fee_ngn)}</strong>
            </div>
            {!payment && (
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span className="text-muted">Commission</span>
                <strong className="money">{formatNaira(listing.commission_ngn)}</strong>
              </div>
            )}
            {!payment && (
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16, paddingTop: 8, borderTop: "1px dashed var(--border)" }}>
                <span>Total due now</span>
                <strong className="money">{formatNaira(listing.rent_amount_ngn + listing.agreement_fee_ngn + listing.commission_ngn)}</strong>
              </div>
            )}
            <p className="field-hint" style={{ marginTop: -8, marginBottom: 16 }}>
              Agreement fee and commission are charged once at move-in. Renewals are rent only.
            </p>
            <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "12px 0" }} />

            {listing.status !== "live" && !payment ? (
              <div className="banner banner-info">{STATUS_BANNER[listing.status] || "This listing is not currently available."}</div>
            ) : payment ? (
              <div>
                <div className="banner banner-success" style={{ marginBottom: 12 }}>You're renting this. Contact the landlord to arrange move-in.</div>
                <div className="field"><label>Landlord</label><div>{payment.landlord_name}</div></div>
                <div className="field"><label>Phone</label><div>{payment.landlord_phone}</div></div>
                <div className="field"><label>Exact address</label><div>{payment.address}</div></div>
                <p className="field-hint">Tenancy runs until {new Date(payment.end_date).toLocaleDateString()}</p>
                <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                  <Link to={`/chat/${payment.id}`} className="btn btn-secondary" style={{ flex: 1 }}>Chat</Link>
                  <Link to={`/renter/payments/${payment.id}/receipt`} className="btn btn-ghost" style={{ flex: 1 }}>Receipt</Link>
                </div>
              </div>
            ) : (
              <>
                {error && <div className="banner banner-error" style={{ marginBottom: 12 }}>{error}</div>}
                {user?.role === "renter" ? (
                  !availability || availability.status === "rejected" ? (
                    <>
                      <p className="field-hint" style={{ marginBottom: 14 }}>
                        Before you can pay, we confirm with the landlord that this property is still available.
                      </p>
                      {availability?.status === "rejected" && (
                        <div className="banner banner-error" style={{ marginBottom: 12 }}>
                          {availability.rejection_reason || "The landlord said this is no longer available."}
                        </div>
                      )}
                      <button className="btn btn-primary btn-block" onClick={handleRequestAvailability} disabled={busy}>
                        {busy ? "Requesting…" : "Request availability confirmation"}
                      </button>
                    </>
                  ) : availability.status === "pending" ? (
                    <div className="banner banner-info">We've notified the landlord. An admin will confirm shortly. Check back soon.</div>
                  ) : (
                    <>
                      <p className="field-hint" style={{ marginBottom: 12 }}>
                        Wakaless holds this payment. It's only released to the landlord after you've met them,
                        seen the house in person, and confirmed you're satisfied (from My rentals).
                      </p>
                      <button className="btn btn-primary btn-block" onClick={handlePay} disabled={busy}>
                        {busy ? "Processing…" : `Pay ${formatNaira(listing.rent_amount_ngn + listing.agreement_fee_ngn + listing.commission_ngn)} now`}
                      </button>
                    </>
                  )
                ) : (
                  <a href="/signup" className="btn btn-primary btn-block">Sign up as a renter to pay</a>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
