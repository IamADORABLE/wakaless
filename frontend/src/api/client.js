// Thin fetch wrapper around the FastAPI backend.
// Set VITE_API_BASE_URL in frontend/.env for a deployed backend; defaults
// to the local dev server FastAPI runs on (see backend/README section).
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function authHeaders() {
  const token = localStorage.getItem("wakaless_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, { method = "GET", body, isForm = false, auth = true } = {}) {
  const headers = auth ? { ...authHeaders() } : {};
  if (body && !isForm) headers["Content-Type"] = "application/json";

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
  });

  const contentType = res.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await res.json() : await res.text();

  if (!res.ok) {
    const message = (data && data.detail) || `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

export const api = {
  // auth
  signup: (payload) => request("/auth/signup", { method: "POST", body: payload, auth: false }),
  login: (payload) => request("/auth/login", { method: "POST", body: payload, auth: false }),
  verifyEmail: (token) => request("/auth/verify-email", { method: "POST", body: { token }, auth: false }),
  resendVerification: (email) => request("/auth/resend-verification", { method: "POST", body: { email }, auth: false }),
  forgotPassword: (email) => request("/auth/forgot-password", { method: "POST", body: { email }, auth: false }),
  resetPassword: (token, new_password) => request("/auth/reset-password", { method: "POST", body: { token, new_password }, auth: false }),

  // listings
  browseListings: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    return request(`/listings${qs ? `?${qs}` : ""}`, { auth: false });
  },
  getListing: (id) => request(`/listings/${id}`, { auth: false }),
  rentDurationOptions: () => request("/listings/rent-duration-options", { auth: false }),
  myListings: () => request("/listings/mine/list"),
  createListing: (payload) => request("/listings", { method: "POST", body: payload }),
  uploadListingPhoto: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/listings/photo", { method: "POST", body: form, isForm: true });
  },
  uploadOwnershipDoc: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/listings/ownership-doc", { method: "POST", body: form, isForm: true });
  },
  updateListingStatus: (id, status) =>
    request(`/listings/${id}/status`, { method: "PATCH", body: { status } }),

  // landlords / verification
  myVerification: () => request("/landlords/me/verification"),
  uploadOwnershipProof: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/landlords/me/ownership-proof", { method: "POST", body: form, isForm: true });
  },
  submitVerification: (payload) => request("/landlords/me/verify", { method: "POST", body: payload }),
  myBankDetails: () => request("/landlords/me/bank-details"),
  updateBankDetails: (payload) => request("/landlords/me/bank-details", { method: "PUT", body: payload }),
  banks: () => request("/landlords/banks"),
  resolveAccount: (accountNumber, bankCode) =>
    request(`/landlords/resolve-account?${new URLSearchParams({ account_number: accountNumber, bank_code: bankCode })}`),

  // availability
  requestAvailability: (listingId) =>
    request("/availability/request", { method: "POST", body: { listing_id: listingId } }),
  getAvailabilityStatus: (listingId) => request(`/availability/status/${listingId}`),
  myAvailabilityRequests: () => request("/availability/mine"),

  // rent payments
  initiateRentPayment: (listingId) =>
    request("/rent-payments/initiate", { method: "POST", body: { listing_id: listingId } }),
  verifyRentPayment: (reference) => request("/rent-payments/verify", { method: "POST", body: { reference } }),
  myRentPayments: () => request("/rent-payments/mine"),
  confirmInspection: (id) => request(`/rent-payments/${id}/confirm-inspection`, { method: "POST" }),
  getReceipt: (id) => request(`/rent-payments/${id}/receipt`),
  initiateRenewal: (id) => request(`/rent-payments/${id}/renew/initiate`, { method: "POST" }),
  verifyRenewal: (id, reference) => request(`/rent-payments/${id}/renew/verify`, { method: "POST", body: { reference } }),

  // chat
  chatThreads: () => request("/chat/threads"),
  chatMessages: (rentPaymentId, since) =>
    request(`/chat/${rentPaymentId}/messages${since ? `?since=${encodeURIComponent(since)}` : ""}`),
  sendChatMessage: (rentPaymentId, body) =>
    request(`/chat/${rentPaymentId}/messages`, { method: "POST", body: { body } }),

  // admin
  reviewQueue: () => request("/admin/review-queue"),
  reviewListing: (id, payload) => request(`/admin/listings/${id}/review`, { method: "POST", body: payload }),
  verificationQueue: () => request("/admin/verification-queue"),
  reviewVerification: (id, payload) => request(`/admin/verifications/${id}/review`, { method: "POST", body: payload }),
  listUsers: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    return request(`/admin/users${qs ? `?${qs}` : ""}`);
  },
  availabilityQueue: () => request("/admin/availability-queue"),
  reviewAvailability: (id, payload) => request(`/admin/availability-requests/${id}/review`, { method: "POST", body: payload }),
  payoutsQueue: () => request("/admin/payouts-queue"),
  markPayoutPaid: (id, payload) => request(`/admin/payouts/${id}/mark-paid`, { method: "POST", body: payload }),
  adminInspections: () => request("/admin/inspections"),
  adminTransactions: () => request("/admin/transactions"),
  adminChatThreads: () => request("/admin/chat-threads"),
  adminChatMessages: (rentPaymentId) => request(`/admin/chat-threads/${rentPaymentId}/messages`),

  fileUrl: (path) => (path?.startsWith("http") ? path : `${BASE_URL}${path}`),
};
