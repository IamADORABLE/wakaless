import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

const STATUS_LABEL = {
  pending_review: "Awaiting review",
  live: "Live",
  rejected: "Rejected",
  rented: "Rented",
  expired: "Expired: confirm availability",
};

function BankDetailsCard() {
  const [form, setForm] = useState({ bank_name: "", bank_account_number: "", bank_account_name: "" });
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.myBankDetails().then((d) => setForm({
      bank_name: d.bank_name || "", bank_account_number: d.bank_account_number || "", bank_account_name: d.bank_account_name || "",
    })).catch(() => {});
  }, []);

  function set(field, value) { setForm((f) => ({ ...f, [field]: value })); setSaved(false); }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.updateBankDetails(form);
      setSaved(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card" style={{ padding: 20, marginBottom: 24 }}>
      <h2 style={{ marginTop: 0, fontSize: 17 }}>Bank details</h2>
      <p className="text-muted" style={{ fontSize: 13, marginTop: -8, marginBottom: 16 }}>
        Your share of each rent payment is sent here manually by an admin after the platform's fee is deducted.
      </p>
      {error && <div className="banner banner-error" style={{ marginBottom: 12 }}>{error}</div>}
      {saved && <div className="banner banner-success" style={{ marginBottom: 12 }}>Saved.</div>}
      <form onSubmit={onSubmit} style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, alignItems: "end" }}>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>Bank name</label>
          <input required value={form.bank_name} onChange={(e) => set("bank_name", e.target.value)} />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>Account number</label>
          <input required value={form.bank_account_number} onChange={(e) => set("bank_account_number", e.target.value)} />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>Account name</label>
          <input required value={form.bank_account_name} onChange={(e) => set("bank_account_name", e.target.value)} />
        </div>
        <button className="btn btn-secondary" disabled={busy} type="submit" style={{ gridColumn: "1 / -1" }}>
          {busy ? "Saving…" : "Save"}
        </button>
      </form>
    </div>
  );
}

export default function LandlordDashboard() {
  const [listings, setListings] = useState([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function load() {
    try {
      setListings(await api.myListings());
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function markRented(id) {
    setBusyId(id);
    try {
      await api.updateListingStatus(id, "rented");
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusyId(null);
    }
  }

  async function confirmStillAvailable(id) {
    setBusyId(id);
    try {
      await api.updateListingStatus(id, "live");
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
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h1 style={{ color: "var(--teal)", margin: 0 }}>My listings</h1>
          <Link to="/landlord/listings/new" className="btn btn-primary">+ New listing</Link>
        </div>

        <BankDetailsCard />

        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

        {listings.length === 0 ? (
          <p className="text-muted">You haven't created any listings yet.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {listings.map((l) => (
              <div key={l.id} className="card" style={{ padding: 16, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                <div>
                  <strong>{l.title}</strong>
                  <div className="text-muted" style={{ fontSize: 13 }}>{l.area}</div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span className="badge badge-status">{STATUS_LABEL[l.status] || l.status}</span>
                  {l.status === "live" && (
                    <button className="btn btn-ghost" disabled={busyId === l.id} onClick={() => markRented(l.id)}>
                      Mark rented
                    </button>
                  )}
                  {l.status === "expired" && (
                    <button className="btn btn-secondary" disabled={busyId === l.id} onClick={() => confirmStillAvailable(l.id)}>
                      Still available
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
