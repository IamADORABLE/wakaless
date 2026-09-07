import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import PasswordInput from "../components/PasswordInput";

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState("renter");
  const [form, setForm] = useState({ full_name: "", phone: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await signup({ ...form, role });
      navigate(role === "landlord" ? "/landlord/verify" : "/");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 440 }}>
        <h1 style={{ color: "var(--teal)" }}>Create your account</h1>

        <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
          {["renter", "landlord"].map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              className={role === r ? "btn btn-secondary" : "btn btn-ghost"}
              style={{ flex: 1 }}
            >
              I'm a {r}
            </button>
          ))}
        </div>

        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

        <form onSubmit={onSubmit} className="card" style={{ padding: 24 }}>
          <div className="field">
            <label>Full name</label>
            <input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          </div>
          <div className="field">
            <label>Phone number</label>
            <input required placeholder="+234 or 0..." value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </div>
          <div className="field">
            <label>Email</label>
            <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div className="field">
            <label>Password</label>
            <PasswordInput required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </div>
          <button className="btn btn-primary btn-block" disabled={busy} type="submit">
            {busy ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="text-muted" style={{ marginTop: 16 }}>
          Already have an account? <Link to="/login" style={{ color: "var(--teal)", fontWeight: 600 }}>Log in</Link>
        </p>
      </div>
    </div>
  );
}
