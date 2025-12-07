import { useState, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function AdminShipping() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [creatingLabel, setCreatingLabel] = useState(false);

  const token = localStorage.getItem("adminToken");

  useEffect(() => {
    fetchReadyOrders();
  }, []);

  const fetchReadyOrders = async () => {
    if (!token) return;

    setLoading(true);
    try {
      // Fetch orders ready to ship
      const res = await fetch(`${API_URL}/api/v1/sales-orders/?status=ready_to_ship&limit=100`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) throw new Error("Failed to fetch orders");

      const data = await res.json();
      setOrders(data.items || data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLabel = async (orderId) => {
    setCreatingLabel(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/sales-orders/${orderId}/ship`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          carrier: "USPS",
          service: "Priority",
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to create shipping label");
      }

      const data = await res.json();
      alert(`Label created! Tracking: ${data.tracking_number}`);
      fetchReadyOrders();
      setSelectedOrder(null);
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setCreatingLabel(false);
    }
  };

  const handleMarkShipped = async (orderId) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/sales-orders/${orderId}/status`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: "shipped" }),
      });

      if (res.ok) {
        fetchReadyOrders();
        setSelectedOrder(null);
      }
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Shipping</h1>
        <p className="text-gray-400 mt-1">Manage orders ready to ship and create shipping labels</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-cyan-600/20 to-cyan-600/5 border border-cyan-500/30 rounded-xl p-6">
          <p className="text-gray-400 text-sm">Ready to Ship</p>
          <p className="text-3xl font-bold text-white mt-1">{orders.length}</p>
        </div>
        <div className="bg-gradient-to-br from-blue-600/20 to-blue-600/5 border border-blue-500/30 rounded-xl p-6">
          <p className="text-gray-400 text-sm">With Label</p>
          <p className="text-3xl font-bold text-white mt-1">
            {orders.filter((o) => o.tracking_number).length}
          </p>
        </div>
        <div className="bg-gradient-to-br from-yellow-600/20 to-yellow-600/5 border border-yellow-500/30 rounded-xl p-6">
          <p className="text-gray-400 text-sm">Needs Label</p>
          <p className="text-3xl font-bold text-white mt-1">
            {orders.filter((o) => !o.tracking_number).length}
          </p>
        </div>
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

      {/* Orders Grid */}
      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-white font-semibold">{order.order_number}</h3>
                  <p className="text-gray-500 text-sm">{order.product_name}</p>
                </div>
                {order.tracking_number ? (
                  <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded-full text-xs">
                    Has Label
                  </span>
                ) : (
                  <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded-full text-xs">
                    Needs Label
                  </span>
                )}
              </div>

              <div className="space-y-2 text-sm mb-4">
                <div className="flex justify-between">
                  <span className="text-gray-400">Quantity:</span>
                  <span className="text-white">{order.quantity}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Total:</span>
                  <span className="text-green-400">${parseFloat(order.grand_total || 0).toFixed(2)}</span>
                </div>
                {order.tracking_number && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Tracking:</span>
                    <span className="text-blue-400 font-mono text-xs">{order.tracking_number}</span>
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                {!order.tracking_number ? (
                  <button
                    onClick={() => setSelectedOrder(order)}
                    className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                  >
                    Create Label
                  </button>
                ) : (
                  <>
                    <button
                      onClick={() => handleMarkShipped(order.id)}
                      className="flex-1 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700"
                    >
                      Mark Shipped
                    </button>
                    <a
                      href={order.label_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="py-2 px-4 bg-gray-700 text-white rounded-lg text-sm hover:bg-gray-600"
                    >
                      Print
                    </a>
                  </>
                )}
              </div>
            </div>
          ))}

          {orders.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-500">
              No orders ready to ship
            </div>
          )}
        </div>
      )}

      {/* Create Label Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20">
            <div className="fixed inset-0 bg-black/70" onClick={() => setSelectedOrder(null)} />
            <div className="relative bg-gray-900 border border-gray-700 rounded-xl shadow-xl max-w-lg w-full mx-auto p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-white">Create Shipping Label</h3>
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
                <div className="bg-gray-800 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Order Details</h4>
                  <p className="text-white">{selectedOrder.order_number}</p>
                  <p className="text-gray-400 text-sm">{selectedOrder.product_name}</p>
                  <p className="text-gray-400 text-sm">Qty: {selectedOrder.quantity}</p>
                </div>

                {selectedOrder.shipping_address ? (
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-gray-300 mb-2">Ship To</h4>
                    <p className="text-white text-sm whitespace-pre-line">{selectedOrder.shipping_address}</p>
                  </div>
                ) : (
                  <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                    <p className="text-yellow-400 text-sm">No shipping address on file</p>
                  </div>
                )}

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => handleCreateLabel(selectedOrder.id)}
                    disabled={creatingLabel || !selectedOrder.shipping_address}
                    className="flex-1 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {creatingLabel ? "Creating..." : "Create USPS Priority Label"}
                  </button>
                  <button
                    onClick={() => setSelectedOrder(null)}
                    className="py-2.5 px-4 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
