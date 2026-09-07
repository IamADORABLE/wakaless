import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const { setUser } = useAuth();
  const [status, setStatus] = useState("verifying"); // verifying | success | error

  useEffect(() => {
    if (!token) {
      setStatus("error");
      return;
    }
    api.verifyEmail(token)
      .then(() => {
        setStatus("success");
        // Read straight from localStorage rather than the `user` from context:
        // AuthContext hydrates it from localStorage in its own mount effect,
        // which may not have run yet when this effect fires.
        const stored = localStorage.getItem("wakaless_user");
        if (stored) {
          const updated = { ...JSON.parse(stored), email_verified: true };
          localStorage.setItem("wakaless_user", JSON.stringify(updated));
          setUser(updated);
        }
      })
      .catch(() => setStatus("error"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 420 }}>
        <h1 style={{ color: "var(--teal)" }}>Email verification</h1>
        {status === "verifying" && <div className="banner banner-info">Verifying your email…</div>}
        {status === "success" && <div className="banner banner-success">Your email is confirmed.</div>}
        {status === "error" && (
          <div className="banner banner-error">This verification link is invalid or has expired.</div>
        )}
        <p className="text-muted" style={{ marginTop: 16 }}>
          <Link to="/" style={{ color: "var(--teal)", fontWeight: 600 }}>Back to Wakaless</Link>
        </p>
      </div>
    </div>
  );
}
