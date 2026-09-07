import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import PasswordInput from "../components/PasswordInput";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ identifier: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = await login(form);
      navigate(user.role === "landlord" ? "/landlord/dashboard" : user.role === "admin" ? "/admin/review-queue" : "/");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 420 }}>
        <h1 style={{ color: "var(--teal)" }}>Log in</h1>
        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}
        <form onSubmit={onSubmit} className="card" style={{ padding: 24 }}>
          <div className="field">
            <label>Phone number or email</label>
            <input required value={form.identifier} onChange={(e) => setForm({ ...form, identifier: e.target.value })} />
          </div>
          <div className="field">
            <label>Password</label>
            <PasswordInput required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </div>
          <button className="btn btn-primary btn-block" disabled={busy} type="submit">
            {busy ? "Logging in…" : "Log in"}
          </button>
        </form>
        <p style={{ marginTop: 12 }}>
          <Link to="/forgot-password" style={{ color: "var(--teal)", fontWeight: 600 }}>Forgot password?</Link>
        </p>
        <p className="text-muted" style={{ marginTop: 8 }}>
          New here? <Link to="/signup" style={{ color: "var(--teal)", fontWeight: 600 }}>Create an account</Link>
        </p>
      </div>
    </div>
  );
}
