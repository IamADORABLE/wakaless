import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";
import logo from "../assets/wakaless-icon-color.svg";

const NAV_ITEMS = [
  { to: "/", label: "Browse" },
  { to: "/landlord/dashboard", label: "My listings", role: "landlord" },
  { to: "/renter/payments", label: "My rentals", role: "renter" },
  { to: "/chat", label: "Messages", roles: ["renter", "landlord"] },
  { to: "/admin/review-queue", label: "Listings", role: "admin" },
  { to: "/admin/verification-queue", label: "Verifications", role: "admin" },
  { to: "/admin/availability-queue", label: "Availability", role: "admin" },
  { to: "/admin/payouts", label: "Payouts", role: "admin" },
  { to: "/admin/inspections", label: "Inspections", role: "admin" },
  { to: "/admin/transactions", label: "Transactions", role: "admin" },
  { to: "/admin/chats", label: "Chats", role: "admin" },
  { to: "/admin/users", label: "Users", role: "admin" },
];

function visibleFor(item, user) {
  if (item.role) return user?.role === item.role;
  if (item.roles) return item.roles.includes(user?.role);
  return true;
}

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

  function handleLogout() {
    setOpen(false);
    logout();
    navigate("/");
  }

  const items = NAV_ITEMS.filter((item) => visibleFor(item, user));

  return (
    <>
      <header style={{ background: "transparent", position: "sticky", top: 0, zIndex: 100 }}>
        <div className="container" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: 64, gap: 20 }}>
          <Link to="/" style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
            <img src={logo} alt="Wakaless" height={30} />
            <div>
              <div style={{ fontWeight: 800, fontSize: 18, color: "var(--teal)", lineHeight: 1 }}>Wakaless</div>
              <div style={{ fontSize: 11, color: "var(--muted)" }}>No agent. No wahala.</div>
            </div>
          </Link>

          <nav className="nav-links" style={{ alignItems: "center", gap: 20, fontSize: 14, fontWeight: 600, flex: 1, justifyContent: "flex-end" }}>
            {items.map((item) => (
              <Link key={item.to} to={item.to} style={{ color: "var(--ink)", whiteSpace: "nowrap" }}>{item.label}</Link>
            ))}
            {user ? (
              <button className="btn btn-ghost" onClick={handleLogout}>Log out</button>
            ) : (
              <>
                <Link to="/login" style={{ color: "var(--ink)", whiteSpace: "nowrap" }}>Log in</Link>
                <Link to="/signup" className="btn btn-primary">Get started</Link>
              </>
            )}
          </nav>

          <button
            className="nav-hamburger-btn"
            aria-label="Open menu"
            onClick={() => setOpen(true)}
            style={{
              flexDirection: "column", justifyContent: "center", gap: 5,
              width: 40, height: 40, background: "var(--white)", border: "1px solid var(--border)",
              borderRadius: 10, cursor: "pointer", flexShrink: 0,
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
          <span>Please confirm your email address.{resendState === "sent" ? " Check your inbox for the code." : ""}</span>
          <span style={{ display: "flex", gap: 8 }}>
            <Link to="/verify-email" className="btn btn-secondary">Enter code</Link>
            {resendState !== "sent" && (
              <button className="btn btn-ghost" disabled={resendState === "sending"} onClick={resendVerification}>
                {resendState === "sending" ? "Sending…" : "Resend code"}
              </button>
            )}
          </span>
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
          {items.map((item) => (
            <SidebarLink key={item.to} to={item.to}>{item.label}</SidebarLink>
          ))}

          <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "12px 0" }} />

          {user ? (
            <button className="btn btn-ghost btn-block" onClick={handleLogout}>Log out</button>
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
