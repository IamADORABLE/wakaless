import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { api } from "../api/client";

export default function PaymentCallback() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const started = useRef(false);

  useEffect(() => {
    // Guard against firing twice (React StrictMode's dev double-invoke,
    // or a re-render before navigate() away completes). The backend is
    // also idempotent on the payment reference, but there's no reason to
    // make a redundant second request.
    if (started.current) return;
    started.current = true;

    const kind = params.get("kind");
    const reference = params.get("reference") || params.get("trxref");
    const listingId = params.get("listing_id");
    const rentPaymentId = params.get("rent_payment_id");

    if (!reference) {
      setError("Missing payment reference. The payment may not have completed.");
      return;
    }

    (async () => {
      try {
        if (kind === "renew" && rentPaymentId) {
          await api.verifyRenewal(rentPaymentId, reference);
          navigate("/renter/payments", { replace: true });
        } else if (kind === "payment" && listingId) {
          await api.verifyRentPayment(reference);
          navigate(`/listings/${listingId}`, { replace: true });
        } else {
          setError("Couldn't tell what this payment was for.");
        }
      } catch (e) {
        setError(e.message);
      }
    })();
  }, [params, navigate]);

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 460 }}>
        {error ? (
          <>
            <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>
            <Link to="/" className="btn btn-secondary">Back to browse</Link>
          </>
        ) : (
          <p className="text-muted">Confirming your payment…</p>
        )}
      </div>
    </div>
  );
}
