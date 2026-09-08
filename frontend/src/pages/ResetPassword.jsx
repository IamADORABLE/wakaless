import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import PasswordInput from "../components/PasswordInput";
import OtpInput from "../components/OtpInput";
import { api } from "../api/client";
import useCountdown from "../hooks/useCountdown";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [email, setEmail] = useState(searchParams.get("email") || "");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const { seconds: resendIn, restart: restartCountdown } = useCountdown(60);

  async function resend() {
    if (resendIn > 0 || !email) return;
    setError("");
    try {
      await api.forgotPassword(email);
      restartCountdown();
    } catch (e) {
      setError(e.message);
    }
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError("Passwords don't match");
      return;
    }
    setBusy(true);
    try {
      await api.resetPassword(email, code, password);
      setDone(true);
      setTimeout(() => navigate("/login"), 2000);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="page"><div className="container" style={{ maxWidth: 420 }}>
        <div className="banner banner-success">Password reset. Taking you to log in…</div>
      </div></div>
    );
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 420 }}>
        <h1 style={{ color: "var(--teal)", marginBottom: 4 }}>Reset password</h1>
        <p className="text-muted" style={{ marginBottom: 24 }}>
          {email ? `We sent a 6-digit code to ${email}. Enter it below with your new password.` : "Enter your email, the code we sent you, and your new password."}
        </p>
        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

        <form onSubmit={onSubmit} className="card" style={{ padding: 24 }}>
          <div className="field">
            <label>EMAIL</label>
            <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>

          <div style={{ marginBottom: 8 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "var(--muted)", marginBottom: 6 }}>RESET CODE</label>
            <OtpInput value={code} onChange={setCode} autoFocus={false} />
          </div>
          <div style={{ marginBottom: 20 }}>
            <span className="text-muted" style={{ fontSize: 13 }}>
              {resendIn > 0 ? (
                `Resend in ${resendIn}s`
              ) : (
                <button type="button" onClick={resend} className="btn btn-ghost" style={{ padding: 0, border: "none", fontSize: 13 }}>
                  Resend code
                </button>
              )}
            </span>
          </div>

          <div className="field">
            <label>New password</label>
            <PasswordInput required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <div className="field">
            <label>Confirm new password</label>
            <PasswordInput required minLength={8} value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          </div>
          <button className="btn btn-primary btn-block" disabled={busy || code.length !== 6} type="submit">
            {busy ? "Resetting…" : "Reset password →"}
          </button>
        </form>
      </div>
    </div>
  );
}
