import { useEffect, useState } from "react";
import { api } from "../api/client";

const TABS = [
  { label: "All", role: "" },
  { label: "Landlords", role: "landlord" },
  { label: "Renters", role: "renter" },
  { label: "Admins", role: "admin" },
];

const VERIFICATION_TABS = [
  { label: "All", status: "" },
  { label: "Unverified", status: "unverified" },
  { label: "Pending review", status: "pending" },
  { label: "Verified", status: "verified" },
  { label: "Failed", status: "failed" },
];

function VerificationBadge({ status }) {
  if (!status || status === "unverified") return <span className="text-muted" style={{ fontSize: 13 }}>N/A</span>;
  const label = { verified: "Verified", pending: "Pending review", failed: "Failed" }[status] || status;
  const className = status === "verified" ? "badge badge-verified" : "badge badge-status";
  return <span className={className}>{label}</span>;
}

export default function AdminUsers() {
  const [role, setRole] = useState("");
  const [verificationStatus, setVerificationStatus] = useState("");
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.listUsers({ role, verification_status: role === "landlord" ? verificationStatus : "" })
      .then(setUsers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [role, verificationStatus]);

  function selectRole(r) {
    setRole(r);
    setVerificationStatus("");
  }

  return (
    <div className="page">
      <div className="container">
        <h1 style={{ color: "var(--teal)" }}>Users</h1>
        <p className="text-muted">Everyone signed up on Wakaless: renters, landlords, and admins.</p>

        <div style={{ display: "flex", gap: 8, marginBottom: role === "landlord" ? 12 : 20 }}>
          {TABS.map((t) => (
            <button
              key={t.role}
              type="button"
              onClick={() => selectRole(t.role)}
              className={role === t.role ? "btn btn-secondary" : "btn btn-ghost"}
              style={{ padding: "8px 16px" }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {role === "landlord" && (
          <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
            {VERIFICATION_TABS.map((t) => (
              <button
                key={t.status}
                type="button"
                onClick={() => setVerificationStatus(t.status)}
                className={verificationStatus === t.status ? "badge badge-verified" : "badge badge-status"}
                style={{ border: "none", cursor: "pointer", opacity: verificationStatus === t.status ? 1 : 0.6 }}
              >
                {t.label}
              </button>
            ))}
          </div>
        )}

        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

        {!loading && users.length === 0 ? (
          <p className="text-muted">No users here yet.</p>
        ) : (
          <div className="card" style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
                  <th style={{ padding: "12px 16px" }}>Name</th>
                  <th style={{ padding: "12px 16px" }}>Phone</th>
                  <th style={{ padding: "12px 16px" }}>Email</th>
                  <th style={{ padding: "12px 16px" }}>Role</th>
                  <th style={{ padding: "12px 16px" }}>Verification</th>
                  <th style={{ padding: "12px 16px" }}>Listings</th>
                  <th style={{ padding: "12px 16px" }}>Joined</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "12px 16px", fontWeight: 600 }}>{u.full_name}</td>
                    <td style={{ padding: "12px 16px" }}>{u.phone}</td>
                    <td style={{ padding: "12px 16px" }}>{u.email}</td>
                    <td style={{ padding: "12px 16px", textTransform: "capitalize" }}>{u.role}</td>
                    <td style={{ padding: "12px 16px" }}>
                      {u.role === "landlord" ? <VerificationBadge status={u.verification_status} /> : <span className="text-muted" style={{ fontSize: 13 }}>N/A</span>}
                    </td>
                    <td style={{ padding: "12px 16px" }}>{u.role === "landlord" ? u.listings_count : "N/A"}</td>
                    <td style={{ padding: "12px 16px" }} className="text-muted">
                      {new Date(u.created_at).toLocaleDateString("en-NG", { year: "numeric", month: "short", day: "numeric" })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
