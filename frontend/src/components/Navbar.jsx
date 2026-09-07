import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";
import logo from "../assets/wakaless-icon-color.svg";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [resendState, setResendState] = useState("idle"); // idle | sending | sent

  async function resendVerification() {
    setResendState("sending");
    try {
      await api.resendVerification(user.email);
    } finally {
      setResendState("sent");
    }
  }

  useEffect(() => { setOpen(false); }, [location.pathname]);

  useEffect(() => {
    if (!open) return;
    function onKey(e) { if (e.key === "Escape") setOpen(false); }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <>
      <header style={{ background: "transparent", position: "sticky", top: 0, zIndex: 100 }}>
        <div className="container" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: 64 }}>
          <Link to="/" style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <img src={logo} alt="Wakaless" height={30} />
            <div>
              <div style={{ fontWeight: 800, fontSize: 18, color: "var(--teal)", lineHeight: 1 }}>Wakaless</div>
              <div style={{ fontSize: 11, color: "var(--muted)" }}>No agent. No wahala.</div>
            </div>
          </Link>

          <button
            aria-label="Open menu"
            onClick={() => setOpen(true)}
            style={{
              display: "flex", flexDirection: "column", justifyContent: "center", gap: 5,
              width: 40, height: 40, background: "var(--white)", border: "1px solid var(--border)",
              borderRadius: 10, cursor: "pointer",
            }}
          >
            <span style={{ display: "block", height: 2, width: 20, background: "var(--ink)", margin: "0 auto" }} />
            <span style={{ display: "block", height: 2, width: 20, background: "var(--ink)", margin: "0 auto" }} />
            <span style={{ display: "block", height: 2, width: 20, background: "var(--ink)", margin: "0 auto" }} />
          </button>
        </div>
      </header>

      {user && user.role !== "admin" && !user.email_verified && (
        <div className="banner banner-info" style={{ margin: "0 auto 16px", maxWidth: 960, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <span>Please confirm your email address.{resendState === "sent" ? " Check your inbox for the link." : ""}</span>
          {resendState !== "sent" && (
            <button className="btn btn-ghost" disabled={resendState === "sending"} onClick={resendVerification}>
              {resendState === "sending" ? "Sending…" : "Resend verification email"}
            </button>
          )}
        </div>
      )}

      {open && (
        <div
          onClick={() => setOpen(false)}
          style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)", zIndex: 200 }}
        />
      )}

      <aside
        style={{
          position: "fixed", top: 0, right: 0, height: "100vh", width: 280, maxWidth: "85vw",
          background: "var(--white)", boxShadow: "-4px 0 24px rgba(0,0,0,0.15)", zIndex: 201,
          transform: open ? "translateX(0)" : "translateX(100%)", transition: "transform 0.2s ease",
          display: "flex", flexDirection: "column", padding: 20,
        }}
      >
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
          <button
            aria-label="Close menu"
            onClick={() => setOpen(false)}
            className="btn btn-ghost"
            style={{ padding: "6px 12px", fontSize: 18, lineHeight: 1 }}
          >
            ✕
          </button>
        </div>

        <nav style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 15, fontWeight: 600 }}>
          <SidebarLink to="/">Browse</SidebarLink>
          {user?.role === "landlord" && <SidebarLink to="/landlord/dashboard">My listings</SidebarLink>}
          {user?.role === "renter" && <SidebarLink to="/renter/payments">My rentals</SidebarLink>}
          {(user?.role === "renter" || user?.role === "landlord") && <SidebarLink to="/chat">Messages</SidebarLink>}
          {user?.role === "admin" && <SidebarLink to="/admin/review-queue">Listings</SidebarLink>}
          {user?.role === "admin" && <SidebarLink to="/admin/verification-queue">Verifications</SidebarLink>}
          {user?.role === "admin" && <SidebarLink to="/admin/availability-queue">Availability</SidebarLink>}
          {user?.role === "admin" && <SidebarLink to="/admin/payouts">Payouts</SidebarLink>}
          {user?.role === "admin" && <SidebarLink to="/admin/inspections">Inspections</SidebarLink>}
          {user?.role === "admin" && <SidebarLink to="/admin/transactions">Transactions</SidebarLink>}
          {user?.role === "admin" && <SidebarLink to="/admin/chats">Chats</SidebarLink>}
          {user?.role === "admin" && <SidebarLink to="/admin/users">Users</SidebarLink>}

          <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "12px 0" }} />

          {user ? (
            <button
              className="btn btn-ghost btn-block"
              onClick={() => { setOpen(false); logout(); navigate("/"); }}
            >
              Log out
            </button>
          ) : (
            <>
              <SidebarLink to="/login">Log in</SidebarLink>
              <Link to="/signup" className="btn btn-primary btn-block" style={{ marginTop: 8 }}>Get started</Link>
            </>
          )}
        </nav>
      </aside>
    </>
  );
}

function SidebarLink({ to, children }) {
  return (
    <Link to={to} style={{ padding: "10px 8px", borderRadius: 8 }}>
      {children}
    </Link>
  );
}
