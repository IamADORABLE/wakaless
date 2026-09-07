import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import RequireRole from "./components/RequireRole";
import Home from "./pages/Home";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import VerifyEmail from "./pages/VerifyEmail";
import ListingDetail from "./pages/ListingDetail";
import LandlordVerify from "./pages/LandlordVerify";
import CreateListing from "./pages/CreateListing";
import LandlordDashboard from "./pages/LandlordDashboard";
import AdminReviewQueue from "./pages/AdminReviewQueue";
import AdminVerificationQueue from "./pages/AdminVerificationQueue";
import AdminAvailabilityQueue from "./pages/AdminAvailabilityQueue";
import AdminPayouts from "./pages/AdminPayouts";
import AdminUsers from "./pages/AdminUsers";
import AdminTransactions from "./pages/AdminTransactions";
import AdminChats from "./pages/AdminChats";
import AdminChatThread from "./pages/AdminChatThread";
import RenterPayments from "./pages/RenterPayments";
import ChatThreads from "./pages/ChatThreads";
import ChatThread from "./pages/ChatThread";
import ReceiptView from "./pages/ReceiptView";
import PaymentCallback from "./pages/PaymentCallback";

export default function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/listings/:id" element={<ListingDetail />} />

        <Route path="/landlord/verify" element={<RequireRole role="landlord"><LandlordVerify /></RequireRole>} />
        <Route path="/landlord/listings/new" element={<RequireRole role="landlord"><CreateListing /></RequireRole>} />
        <Route path="/landlord/dashboard" element={<RequireRole role="landlord"><LandlordDashboard /></RequireRole>} />

        <Route path="/payments/callback" element={<RequireRole role="renter"><PaymentCallback /></RequireRole>} />
        <Route path="/renter/payments" element={<RequireRole role="renter"><RenterPayments /></RequireRole>} />
        <Route path="/renter/payments/:id/receipt" element={<RequireRole role="renter"><ReceiptView /></RequireRole>} />

        <Route path="/chat" element={<RequireRole><ChatThreads /></RequireRole>} />
        <Route path="/chat/:id" element={<RequireRole><ChatThread /></RequireRole>} />

        <Route path="/admin/review-queue" element={<RequireRole role="admin"><AdminReviewQueue /></RequireRole>} />
        <Route path="/admin/verification-queue" element={<RequireRole role="admin"><AdminVerificationQueue /></RequireRole>} />
        <Route path="/admin/availability-queue" element={<RequireRole role="admin"><AdminAvailabilityQueue /></RequireRole>} />
        <Route path="/admin/payouts" element={<RequireRole role="admin"><AdminPayouts /></RequireRole>} />
        <Route path="/admin/users" element={<RequireRole role="admin"><AdminUsers /></RequireRole>} />
        <Route path="/admin/transactions" element={<RequireRole role="admin"><AdminTransactions /></RequireRole>} />
        <Route path="/admin/chats" element={<RequireRole role="admin"><AdminChats /></RequireRole>} />
        <Route path="/admin/chats/:id" element={<RequireRole role="admin"><AdminChatThread /></RequireRole>} />
      </Routes>
    </div>
  );
}
