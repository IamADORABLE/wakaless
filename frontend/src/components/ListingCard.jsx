import { Link } from "react-router-dom";
import VerifiedBadge from "./VerifiedBadge";
import { api } from "../api/client";

function formatNaira(n) {
  return `₦${Number(n).toLocaleString("en-NG")}`;
}

export default function ListingCard({ listing }) {
  const cover = listing.photos?.[0];
  return (
    <Link to={`/listings/${listing.id}`} className="card" style={{ overflow: "hidden", display: "block" }}>
      <div style={{ aspectRatio: "4/3", background: "#eee2c9", position: "relative" }}>
        {cover ? (
          <img src={api.fileUrl(cover)} alt={listing.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--muted)" }}>
            No photo yet
          </div>
        )}
      </div>
      <div style={{ padding: 14 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 8, marginBottom: 6 }}>
          <strong style={{ fontSize: 15 }}>{listing.title}</strong>
        </div>
        <div className="text-muted" style={{ fontSize: 13, marginBottom: 8 }}>{listing.area}</div>
        <div className="money" style={{ fontWeight: 700, color: "var(--teal)" }}>
          {formatNaira(listing.rent_amount_ngn)}<span style={{ fontWeight: 400, color: "var(--muted)" }}> / {listing.rent_duration_months} months</span>
        </div>
        <div className="text-muted" style={{ fontSize: 12, marginTop: 2 }}>
          + {formatNaira(listing.agreement_fee_ngn)} agreement fee
        </div>
        <div style={{ marginTop: 10 }}>
          <VerifiedBadge verified={listing.verified_landlord} />
        </div>
      </div>
    </Link>
  );
}
