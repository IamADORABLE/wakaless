import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import PasswordInput from "../components/PasswordInput";
import { api } from "../api/client";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError("Passwords don't match");
      return;
    }
    setBusy(true);
    try {
      await api.resetPassword(token, password);
      setDone(true);
      setTimeout(() => navigate("/login"), 2000);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <div className="page">
        <div className="container" style={{ maxWidth: 420 }}>
          <div className="banner banner-error">
            This reset link is missing its token. Request a new one from{" "}
            <Link to="/forgot-password" style={{ color: "var(--teal)", fontWeight: 600 }}>forgot password</Link>.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 420 }}>
        <h1 style={{ color: "var(--teal)" }}>Reset password</h1>
        {done ? (
          <div className="banner banner-success">Password reset. Taking you to log in…</div>
        ) : (
          <>
            {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}
            <form onSubmit={onSubmit} className="card" style={{ padding: 24 }}>
              <div className="field">
                <label>New password</label>
                <PasswordInput required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} />
              </div>
              <div className="field">
                <label>Confirm new password</label>
                <PasswordInput required minLength={8} value={confirm} onChange={(e) => setConfirm(e.target.value)} />
              </div>
              <button className="btn btn-primary btn-block" disabled={busy} type="submit">
                {busy ? "Resetting…" : "Reset password"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
