import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";
import OtpInput from "../components/OtpInput";
import useCountdown from "../hooks/useCountdown";

function storedEmail() {
  // Read straight from localStorage rather than the `user` from context:
  // AuthContext hydrates it from localStorage in its own mount effect,
  // which may not have run yet when this component's state initializes.
  try {
    const stored = localStorage.getItem("wakaless_user");
    return stored ? JSON.parse(stored).email || "" : "";
  } catch {
    return "";
  }
}

export default function VerifyEmail() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState("email"); // email | code
  const [email, setEmail] = useState(storedEmail);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const { seconds: resendIn, restart: restartCountdown } = useCountdown(60);

  async function sendCode(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.resendVerification(email);
      restartCountdown();
      setStep("code");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    if (resendIn > 0) return;
    setError("");
    try {
      await api.resendVerification(email);
      restartCountdown();
    } catch (e) {
      setError(e.message);
    }
  }

  async function verify(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.verifyEmail(email, code);
      setDone(true);
      if (user && user.email === email) {
        const updated = { ...user, email_verified: true };
        localStorage.setItem("wakaless_user", JSON.stringify(updated));
        setUser(updated);
      }
      setTimeout(() => navigate("/"), 1200);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="page"><div className="container" style={{ maxWidth: 420 }}>
        <div className="banner banner-success">Your email is confirmed.</div>
      </div></div>
    );
  }

  if (step === "email") {
    return (
      <div className="page">
        <div className="container" style={{ maxWidth: 420 }}>
          <h1 style={{ color: "var(--teal)", marginBottom: 4 }}>Confirm your email</h1>
          <p className="text-muted" style={{ marginBottom: 24 }}>Enter your email to get a verification code.</p>
          {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

          <form onSubmit={sendCode} className="card" style={{ padding: 24 }}>
            <div className="field">
              <label>EMAIL</label>
              <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <button className="btn btn-secondary btn-block" disabled={busy} type="submit">
              {busy ? "Sending…" : "Continue →"}
            </button>
          </form>
          <p className="text-muted" style={{ marginTop: 16 }}>
            <Link to="/" style={{ color: "var(--teal)", fontWeight: 600 }}>Back to Wakaless</Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 420 }}>
        <h1 style={{ color: "var(--teal)", marginBottom: 4 }}>Verify your email</h1>
        <p className="text-muted" style={{ marginBottom: 24 }}>
          We sent a 6-digit code to {email}. Enter it below to continue.
        </p>
        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

        <form onSubmit={verify} className="card" style={{ padding: 24 }}>
          <div style={{ marginBottom: 20 }}>
            <OtpInput value={code} onChange={setCode} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
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
          <button className="btn btn-secondary btn-block" disabled={busy || code.length !== 6} type="submit">
            {busy ? "Verifying…" : "Verify →"}
          </button>
        </form>
        <p className="text-muted" style={{ marginTop: 16, textAlign: "center" }}>
          <button type="button" onClick={() => setStep("email")} className="btn btn-ghost" style={{ padding: 0, border: "none" }}>
            ← Change email
          </button>
        </p>
      </div>
    </div>
  );
}
