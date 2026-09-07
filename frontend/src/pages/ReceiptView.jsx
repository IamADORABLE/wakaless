import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import logo from "../assets/wakaless-icon-color.svg";

function formatNaira(n) {
  return `₦${Number(n).toLocaleString("en-NG")}`;
}

function formatDate(d) {
  return new Date(d).toLocaleDateString("en-NG", { year: "numeric", month: "long", day: "numeric" });
}

export default function ReceiptView() {
  const { id } = useParams();
  const [receipt, setReceipt] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => { api.getReceipt(id).then(setReceipt).catch((e) => setError(e.message)); }, [id]);

  if (error) return <div className="page"><div className="container"><div className="banner banner-error">{error}</div></div></div>;
  if (!receipt) return <div className="page"><div className="container"><p className="text-muted">Loading…</p></div></div>;

  const items = [{ label: `Rent (${receipt.rent_duration_months} months)`, amount: receipt.rent_amount_ngn }];
  if (receipt.agreement_fee_ngn > 0) items.push({ label: "Agreement fee", amount: receipt.agreement_fee_ngn });
  if (receipt.commission_ngn > 0) items.push({ label: "Commission", amount: receipt.commission_ngn });

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 640 }}>
        <div className="no-print" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h1 style={{ color: "var(--teal)", margin: 0 }}>Receipt</h1>
          <button className="btn btn-secondary" onClick={() => window.print()}>Print / Save as PDF</button>
        </div>

        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          {/* Letterhead */}
          <div style={{ background: "var(--teal)", color: "var(--white)", padding: "28px 32px", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <img src={logo} alt="Wakaless" height={30} style={{ filter: "brightness(0) invert(1)" }} />
              <div>
                <div style={{ fontWeight: 800, fontSize: 18, lineHeight: 1 }}>Wakaless</div>
                <div style={{ fontSize: 11, opacity: 0.8 }}>No agent. No wahala.</div>
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontWeight: 700, fontSize: 20, letterSpacing: 1 }}>RECEIPT</div>
              <div style={{ fontSize: 12, opacity: 0.85, marginTop: 2 }}>#{receipt.id.slice(0, 8).toUpperCase()}</div>
            </div>
          </div>

          <div style={{ padding: 32 }}>
            {/* Status + date */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
              <span className="badge badge-verified" style={{ fontSize: 13 }}>✓ Paid</span>
              <span className="text-muted" style={{ fontSize: 13 }}>{formatDate(receipt.paid_at)}</span>
            </div>

            {/* Parties */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 28 }}>
              <div>
                <div className="text-muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 6 }}>Renter</div>
                <div style={{ fontWeight: 700 }}>{receipt.renter_name}</div>
              </div>
              <div>
                <div className="text-muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 6 }}>Landlord</div>
                <div style={{ fontWeight: 700 }}>{receipt.landlord_name}</div>
              </div>
            </div>

            <div style={{ marginBottom: 28 }}>
              <div className="text-muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 6 }}>Property</div>
              <div style={{ fontWeight: 700 }}>{receipt.listing_title}</div>
              <div className="text-muted" style={{ fontSize: 14 }}>{receipt.address}</div>
            </div>

            {/* Itemized cost table */}
            <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 8 }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--ink)" }}>
                  <th style={{ textAlign: "left", padding: "0 0 8px", fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>Description</th>
                  <th style={{ textAlign: "right", padding: "0 0 8px", fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.label} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "10px 0" }}>{item.label}</td>
                    <td className="money" style={{ padding: "10px 0", textAlign: "right" }}>{formatNaira(item.amount)}</td>
                  </tr>
                ))}
                <tr>
                  <td style={{ padding: "12px 0 0", fontWeight: 700, fontSize: 16 }}>Total paid</td>
                  <td className="money" style={{ padding: "12px 0 0", textAlign: "right", fontWeight: 700, fontSize: 16, color: "var(--teal)" }}>
                    {formatNaira(receipt.total_paid_ngn)}
                  </td>
                </tr>
              </tbody>
            </table>

            <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "24px 0" }} />

            {/* Tenancy + payment details */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, fontSize: 14 }}>
              <Row label="Tenancy start" value={formatDate(receipt.start_date)} />
              <Row label="Tenancy end" value={formatDate(receipt.end_date)} />
              {receipt.payment_reference && <Row label="Payment reference" value={receipt.payment_reference} mono />}
            </div>
          </div>

          <div style={{ background: "var(--cream)", padding: "16px 32px", textAlign: "center" }}>
            <span className="text-muted" style={{ fontSize: 12 }}>This is a computer-generated receipt from Wakaless.</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, mono }) {
  return (
    <div>
      <div className="text-muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 2 }}>{label}</div>
      <div style={{ fontWeight: 600, fontFamily: mono ? "monospace" : "inherit" }}>{value}</div>
    </div>
  );
}
