import { useEffect, useState } from "react";
import { api } from "../api/client";

function formatNaira(n) {
  return `₦${Number(n).toLocaleString("en-NG")}`;
}

export default function AdminTransactions() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.adminTransactions()
      .then(setRows)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <div className="container">
        <h1 style={{ color: "var(--teal)" }}>Transactions</h1>
        <p className="text-muted">Every rent payment on the platform.</p>

        {error && <div className="banner banner-error" style={{ marginBottom: 16 }}>{error}</div>}

        {!loading && rows.length === 0 ? (
          <p className="text-muted">No transactions yet.</p>
        ) : (
          <div className="card" style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
                  <th style={{ padding: "12px 16px" }}>Property</th>
                  <th style={{ padding: "12px 16px" }}>Renter</th>
                  <th style={{ padding: "12px 16px" }}>Landlord</th>
                  <th style={{ padding: "12px 16px" }}>Rent</th>
                  <th style={{ padding: "12px 16px" }}>Agreement fee</th>
                  <th style={{ padding: "12px 16px" }}>Commission</th>
                  <th style={{ padding: "12px 16px" }}>Total paid</th>
                  <th style={{ padding: "12px 16px" }}>Landlord gets</th>
                  <th style={{ padding: "12px 16px" }}>Payout</th>
                  <th style={{ padding: "12px 16px" }}>Tenancy</th>
                  <th style={{ padding: "12px 16px" }}>Paid on</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((t) => (
                  <tr key={t.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "12px 16px", fontWeight: 600 }}>{t.listing_title}</td>
                    <td style={{ padding: "12px 16px" }}>{t.renter_name}<div className="text-muted" style={{ fontSize: 12 }}>{t.renter_phone}</div></td>
                    <td style={{ padding: "12px 16px" }}>{t.landlord_name}<div className="text-muted" style={{ fontSize: 12 }}>{t.landlord_phone}</div></td>
                    <td className="money" style={{ padding: "12px 16px" }}>{formatNaira(t.rent_amount_ngn)}</td>
                    <td className="money" style={{ padding: "12px 16px" }}>{formatNaira(t.agreement_fee_ngn)}</td>
                    <td className="money" style={{ padding: "12px 16px" }}>{formatNaira(t.commission_ngn)}</td>
                    <td className="money" style={{ padding: "12px 16px", fontWeight: 600 }}>{formatNaira(t.total_paid_ngn)}</td>
                    <td className="money" style={{ padding: "12px 16px" }}>{formatNaira(t.landlord_payout_ngn)}</td>
                    <td style={{ padding: "12px 16px" }}>
                      <span className={`badge ${t.payout_status === "paid_out" ? "badge-verified" : "badge-status"}`}>
                        {t.payout_status === "paid_out" ? "Paid out" : "Awaiting"}
                      </span>
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <span className={`badge ${t.status === "active" ? "badge-verified" : "badge-status"}`}>
                        {t.status === "active" ? "Active" : "Ended"}
                      </span>
                    </td>
                    <td style={{ padding: "12px 16px" }} className="text-muted">
                      {new Date(t.paid_at).toLocaleDateString("en-NG", { year: "numeric", month: "short", day: "numeric" })}
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
