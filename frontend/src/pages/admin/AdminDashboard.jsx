import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Stat Card Component
function StatCard({ title, value, subtitle, color, icon }) {
  const colorClasses = {
    blue: "from-blue-600/20 to-blue-600/5 border-blue-500/30",
    green: "from-green-600/20 to-green-600/5 border-green-500/30",
    purple: "from-purple-600/20 to-purple-600/5 border-purple-500/30",
    orange: "from-orange-600/20 to-orange-600/5 border-orange-500/30",
    red: "from-red-600/20 to-red-600/5 border-red-500/30",
    cyan: "from-cyan-600/20 to-cyan-600/5 border-cyan-500/30",
  };

  return (
    <div
      className={`bg-gradient-to-br ${colorClasses[color]} border rounded-xl p-6`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
          {subtitle && (
            <p className="text-gray-500 text-xs mt-1">{subtitle}</p>
          )}
        </div>
        <div className="text-gray-500">{icon}</div>
      </div>
    </div>
  );
}

// Module Card Component
function ModuleCard({ title, description, to, icon, stats }) {
  return (
    <Link
      to={to}
      className="block bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-gray-700 hover:bg-gray-900/80 transition-all group"
    >
      <div className="flex items-start gap-4">
        <div className="p-3 bg-gray-800 rounded-lg text-gray-400 group-hover:text-blue-400 transition-colors">
          {icon}
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">
            {title}
          </h3>
          <p className="text-gray-500 text-sm mt-1">{description}</p>
          {stats && (
            <div className="flex gap-4 mt-3">
              {stats.map((stat, i) => (
                <div key={i} className="text-xs">
                  <span className="text-gray-400">{stat.label}: </span>
                  <span className="text-white font-medium">{stat.value}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="text-gray-600 group-hover:text-gray-400 transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </Link>
  );
}

// Recent Order Row
function RecentOrderRow({ order }) {
  const statusColors = {
    pending: "bg-yellow-500/20 text-yellow-400",
    confirmed: "bg-blue-500/20 text-blue-400",
    in_production: "bg-purple-500/20 text-purple-400",
    ready_to_ship: "bg-cyan-500/20 text-cyan-400",
    shipped: "bg-green-500/20 text-green-400",
    completed: "bg-green-500/20 text-green-400",
    cancelled: "bg-red-500/20 text-red-400",
  };

  return (
    <tr className="border-b border-gray-800 hover:bg-gray-900/50">
      <td className="py-3 px-4 text-white font-medium">{order.order_number}</td>
      <td className="py-3 px-4 text-gray-400">{order.product_name || order.customer_name}</td>
      <td className="py-3 px-4">
        <span className={`px-2 py-1 rounded-full text-xs ${statusColors[order.status] || "bg-gray-500/20 text-gray-400"}`}>
          {order.status?.replace(/_/g, " ")}
        </span>
      </td>
      <td className="py-3 px-4 text-gray-400">${parseFloat(order.grand_total || order.total_price || 0).toFixed(2)}</td>
    </tr>
  );
}

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [pendingBOMs, setPendingBOMs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    const token = localStorage.getItem("adminToken");
    if (!token) return;

    try {
      setLoading(true);

      // Fetch summary stats
      const summaryRes = await fetch(`${API_URL}/api/v1/admin/dashboard/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!summaryRes.ok) throw new Error("Failed to fetch dashboard summary");
      const summaryData = await summaryRes.json();
      setStats(summaryData);

      // Fetch recent orders
      const ordersRes = await fetch(`${API_URL}/api/v1/admin/dashboard/recent-orders?limit=5`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (ordersRes.ok) {
        const ordersData = await ordersRes.json();
        setRecentOrders(ordersData);
      }

      // Fetch pending BOMs
      const bomsRes = await fetch(`${API_URL}/api/v1/admin/dashboard/pending-bom-reviews?limit=5`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (bomsRes.ok) {
        const bomsData = await bomsRes.json();
        setPendingBOMs(bomsData);
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-red-400">
        <h3 className="font-semibold mb-2">Error loading dashboard</h3>
        <p className="text-sm">{error}</p>
        <button
          onClick={fetchDashboardData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Welcome to the BLB3D Admin Panel</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Pending Quotes"
          value={stats?.quotes?.pending || 0}
          subtitle="Awaiting review"
          color="orange"
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
        />
        <StatCard
          title="Active Orders"
          value={stats?.orders?.in_production || 0}
          subtitle={`${stats?.orders?.confirmed || 0} confirmed, ${stats?.orders?.ready_to_ship || 0} ready`}
          color="blue"
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
          }
        />
        <StatCard
          title="In Production"
          value={stats?.production?.in_progress || 0}
          subtitle={`${stats?.production?.scheduled || 0} scheduled`}
          color="purple"
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          }
        />
        <StatCard
          title="BOMs Needing Review"
          value={stats?.boms?.needs_review || 0}
          subtitle={`${stats?.boms?.active || 0} active total`}
          color="cyan"
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
          }
        />
      </div>

      {/* Quick Access Modules */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Quick Access</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ModuleCard
            title="Quote Management"
            description="Review and approve customer quotes"
            to="/admin/quotes"
            stats={[
              { label: "Pending", value: stats?.quotes?.pending || 0 },
              { label: "This Week", value: stats?.quotes?.this_week || 0 },
            ]}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
          />
          <ModuleCard
            title="Order Management"
            description="View and manage sales orders"
            to="/admin/orders"
            stats={[
              { label: "Active", value: (stats?.orders?.confirmed || 0) + (stats?.orders?.in_production || 0) },
              { label: "Ready to Ship", value: stats?.orders?.ready_to_ship || 0 },
            ]}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            }
          />
          <ModuleCard
            title="Bill of Materials"
            description="Manage product BOMs and components"
            to="/admin/bom"
            stats={[
              { label: "Active", value: stats?.boms?.active || 0 },
              { label: "Needs Review", value: stats?.boms?.needs_review || 0 },
            ]}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            }
          />
          <ModuleCard
            title="Production"
            description="Track print jobs and production orders"
            to="/admin/production"
            stats={[
              { label: "In Progress", value: stats?.production?.in_progress || 0 },
              { label: "Scheduled", value: stats?.production?.scheduled || 0 },
            ]}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            }
          />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Orders */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-800 flex justify-between items-center">
            <h3 className="font-semibold text-white">Recent Orders</h3>
            <Link to="/admin/orders" className="text-sm text-blue-400 hover:text-blue-300">
              View all →
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-800/50">
                <tr>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Order</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Product</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Status</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Total</th>
                </tr>
              </thead>
              <tbody>
                {recentOrders.length > 0 ? (
                  recentOrders.map((order) => (
                    <RecentOrderRow key={order.id} order={order} />
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-gray-500">
                      No recent orders
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pending BOM Reviews */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-800 flex justify-between items-center">
            <h3 className="font-semibold text-white">BOMs Needing Review</h3>
            <Link to="/admin/bom" className="text-sm text-blue-400 hover:text-blue-300">
              View all →
            </Link>
          </div>
          <div className="divide-y divide-gray-800">
            {pendingBOMs.length > 0 ? (
              pendingBOMs.map((bom) => (
                <div key={bom.id} className="px-6 py-4 hover:bg-gray-800/50 transition-colors">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-white font-medium">{bom.code}</p>
                      <p className="text-sm text-gray-400">{bom.name}</p>
                    </div>
                    <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded-full">
                      Needs Review
                    </span>
                  </div>
                  <div className="mt-2 flex gap-4 text-xs text-gray-500">
                    <span>{bom.line_count || 0} components</span>
                    <span>${parseFloat(bom.total_cost || 0).toFixed(2)} cost</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-6 py-8 text-center text-gray-500">
                No BOMs pending review
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
