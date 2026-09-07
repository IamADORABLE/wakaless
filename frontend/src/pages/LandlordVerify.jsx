import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function LandlordVerify() {
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [proofFile, setProofFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.myVerification().then((v) => {
      setStatus(v.status);
      if (v.status === "failed") setError(v.failure_reason || "Your previous submission did not pass review.");
    }).catch(() => {});
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    if (!proofFile) { setError("Please add a photo of your proof of ownership."); return; }
    setBusy(true);
    try {
      const { url } = await api.uploadOwnershipProof(proofFile);
      const result = await api.submitVerification({ ownership_proof_url: url });
      setStatus(result.status);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 460 }}>
        <h1 style={{ color: "var(--teal)" }}>Verify your identity</h1>
        <p className="text-muted">
          One-time check per account, not per listing. Upload a photo of a document that shows you own or manage the
          property (e.g. a utility bill, C of O, or tenancy agreement in your name) and an admin will review it.
        </p>

        {status === "verified" ? (
          <div className="banner banner-success">You're verified! You can now create listings.</div>
        ) : status === "pending" ? (
          <div className="banner banner-success">
            Your proof of ownership is submitted. An admin will review it shortly. Check back later.
          </div>
        ) : (
          <form onSubmit={onSubmit} className="card" style={{ padding: 24 }}>
            {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}
            <div className="field">
              <label>Proof of ownership</label>
              <input required type="file" accept="image/*" onChange={(e) => setProofFile(e.target.files?.[0] || null)} />
              <span className="field-hint">A clear photo of a utility bill, C of O, tenancy agreement, or similar document in your name.</span>
            </div>
            <button className="btn btn-primary btn-block" disabled={busy} type="submit">
              {busy ? "Submitting…" : "Submit for review"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
