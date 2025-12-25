import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API_URL } from "../../config/api";
import StatCard from "../../components/StatCard";

// Recent Order Row - clickable to order detail
function RecentOrderRow({ order }) {
  const navigate = useNavigate();
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
    <tr
      onClick={() => navigate(`/admin/orders/${order.id}`)}
      className="border-b border-gray-800 hover:bg-gray-800/70 cursor-pointer transition-colors"
    >
      <td className="py-3 px-4 text-white font-medium">{order.order_number}</td>
      <td className="py-3 px-4 text-gray-400">
        {order.product_name || order.customer_name}
      </td>
      <td className="py-3 px-4">
        <span
          className={`px-2 py-1 rounded-full text-xs ${
            statusColors[order.status] || "bg-gray-500/20 text-gray-400"
          }`}
        >
          {order.status?.replace(/_/g, " ")}
        </span>
      </td>
      <td className="py-3 px-4 text-gray-400">
        ${parseFloat(order.grand_total || order.total_price || 0).toFixed(2)}
      </td>
      <td className="py-3 px-2 text-gray-600">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </td>
    </tr>
  );
}

// Sales & Payments trend dual line chart
function SalesChart({ data, period, onPeriodChange, loading }) {
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const chartRef = useRef(null);

  // Parse date string as local date (avoid UTC timezone shift)
  const parseLocalDate = (dateStr) => {
    if (!dateStr) return null;
    // "2025-12-22" -> parse as local date, not UTC
    const [year, month, day] = dateStr.split('-').map(Number);
    return new Date(year, month - 1, day);
  };

  // Format date as YYYY-MM-DD for comparison
  const formatDateKey = (date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  };

  // Fill in missing dates in the range with zero values
  const fillDateRange = (rawData, startDate, endDate) => {
    if (!startDate || !endDate || !rawData) return rawData || [];

    // Create a map of existing data by date
    const dataMap = {};
    (rawData || []).forEach(d => {
      dataMap[d.date] = d;
    });

    // Parse start and end dates
    const start = parseLocalDate(startDate.split('T')[0]);
    const end = parseLocalDate(endDate.split('T')[0]);
    if (!start || !end) return rawData || [];

    // Generate all dates in range
    const filledData = [];
    const current = new Date(start);
    while (current <= end) {
      const dateKey = formatDateKey(current);
      if (dataMap[dateKey]) {
        filledData.push(dataMap[dateKey]);
      } else {
        // Add zero entry for missing date
        filledData.push({
          date: dateKey,
          total: 0,
          sales: 0,
          orders: 0,
          payments: 0,
          payment_count: 0,
        });
      }
      current.setDate(current.getDate() + 1);
    }

    return filledData;
  };

  const periods = [
    { key: "WTD", label: "Week" },
    { key: "MTD", label: "Month" },
    { key: "QTD", label: "Quarter" },
    { key: "YTD", label: "Year" },
    { key: "ALL", label: "All" },
  ];

  // Calculate chart dimensions
  const chartHeight = 120;

  if (loading) {
    return (
      <div className="h-40 flex items-center justify-center">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Fill in all dates in the period range (show zeros for days with no activity)
  const dataPoints = fillDateRange(data?.data, data?.start_date, data?.end_date);

  // Calculate cumulative values for proper trend display
  let cumulativeSales = 0;
  let cumulativePayments = 0;
  const cumulativeData = dataPoints.map((d) => {
    cumulativeSales += d.sales || d.total || 0;
    cumulativePayments += d.payments || 0;
    return {
      ...d,
      cumulativeSales,
      cumulativePayments,
    };
  });

  // Use max of both cumulative totals for consistent scale
  const maxCumulativeSales = cumulativeData.length > 0 ? cumulativeData[cumulativeData.length - 1].cumulativeSales : 1;
  const maxCumulativePayments = cumulativeData.length > 0 ? cumulativeData[cumulativeData.length - 1].cumulativePayments : 1;
  const maxValue = Math.max(maxCumulativeSales, maxCumulativePayments, 1);

  // Max daily orders for bar scaling
  const maxDailyOrders = Math.max(...dataPoints.map(d => d.orders || 0), 1);

  // Generate SVG path for sales line (cumulative)
  const generateSalesPath = () => {
    if (cumulativeData.length === 0) return "";

    const points = cumulativeData.map((d, i) => {
      const x = (i / Math.max(cumulativeData.length - 1, 1)) * 100;
      const y = 100 - (d.cumulativeSales / maxValue) * 100;
      return `${x},${y}`;
    });

    return `M ${points.join(" L ")}`;
  };

  // Generate SVG path for payments line (cumulative)
  const generatePaymentsPath = () => {
    if (cumulativeData.length === 0) return "";

    const points = cumulativeData.map((d, i) => {
      const x = (i / Math.max(cumulativeData.length - 1, 1)) * 100;
      const y = 100 - (d.cumulativePayments / maxValue) * 100;
      return `${x},${y}`;
    });

    return `M ${points.join(" L ")}`;
  };

  // Generate area fill path for sales (cumulative)
  const generateSalesAreaPath = () => {
    if (cumulativeData.length === 0) return "";

    const points = cumulativeData.map((d, i) => {
      const x = (i / Math.max(cumulativeData.length - 1, 1)) * 100;
      const y = 100 - (d.cumulativeSales / maxValue) * 100;
      return `${x},${y}`;
    });

    return `M 0,100 L ${points.join(" L ")} L 100,100 Z`;
  };

  const formatCurrency = (value) => {
    if (value >= 1000) return `$${(value / 1000).toFixed(1)}k`;
    return `$${value.toFixed(0)}`;
  };

  // Handle mouse move for tooltip positioning
  const handleMouseMove = (e, index) => {
    if (chartRef.current) {
      const rect = chartRef.current.getBoundingClientRect();
      setMousePos({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    }
    setHoveredIndex(index);
  };

  // Get hovered data point info
  const getHoveredData = () => {
    if (hoveredIndex === null || !cumulativeData[hoveredIndex]) return null;
    const d = cumulativeData[hoveredIndex];
    const outstanding = d.cumulativeSales - d.cumulativePayments;
    const localDate = parseLocalDate(d.date);
    return {
      date: localDate ? localDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '',
      orders: d.orders || 0,
      dailySales: d.sales || d.total || 0,
      dailyPayments: d.payments || 0,
      cumulativeSales: d.cumulativeSales,
      cumulativePayments: d.cumulativePayments,
      outstanding,
    };
  };

  const totalRevenue = data?.total_revenue || 0;
  const totalPayments = data?.total_payments || 0;
  const outstanding = totalRevenue - totalPayments;

  return (
    <div>
      {/* Period selector */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-1">
          {periods.map((p) => (
            <button
              key={p.key}
              onClick={() => onPeriodChange(p.key)}
              className={`px-3 py-1 text-xs rounded-md transition-colors ${
                period === p.key
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
        {/* Summary stats with both sales and payments */}
        <div className="flex gap-4 text-right">
          <div>
            <p className="text-sm font-semibold text-blue-400">
              {formatCurrency(totalRevenue)}
            </p>
            <p className="text-xs text-gray-500">
              {data?.total_orders || 0} orders
            </p>
          </div>
          <div>
            <p className="text-sm font-semibold text-green-400">
              {formatCurrency(totalPayments)}
            </p>
            <p className="text-xs text-gray-500">
              collected
            </p>
          </div>
          {outstanding > 0 && (
            <div>
              <p className="text-sm font-semibold text-yellow-400">
                {formatCurrency(outstanding)}
              </p>
              <p className="text-xs text-gray-500">
                outstanding
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="flex gap-4 mb-2 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-2 h-3 bg-gray-500/30 rounded-sm"></div>
          <span className="text-gray-500">Daily Orders</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-0.5 bg-blue-500"></div>
          <span className="text-gray-400">Cumulative Orders</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-0.5 bg-green-500"></div>
          <span className="text-gray-400">Cumulative Payments</span>
        </div>
      </div>

      {/* Chart */}
      {dataPoints.length > 0 ? (
        <div
          ref={chartRef}
          className="relative"
          style={{ height: chartHeight }}
          onMouseLeave={() => setHoveredIndex(null)}
        >
          <svg
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            className="w-full h-full"
          >
            {/* Grid lines */}
            <line x1="0" y1="25" x2="100" y2="25" stroke="#374151" strokeWidth="0.5" />
            <line x1="0" y1="50" x2="100" y2="50" stroke="#374151" strokeWidth="0.5" />
            <line x1="0" y1="75" x2="100" y2="75" stroke="#374151" strokeWidth="0.5" />

            {/* Daily order count bars (background) */}
            {dataPoints.map((d, i) => {
              const barWidth = 100 / Math.max(dataPoints.length, 1) * 0.6;
              const x = (i / Math.max(dataPoints.length - 1, 1)) * 100 - barWidth / 2;
              const barHeight = ((d.orders || 0) / maxDailyOrders) * 100;
              return (
                <rect
                  key={`bar-${i}`}
                  x={Math.max(0, x)}
                  y={100 - barHeight}
                  width={barWidth}
                  height={barHeight}
                  fill="url(#barGradient)"
                  opacity="0.3"
                />
              );
            })}

            {/* Sales area fill */}
            <path
              d={generateSalesAreaPath()}
              fill="url(#salesGradient)"
              opacity="0.2"
            />

            {/* Sales line (blue) */}
            <path
              d={generateSalesPath()}
              fill="none"
              stroke="#3b82f6"
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
            />

            {/* Payments line (green) */}
            <path
              d={generatePaymentsPath()}
              fill="none"
              stroke="#22c55e"
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
            />

            {/* Hover targets (invisible rectangles for each data point) */}
            {dataPoints.map((d, i) => {
              const sliceWidth = 100 / dataPoints.length;
              const x = i * sliceWidth;
              return (
                <rect
                  key={`hover-${i}`}
                  x={x}
                  y={0}
                  width={sliceWidth}
                  height={100}
                  fill="transparent"
                  onMouseMove={(e) => handleMouseMove(e, i)}
                  style={{ cursor: 'crosshair' }}
                />
              );
            })}

            {/* Hover indicator circles */}
            {hoveredIndex !== null && cumulativeData[hoveredIndex] && (
              <>
                <circle
                  cx={(hoveredIndex / Math.max(cumulativeData.length - 1, 1)) * 100}
                  cy={100 - (cumulativeData[hoveredIndex].cumulativeSales / maxValue) * 100}
                  r="3"
                  fill="#3b82f6"
                  stroke="white"
                  strokeWidth="1"
                  vectorEffect="non-scaling-stroke"
                />
                <circle
                  cx={(hoveredIndex / Math.max(cumulativeData.length - 1, 1)) * 100}
                  cy={100 - (cumulativeData[hoveredIndex].cumulativePayments / maxValue) * 100}
                  r="3"
                  fill="#22c55e"
                  stroke="white"
                  strokeWidth="1"
                  vectorEffect="non-scaling-stroke"
                />
              </>
            )}

            {/* Gradient definitions */}
            <defs>
              <linearGradient id="salesGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
              </linearGradient>
              <linearGradient id="barGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#6b7280" />
                <stop offset="100%" stopColor="#6b7280" stopOpacity="0.2" />
              </linearGradient>
            </defs>
          </svg>

          {/* Y-axis labels */}
          <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-gray-600 pointer-events-none">
            <span>{formatCurrency(maxValue)}</span>
            <span>{formatCurrency(maxValue / 2)}</span>
            <span>$0</span>
          </div>

          {/* Tooltip */}
          {hoveredIndex !== null && getHoveredData() && (
            <div
              className="absolute z-10 bg-gray-800 border border-gray-700 rounded-lg shadow-lg p-3 pointer-events-none"
              style={{
                left: Math.min(mousePos.x + 10, chartRef.current?.offsetWidth - 180 || 0),
                top: Math.max(mousePos.y - 80, 0),
                minWidth: '160px',
              }}
            >
              {(() => {
                const d = getHoveredData();
                return (
                  <>
                    <div className="text-white font-medium text-sm mb-2">{d.date}</div>
                    <div className="space-y-1 text-xs">
                      <div className="flex justify-between gap-4">
                        <span className="text-gray-400">Orders:</span>
                        <span className="text-white font-medium">{d.orders}</span>
                      </div>
                      <div className="flex justify-between gap-4">
                        <span className="text-blue-400">Day Sales:</span>
                        <span className="text-white">${d.dailySales.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between gap-4">
                        <span className="text-green-400">Day Payments:</span>
                        <span className="text-white">${d.dailyPayments.toFixed(2)}</span>
                      </div>
                      <div className="border-t border-gray-700 my-1 pt-1">
                        <div className="flex justify-between gap-4">
                          <span className="text-blue-400">Total Orders:</span>
                          <span className="text-white">${d.cumulativeSales.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between gap-4">
                          <span className="text-green-400">Total Paid:</span>
                          <span className="text-white">${d.cumulativePayments.toFixed(2)}</span>
                        </div>
                        {d.outstanding > 0 && (
                          <div className="flex justify-between gap-4">
                            <span className="text-yellow-400">Outstanding:</span>
                            <span className="text-yellow-400 font-medium">${d.outstanding.toFixed(2)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </>
                );
              })()}
            </div>
          )}
        </div>
      ) : (
        <div className="h-32 flex items-center justify-center text-gray-500 text-sm">
          No data for this period
        </div>
      )}

      {/* X-axis date range */}
      {dataPoints.length > 0 && (
        <div className="flex justify-between text-xs text-gray-500 mt-2">
          <span>{dataPoints[0]?.date ? parseLocalDate(dataPoints[0].date)?.toLocaleDateString() : ""}</span>
          <span>{dataPoints[dataPoints.length - 1]?.date ? parseLocalDate(dataPoints[dataPoints.length - 1].date)?.toLocaleDateString() : ""}</span>
        </div>
      )}
    </div>
  );
}

// Simple horizontal bar chart for production pipeline
function ProductionPipeline({ stats }) {
  const stages = [
    { key: "draft", label: "Draft", count: stats?.production?.draft || 0, color: "bg-gray-500" },
    { key: "released", label: "Released", count: stats?.production?.released || 0, color: "bg-blue-500" },
    { key: "scheduled", label: "Scheduled", count: stats?.production?.scheduled || 0, color: "bg-cyan-500" },
    { key: "in_progress", label: "In Progress", count: stats?.production?.in_progress || 0, color: "bg-purple-500" },
    { key: "complete", label: "Complete", count: stats?.production?.complete_today || 0, color: "bg-green-500" },
  ];

  const total = stages.reduce((sum, s) => sum + s.count, 0);
  if (total === 0) return null;

  return (
    <div className="space-y-2">
      <div className="flex h-4 rounded-full overflow-hidden bg-gray-800">
        {stages.map((stage) => (
          stage.count > 0 && (
            <Link
              key={stage.key}
              to={`/admin/production?status=${stage.key}`}
              className={`${stage.color} hover:opacity-80 transition-opacity`}
              style={{ width: `${(stage.count / total) * 100}%` }}
              title={`${stage.label}: ${stage.count}`}
            />
          )
        ))}
      </div>
      <div className="flex flex-wrap gap-3 text-xs">
        {stages.map((stage) => (
          <Link
            key={stage.key}
            to={`/admin/production?status=${stage.key}`}
            className="flex items-center gap-1.5 hover:opacity-80"
          >
            <span className={`w-2 h-2 rounded-full ${stage.color}`}></span>
            <span className="text-gray-400">{stage.label}:</span>
            <span className="text-white font-medium">{stage.count}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [pendingPOs, setPendingPOs] = useState([]);
  const [salesData, setSalesData] = useState(null);
  const [salesPeriod, setSalesPeriod] = useState("MTD");
  const [salesLoading, setSalesLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Fetch sales trend data when period changes
  useEffect(() => {
    fetchSalesData(salesPeriod);
  }, [salesPeriod]);

  const fetchSalesData = async (period) => {
    const token = localStorage.getItem("adminToken");
    if (!token) return;

    setSalesLoading(true);
    try {
      const res = await fetch(
        `${API_URL}/api/v1/admin/dashboard/sales-trend?period=${period}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setSalesData(data);
      }
    } catch (err) {
      console.error("Failed to fetch sales data:", err);
    } finally {
      setSalesLoading(false);
    }
  };

  // Format revenue with smart display (show actual $ under 1k, otherwise Xk)
  const formatRevenue = (amount) => {
    if (amount < 1000) {
      return `$${amount.toFixed(0)}`;
    }
    return `$${(amount / 1000).toFixed(1)}k`;
  };

  const fetchDashboardData = async () => {
    const token = localStorage.getItem("adminToken");
    if (!token) {
      setError("Authentication required");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);

      // Fetch summary stats
      const summaryRes = await fetch(
        `${API_URL}/api/v1/admin/dashboard/summary`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!summaryRes.ok) throw new Error("Failed to fetch dashboard summary");
      const summaryData = await summaryRes.json();
      setStats(summaryData);

      // Fetch recent orders
      const ordersRes = await fetch(
        `${API_URL}/api/v1/admin/dashboard/recent-orders?limit=5`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (ordersRes.ok) {
        const ordersData = await ordersRes.json();
        setRecentOrders(ordersData);
      }

      // Fetch pending purchase orders
      const posRes = await fetch(
        `${API_URL}/api/v1/purchase-orders?status=draft,ordered&limit=5`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (posRes.ok) {
        const posData = await posRes.json();
        setPendingPOs(posData.items || posData || []);
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
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-red-400 flex flex-col">
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
        <p className="text-gray-400 mt-1">Welcome to the FilaOps Admin Panel</p>
      </div>

      {/* Sales Trend Chart - Primary KPI */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <SalesChart
          data={salesData}
          period={salesPeriod}
          onPeriodChange={setSalesPeriod}
          loading={salesLoading}
        />
      </div>

      {/* Action Items Section */}
      {(stats?.orders?.overdue > 0 ||
        stats?.inventory?.low_stock_count > 0 ||
        stats?.production?.ready_to_start > 0 ||
        stats?.orders?.ready_to_ship > 0 ||
        stats?.quotes?.pending > 0) && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800 flex items-center gap-2">
            <svg
              className="w-5 h-5 text-blue-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
              />
            </svg>
            <h3 className="font-semibold text-white">Action Items</h3>
          </div>
          <div className="divide-y divide-gray-800">
            {/* Critical - Overdue */}
            {stats?.orders?.overdue > 0 && (
              <Link
                to="/admin/orders?status=overdue"
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-800/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-red-500"></span>
                  <span className="text-white">
                    {stats.orders.overdue} Overdue Order{stats.orders.overdue !== 1 ? "s" : ""}
                  </span>
                </div>
                <span className="text-xs text-red-400 font-medium">URGENT</span>
              </Link>
            )}
            {/* Warning - Low Stock */}
            {stats?.inventory?.low_stock_count > 0 && (
              <Link
                to="/admin/purchasing?tab=low-stock"
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-800/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                  <span className="text-white">
                    {stats.inventory.low_stock_count} Low Stock Item{stats.inventory.low_stock_count !== 1 ? "s" : ""}
                  </span>
                </div>
                <span className="text-xs text-yellow-400">Reorder needed</span>
              </Link>
            )}
            {/* Action - Quotes */}
            {stats?.quotes?.pending > 0 && (
              <Link
                to="/admin/quotes"
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-800/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  <span className="text-white">
                    {stats.quotes.pending} Pending Quote{stats.quotes.pending !== 1 ? "s" : ""}
                  </span>
                </div>
                <span className="text-xs text-blue-400">Respond</span>
              </Link>
            )}
            {/* Ready - Production */}
            {stats?.production?.ready_to_start > 0 && (
              <Link
                to="/admin/production?status=released"
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-800/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-green-500"></span>
                  <span className="text-white">
                    {stats.production.ready_to_start} Order{stats.production.ready_to_start !== 1 ? "s" : ""} Ready to Start
                  </span>
                </div>
                <span className="text-xs text-green-400">Start production</span>
              </Link>
            )}
            {/* Ready - Shipping */}
            {stats?.orders?.ready_to_ship > 0 && (
              <Link
                to="/admin/shipping"
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-800/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-cyan-500"></span>
                  <span className="text-white">
                    {stats.orders.ready_to_ship} Order{stats.orders.ready_to_ship !== 1 ? "s" : ""} Ready to Ship
                  </span>
                </div>
                <span className="text-xs text-cyan-400">Ship</span>
              </Link>
            )}
          </div>
        </div>
      )}

      {/* SALES Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Sales
          </h2>
          <div className="flex-1 h-px bg-gray-800"></div>
          <Link
            to="/admin/orders"
            className="text-xs text-blue-400 hover:text-blue-300"
            aria-label="View all Sales"
          >
            View all →
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Pending Quotes"
            value={stats?.quotes?.pending || 0}
            subtitle="Awaiting review"
            color="warning"
            to="/admin/quotes"
          />
          <StatCard
            title="Orders in Progress"
            value={
              (stats?.orders?.confirmed || 0) +
              (stats?.orders?.in_production || 0)
            }
            subtitle={`${stats?.orders?.confirmed || 0} confirmed, ${
              stats?.orders?.in_production || 0
            } in production`}
            color="primary"
            to="/admin/orders"
          />
          <StatCard
            title="Ready to Ship"
            value={stats?.orders?.ready_to_ship || 0}
            subtitle={`${stats?.orders?.overdue || 0} overdue`}
            color={stats?.orders?.overdue > 0 ? "danger" : "success"}
            to="/admin/shipping"
          />
          <StatCard
            title="Revenue (30 Days)"
            value={formatRevenue(stats?.revenue?.last_30_days || 0)}
            subtitle={`${stats?.revenue?.orders_last_30_days || 0} orders`}
            color="success"
            to="/admin/payments"
          />
        </div>
      </div>

      {/* INVENTORY Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Inventory
          </h2>
          <div className="flex-1 h-px bg-gray-800"></div>
          <Link
            to="/admin/items"
            className="text-xs text-blue-400 hover:text-blue-300"
            aria-label="View all Inventory"
          >
            View all →
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard
            title="Low Stock Items"
            value={stats?.inventory?.low_stock_count || 0}
            subtitle="Below reorder point or MRP shortage"
            color={stats?.inventory?.low_stock_count > 0 ? "danger" : "success"}
            to="/admin/purchasing?tab=low-stock"
          />
          <StatCard
            title="Active BOMs"
            value={stats?.boms?.active || 0}
            subtitle={`${stats?.boms?.needs_review || 0} need review`}
            color="secondary"
            to="/admin/bom"
          />
          <StatCard
            title="Orders Needing Materials"
            value={stats?.inventory?.active_orders || 0}
            subtitle="For MRP planning"
            color="neutral"
            to="/admin/purchasing"
          />
        </div>
      </div>

      {/* PRODUCTION Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Production
          </h2>
          <div className="flex-1 h-px bg-gray-800"></div>
          <Link
            to="/admin/production"
            className="text-xs text-blue-400 hover:text-blue-300"
            aria-label="View all Production"
          >
            View all →
          </Link>
        </div>

        {/* Production Pipeline Chart */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-4">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Production Pipeline</h3>
          <ProductionPipeline stats={stats} />
          {!stats?.production?.in_progress && !stats?.production?.scheduled && !stats?.production?.draft && !stats?.production?.released && (
            <p className="text-gray-500 text-sm text-center py-4">No active production orders</p>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <StatCard
            title="Work Orders In Progress"
            value={stats?.production?.in_progress || 0}
            subtitle={`${stats?.production?.ready_to_start || 0} ready to start`}
            color="primary"
            to="/admin/production?status=in_progress"
          />
          <StatCard
            title="Completed Today"
            value={stats?.production?.complete_today || 0}
            subtitle="Units finished"
            color="success"
            to="/admin/manufacturing"
          />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Orders */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-800 flex justify-between items-center">
            <h3 className="font-semibold text-white">Recent Orders</h3>
            <Link
              to="/admin/orders"
              className="text-sm text-blue-400 hover:text-blue-300"
              aria-label="View all Orders"
            >
              View all →
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-800/50">
                <tr>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    Order
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    Product
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    Status
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    Total
                  </th>
                  <th className="w-8"></th>
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

        {/* Pending Purchase Orders */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-800 flex justify-between items-center">
            <h3 className="font-semibold text-white">Pending Purchases</h3>
            <Link
              to="/admin/purchasing"
              aria-label="View all Purchases"
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              View all →
            </Link>
          </div>
          <div className="divide-y divide-gray-800">
            {pendingPOs.length > 0 ? (
              pendingPOs.map((po) => (
                <Link
                  key={po.id}
                  to={`/admin/purchasing?po=${po.id}`}
                  className="block px-6 py-4 hover:bg-gray-800/50 transition-colors cursor-pointer"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-white font-medium">{po.po_number || `PO-${po.id}`}</p>
                      <p className="text-sm text-gray-400">{po.vendor_name || "No vendor"}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        po.status === "draft"
                          ? "bg-gray-500/20 text-gray-400"
                          : po.status === "ordered"
                          ? "bg-blue-500/20 text-blue-400"
                          : "bg-purple-500/20 text-purple-400"
                      }`}>
                        {po.status?.charAt(0).toUpperCase() + po.status?.slice(1)}
                      </span>
                      <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                  <div className="mt-2 flex gap-4 text-xs text-gray-500">
                    <span>{po.line_count || po.lines?.length || 0} items</span>
                    <span>
                      ${parseFloat(po.total_amount || po.total || 0).toFixed(2)}
                    </span>
                    {po.expected_date && (
                      <span>Due: {new Date(po.expected_date).toLocaleDateString()}</span>
                    )}
                  </div>
                </Link>
              ))
            ) : (
              <div className="px-6 py-8 text-center text-gray-500">
                No pending purchase orders
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
