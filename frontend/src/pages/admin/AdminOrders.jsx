import { useState, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const statusColors = {
  pending: "bg-yellow-500/20 text-yellow-400",
  confirmed: "bg-blue-500/20 text-blue-400",
  in_production: "bg-purple-500/20 text-purple-400",
  ready_to_ship: "bg-cyan-500/20 text-cyan-400",
  shipped: "bg-green-500/20 text-green-400",
  completed: "bg-green-500/20 text-green-400",
  cancelled: "bg-red-500/20 text-red-400",
};

const paymentColors = {
  pending: "bg-yellow-500/20 text-yellow-400",
  paid: "bg-green-500/20 text-green-400",
  failed: "bg-red-500/20 text-red-400",
  refunded: "bg-gray-500/20 text-gray-400",
};

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    status: "all",
    search: "",
  });
  const [selectedOrder, setSelectedOrder] = useState(null);

  const token = localStorage.getItem("adminToken");

  useEffect(() => {
    fetchOrders();
  }, [filters.status]);

  const fetchOrders = async () => {
    if (!token) return;

    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.status !== "all") params.set("status", filters.status);
      params.set("limit", "100");

      const res = await fetch(`${API_URL}/api/v1/sales-orders/?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) throw new Error("Failed to fetch orders");

      const data = await res.json();
      setOrders(data.items || data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (orderId, newStatus) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/sales-orders/${orderId}/status`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (res.ok) {
        fetchOrders();
        if (selectedOrder?.id === orderId) {
          const updated = await res.json();
          setSelectedOrder(updated);
        }
      }
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  const filteredOrders = orders.filter((o) => {
    if (!filters.search) return true;
    const search = filters.search.toLowerCase();
    return (
      o.order_number?.toLowerCase().includes(search) ||
      o.product_name?.toLowerCase().includes(search) ||
      o.user?.email?.toLowerCase().includes(search)
    );
  });

  const getNextStatus = (currentStatus) => {
    const flow = {
      pending: "confirmed",
      confirmed: "in_production",
      in_production: "ready_to_ship",
      ready_to_ship: "shipped",
      shipped: "completed",
    };
    return flow[currentStatus];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Order Management</h1>
        <p className="text-gray-400 mt-1">View and manage sales orders</p>
      </div>

      {/* Filters */}
      <div className="flex gap-4 bg-gray-900 border border-gray-800 rounded-xl p-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search by order number, product, or customer..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500"
          />
        </div>
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="confirmed">Confirmed</option>
          <option value="in_production">In Production</option>
          <option value="ready_to_ship">Ready to Ship</option>
          <option value="shipped">Shipped</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      )}

      {/* Orders Table */}
      {!loading && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-800/50">
              <tr>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Order #</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Customer</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Product</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Qty</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Total</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Status</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Payment</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Created</th>
                <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.map((order) => (
                <tr key={order.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                  <td className="py-3 px-4 text-white font-medium">{order.order_number}</td>
                  <td className="py-3 px-4 text-gray-400">{order.user?.email || "N/A"}</td>
                  <td className="py-3 px-4 text-gray-300">{order.product_name}</td>
                  <td className="py-3 px-4 text-gray-400">{order.quantity}</td>
                  <td className="py-3 px-4 text-green-400 font-medium">
                    ${parseFloat(order.grand_total || order.total_price || 0).toFixed(2)}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${statusColors[order.status] || "bg-gray-500/20 text-gray-400"}`}>
                      {order.status?.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${paymentColors[order.payment_status] || "bg-gray-500/20 text-gray-400"}`}>
                      {order.payment_status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-500 text-sm">
                    {new Date(order.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4 text-right space-x-2">
                    <button
                      onClick={() => setSelectedOrder(order)}
                      className="text-blue-400 hover:text-blue-300 text-sm"
                    >
                      View
                    </button>
                    {getNextStatus(order.status) && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, getNextStatus(order.status))}
                        className="text-green-400 hover:text-green-300 text-sm"
                      >
                        Advance
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {filteredOrders.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-gray-500">
                    No orders found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Order Detail Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20">
            <div className="fixed inset-0 bg-black/70" onClick={() => setSelectedOrder(null)} />
            <div className="relative bg-gray-900 border border-gray-700 rounded-xl shadow-xl max-w-2xl w-full mx-auto p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-white">
                  Order: {selectedOrder.order_number}
                </h3>
                <button
                  onClick={() => setSelectedOrder(null)}
                  className="text-gray-400 hover:text-white p-1"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Product:</span>
                    <p className="text-white">{selectedOrder.product_name}</p>
                  </div>
                  <div>
                    <span className="text-gray-400">Material:</span>
                    <p className="text-white">{selectedOrder.material_type} / {selectedOrder.color || "N/A"}</p>
                  </div>
                  <div>
                    <span className="text-gray-400">Quantity:</span>
                    <p className="text-white">{selectedOrder.quantity}</p>
                  </div>
                  <div>
                    <span className="text-gray-400">Unit Price:</span>
                    <p className="text-white">${parseFloat(selectedOrder.unit_price || 0).toFixed(2)}</p>
                  </div>
                  <div>
                    <span className="text-gray-400">Grand Total:</span>
                    <p className="text-green-400 font-semibold">${parseFloat(selectedOrder.grand_total || 0).toFixed(2)}</p>
                  </div>
                  <div>
                    <span className="text-gray-400">Source:</span>
                    <p className="text-white">{selectedOrder.source} ({selectedOrder.order_type})</p>
                  </div>
                </div>

                {/* Shipping Info */}
                {selectedOrder.shipping_address && (
                  <div className="bg-gray-800 p-4 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-300 mb-2">Shipping Address</h4>
                    <p className="text-white text-sm whitespace-pre-line">{selectedOrder.shipping_address}</p>
                  </div>
                )}

                {/* Status Flow */}
                <div className="flex gap-2 pt-4 border-t border-gray-800">
                  {["confirmed", "in_production", "ready_to_ship", "shipped", "completed"].map((status) => (
                    <button
                      key={status}
                      onClick={() => handleStatusUpdate(selectedOrder.id, status)}
                      disabled={selectedOrder.status === status}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        selectedOrder.status === status
                          ? "bg-blue-600 text-white"
                          : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white"
                      }`}
                    >
                      {status.replace(/_/g, " ")}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
