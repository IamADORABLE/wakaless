export default function VerifiedBadge({ verified }) {
  if (!verified) return null;
  return <span className="badge badge-verified">✓ Verified landlord</span>;
}
