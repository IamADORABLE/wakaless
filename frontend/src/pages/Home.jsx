import { useEffect, useState } from "react";
import { api } from "../api/client";
import ListingCard from "../components/ListingCard";

export default function Home() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [area, setArea] = useState("");
  const [maxRent, setMaxRent] = useState("");

  async function load(params = {}) {
    setLoading(true);
    setError("");
    try {
      const data = await api.browseListings(params);
      setListings(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <div className="page">
      <div className="container">
        <section style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 30, margin: "0 0 6px", color: "var(--teal)" }}>Find your next place. No agent.</h1>
          <p className="text-muted" style={{ marginTop: 0, maxWidth: 560 }}>
            Browse listings straight from verified landlords. See the real price breakdown up front,
            pay your rent through the platform once availability is confirmed, and we'll reveal the
            exact address and the landlord's number so you can move in.
          </p>
        </section>

        <form
          onSubmit={(e) => { e.preventDefault(); load({ area, max_rent: maxRent || undefined }); }}
          style={{ display: "flex", gap: 10, marginBottom: 24, flexWrap: "wrap" }}
        >
          <input
            placeholder="Area, e.g. Lekki Phase 1"
            value={area}
            onChange={(e) => setArea(e.target.value)}
            style={{ flex: "1 1 220px", border: "1.5px solid var(--border)", borderRadius: 10, padding: "11px 13px" }}
          />
          <input
            placeholder="Max rent (₦)"
            type="number"
            value={maxRent}
            onChange={(e) => setMaxRent(e.target.value)}
            style={{ flex: "1 1 200px", border: "1.5px solid var(--border)", borderRadius: 10, padding: "11px 13px" }}
          />
          <button className="btn btn-secondary" type="submit">Search</button>
        </form>

        {error && <div className="banner banner-error" style={{ marginBottom: 20 }}>{error}</div>}
        {loading ? (
          <p className="text-muted">Loading listings…</p>
        ) : listings.length === 0 ? (
          <div className="banner banner-info">
            No live listings yet. Landlords: <a href="/signup" style={{ textDecoration: "underline" }}>list your property</a> to be first.
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 18 }}>
            {listings.map((l) => <ListingCard key={l.id} listing={l} />)}
          </div>
        )}
      </div>
    </div>
  );
}
