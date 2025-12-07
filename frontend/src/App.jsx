import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AdminLayout from "./components/AdminLayout";

// Admin pages
import AdminLogin from "./pages/admin/AdminLogin";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminOrders from "./pages/admin/AdminOrders";
import AdminBOM from "./pages/admin/AdminBOM";
import AdminProducts from "./pages/admin/AdminProducts";
import AdminItems from "./pages/admin/AdminItems";
import AdminPurchasing from "./pages/admin/AdminPurchasing";
import AdminProduction from "./pages/admin/AdminProduction";
import AdminShipping from "./pages/admin/AdminShipping";
import AdminManufacturing from "./pages/admin/AdminManufacturing";
import AdminPasswordResetApproval from "./pages/admin/AdminPasswordResetApproval";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Redirect root to admin */}
        <Route path="/" element={<Navigate to="/admin" replace />} />

        {/* Auth */}
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route
          path="/admin/password-reset/:action/:token"
          element={<AdminPasswordResetApproval />}
        />

        {/* ERP Admin Panel */}
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="orders" element={<AdminOrders />} />
          <Route path="bom" element={<AdminBOM />} />
          <Route path="products" element={<AdminProducts />} />
          <Route path="items" element={<AdminItems />} />
          <Route path="purchasing" element={<AdminPurchasing />} />
          <Route path="manufacturing" element={<AdminManufacturing />} />
          <Route path="production" element={<AdminProduction />} />
          <Route path="shipping" element={<AdminShipping />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
