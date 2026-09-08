import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.forgotPassword(email);
      navigate(`/reset-password?email=${encodeURIComponent(email)}`);
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
        <p className="text-muted">We'll email you a 6-digit code to reset your password.</p>
        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}
        <form onSubmit={onSubmit} className="card" style={{ padding: 24 }}>
          <div className="field">
            <label>Email</label>
            <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <button className="btn btn-primary btn-block" disabled={busy} type="submit">
            {busy ? "Sending…" : "Send reset code"}
          </button>
        </form>
        <p className="text-muted" style={{ marginTop: 16 }}>
          <Link to="/login" style={{ color: "var(--teal)", fontWeight: 600 }}>Back to log in</Link>
        </p>
      </div>
    </div>
  );
}
