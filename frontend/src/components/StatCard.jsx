/**
 * Reusable StatCard component for displaying metrics across admin pages.
 *
 * Brand-aligned color scheme:
 * - primary: Emerald/cyan (brand colors)
 * - secondary: Cyan variant
 * - success: Green (positive metrics)
 * - warning: Amber/yellow (caution)
 * - danger: Red (needs attention)
 * - neutral: Gray/white (default)
 *
 * Supports two variants:
 * - "gradient" (default): Dashboard-style with gradient background and optional icon
 * - "simple": Flat card with colored value text
 */

const colorClasses = {
  // Gradient variant colors (background gradients)
  gradient: {
    // Brand colors
    primary: "from-emerald-600/20 to-cyan-600/10 border-emerald-500/30",
    secondary: "from-cyan-600/20 to-blue-600/10 border-cyan-500/30",
    // Semantic colors
    success: "from-green-600/20 to-green-600/5 border-green-500/30",
    warning: "from-amber-600/20 to-amber-600/5 border-amber-500/30",
    danger: "from-red-600/20 to-red-600/5 border-red-500/30",
    neutral: "from-gray-600/20 to-gray-600/5 border-gray-500/30",
    // Legacy support (map to new names)
    emerald: "from-emerald-600/20 to-cyan-600/10 border-emerald-500/30",
    cyan: "from-cyan-600/20 to-blue-600/10 border-cyan-500/30",
    green: "from-green-600/20 to-green-600/5 border-green-500/30",
    orange: "from-amber-600/20 to-amber-600/5 border-amber-500/30",
    red: "from-red-600/20 to-red-600/5 border-red-500/30",
    blue: "from-cyan-600/20 to-blue-600/10 border-cyan-500/30",
    purple: "from-emerald-600/20 to-cyan-600/10 border-emerald-500/30",
    yellow: "from-amber-600/20 to-amber-600/5 border-amber-500/30",
    white: "from-gray-600/20 to-gray-600/5 border-gray-500/30",
  },
  // Simple variant colors (text colors for value)
  simple: {
    // Brand colors
    primary: "text-emerald-400",
    secondary: "text-cyan-400",
    // Semantic colors
    success: "text-green-400",
    warning: "text-amber-400",
    danger: "text-red-400",
    neutral: "text-white",
    // Legacy support
    emerald: "text-emerald-400",
    cyan: "text-cyan-400",
    green: "text-green-400",
    orange: "text-amber-400",
    red: "text-red-400",
    blue: "text-cyan-400",
    purple: "text-emerald-400",
    yellow: "text-amber-400",
    white: "text-white",
  },
};

export default function StatCard({
  title,
  value,
  subtitle,
  color = "white",
  icon,
  variant = "gradient",
}) {
  if (variant === "simple") {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <p className="text-gray-400 text-sm">{title}</p>
        <p className={`text-2xl font-bold ${colorClasses.simple[color] || colorClasses.simple.white}`}>
          {value}
        </p>
        {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
      </div>
    );
  }

  // Gradient variant (default)
  return (
    <div
      className={`bg-gradient-to-br ${colorClasses.gradient[color] || colorClasses.gradient.white} border rounded-xl p-6`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
          {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
        </div>
        {icon && <div className="text-gray-500">{icon}</div>}
      </div>
    </div>
  );
}
