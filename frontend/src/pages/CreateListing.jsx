import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";

export default function CreateListing() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [durationOptions, setDurationOptions] = useState([]);
  const [form, setForm] = useState({
    title: "", description: "", rent_amount_ngn: "", rent_duration_months: "", agreement_fee_ngn: "",
    area: "", address: "", lat: "", lng: "",
  });
  const [photoFiles, setPhotoFiles] = useState([]);
  const [videoFile, setVideoFile] = useState(null);
  const [docFile, setDocFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [feeRequired, setFeeRequired] = useState(false);

  const feeJustPaid = searchParams.get("fee_paid") === "1";

  useEffect(() => {
    api.rentDurationOptions().then(({ options }) => {
      setDurationOptions(options);
      if (options.length) set("rent_duration_months", String(options[0]));
    }).catch(() => {});
  }, []);

  function set(field, value) { setForm((f) => ({ ...f, [field]: value })); }

  function buildPayload(photoUrls, docUrl, videoUrl) {
    return {
      title: form.title,
      description: form.description || undefined,
      photos: photoUrls,
      rent_amount_ngn: Number(form.rent_amount_ngn),
      rent_duration_months: Number(form.rent_duration_months),
      agreement_fee_ngn: Number(form.agreement_fee_ngn || 0),
      area: form.area,
      address: form.address,
      lat: form.lat ? Number(form.lat) : undefined,
      lng: form.lng ? Number(form.lng) : undefined,
      ownership_doc_url: docUrl,
      video_url: videoUrl || undefined,
    };
  }

  async function uploadEverything() {
    const [photoResults, { url: docUrl }, videoResult] = await Promise.all([
      Promise.all(photoFiles.map((f) => api.uploadListingPhoto(f))),
      api.uploadOwnershipDoc(docFile),
      videoFile ? api.uploadListingVideo(videoFile) : Promise.resolve(null),
    ]);
    return {
      photoUrls: photoResults.map((r) => r.url),
      docUrl,
      videoUrl: videoResult?.url,
    };
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    if (photoFiles.length === 0) return setError("Add at least one photo.");
    if (photoFiles.length > 10) return setError("At most 10 photos are allowed.");
    if (!docFile) return setError("Upload a proof-of-ownership document (C of O, receipt, or utility bill).");
    setBusy(true);
    try {
      const { photoUrls, docUrl, videoUrl } = await uploadEverything();
      await api.createListing(buildPayload(photoUrls, docUrl, videoUrl));
      setDone(true);
      setTimeout(() => navigate("/landlord/dashboard"), 1200);
    } catch (e) {
      setError(e.message);
      setFeeRequired(e.status === 402);
    } finally {
      setBusy(false);
    }
  }

  async function payFeeAndRetry() {
    setError("");
    setBusy(true);
    try {
      const initiated = await api.initiateListingFee();
      if (initiated.authorization_url) {
        window.location.href = initiated.authorization_url;
        return;
      }
      // Mock provider: verifies instantly, no redirect needed.
      await api.verifyListingFee(initiated.reference);
      const { photoUrls, docUrl, videoUrl } = await uploadEverything();
      await api.createListing(buildPayload(photoUrls, docUrl, videoUrl));
      setFeeRequired(false);
      setDone(true);
      setTimeout(() => navigate("/landlord/dashboard"), 1200);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="page"><div className="container" style={{ maxWidth: 520 }}>
        <div className="banner banner-success">
          Listing submitted! It'll appear in search once an admin reviews your ownership document.
        </div>
      </div></div>
    );
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 520 }}>
        <h1 style={{ color: "var(--teal)" }}>List your property</h1>
        {feeJustPaid && !error && (
          <div className="banner banner-success" style={{ marginBottom: 16 }}>
            Fee paid. Fill in your listing details below and submit to finish.
          </div>
        )}
        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

        <form onSubmit={onSubmit} className="card" style={{ padding: 24 }}>
          <div className="field">
            <label>Title</label>
            <input required placeholder="e.g. 2-bedroom flat, Lekki Phase 1" value={form.title} onChange={(e) => set("title", e.target.value)} />
          </div>
          <div className="field">
            <label>Description (optional)</label>
            <textarea rows={3} value={form.description} onChange={(e) => set("description", e.target.value)} />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div className="field">
              <label>Total rent for this duration (₦)</label>
              <input required type="number" min={1} value={form.rent_amount_ngn} onChange={(e) => set("rent_amount_ngn", e.target.value)} />
            </div>
            <div className="field">
              <label>Rent duration</label>
              <select required value={form.rent_duration_months} onChange={(e) => set("rent_duration_months", e.target.value)}>
                {durationOptions.map((m) => (
                  <option key={m} value={m}>{m} months</option>
                ))}
              </select>
            </div>
          </div>
          <div className="field">
            <label>Agreement fee (₦)</label>
            <input type="number" min={0} value={form.agreement_fee_ngn} onChange={(e) => set("agreement_fee_ngn", e.target.value)} />
          </div>
          <div className="field">
            <label>Area (shown publicly before payment)</label>
            <input required placeholder="e.g. Lekki Phase 1" value={form.area} onChange={(e) => set("area", e.target.value)} />
          </div>
          <div className="field">
            <label>Exact address (revealed only after rent is paid)</label>
            <input required value={form.address} onChange={(e) => set("address", e.target.value)} />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div className="field">
              <label>Map pin: latitude (optional)</label>
              <input type="number" step="any" value={form.lat} onChange={(e) => set("lat", e.target.value)} />
            </div>
            <div className="field">
              <label>Map pin: longitude (optional)</label>
              <input type="number" step="any" value={form.lng} onChange={(e) => set("lng", e.target.value)} />
            </div>
          </div>
          <div className="field">
            <label>Photos (up to 10)</label>
            <input
              required type="file" accept="image/*" multiple
              onChange={(e) => setPhotoFiles(Array.from(e.target.files || []))}
            />
            {photoFiles.length > 0 && (
              <span className="field-hint">{photoFiles.length} photo{photoFiles.length === 1 ? "" : "s"} selected.</span>
            )}
          </div>
          <div className="field">
            <label>Walkthrough video (optional)</label>
            <input type="file" accept="video/*" onChange={(e) => setVideoFile(e.target.files?.[0] || null)} />
            {videoFile && <span className="field-hint">{videoFile.name}</span>}
          </div>
          <div className="field">
            <label>Proof of ownership (C of O, receipt, or utility bill)</label>
            <input required type="file" accept="image/*,.pdf" onChange={(e) => setDocFile(e.target.files?.[0] || null)} />
            <span className="field-hint">Reviewed by an admin before your listing goes live. Not shown publicly.</span>
          </div>

          {feeRequired ? (
            <button className="btn btn-primary btn-block" disabled={busy} type="button" onClick={payFeeAndRetry}>
              {busy ? "Processing…" : "Pay listing fee and continue"}
            </button>
          ) : (
            <button className="btn btn-primary btn-block" disabled={busy} type="submit">
              {busy ? "Submitting…" : "Submit for review"}
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
