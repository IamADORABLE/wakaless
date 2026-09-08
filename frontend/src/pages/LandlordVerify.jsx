import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function LandlordVerify() {
  const [status, setStatus] = useState(null);
  const [photoFile, setPhotoFile] = useState(null);
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
    if (!photoFile) { setError("Please add a photo of yourself."); return; }
    setBusy(true);
    try {
      const { url } = await api.uploadLandlordPhoto(photoFile);
      const result = await api.submitVerification({ photo_url: url });
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
          One-time check per account, not per listing. Upload a photo of yourself and an admin will review it.
          Proof of ownership is collected separately when you list a property, since every listing already requires it.
        </p>

        {status === "verified" ? (
          <div className="banner banner-success">You're verified! You can now create listings.</div>
        ) : status === "pending" ? (
          <div className="banner banner-success">
            Your photo is submitted. An admin will review it shortly. Check back later.
          </div>
        ) : (
          <form onSubmit={onSubmit} className="card" style={{ padding: 24 }}>
            {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}
            <div className="field">
              <label>Your photo</label>
              <input required type="file" accept="image/*" onChange={(e) => setPhotoFile(e.target.files?.[0] || null)} />
              <span className="field-hint">A clear, recent photo of your face.</span>
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
