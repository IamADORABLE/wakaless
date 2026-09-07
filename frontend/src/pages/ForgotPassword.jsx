import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.forgotPassword(email);
      setSent(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 420 }}>
        <h1 style={{ color: "var(--teal)" }}>Forgot password</h1>
        {sent ? (
          <div className="banner banner-success">
            If that email has an account, we've sent a link to reset the password. Check your inbox.
          </div>
        ) : (
          <>
            {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}
            <form onSubmit={onSubmit} className="card" style={{ padding: 24 }}>
              <div className="field">
                <label>Email</label>
                <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <button className="btn btn-primary btn-block" disabled={busy} type="submit">
                {busy ? "Sending…" : "Send reset link"}
              </button>
            </form>
          </>
        )}
        <p className="text-muted" style={{ marginTop: 16 }}>
          <Link to="/login" style={{ color: "var(--teal)", fontWeight: 600 }}>Back to log in</Link>
        </p>
      </div>
    </div>
  );
}
