import { useState, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Item type options
const ITEM_TYPES = [
  { value: "finished_good", label: "Finished Good", color: "blue" },
  { value: "component", label: "Component", color: "purple" },
  { value: "supply", label: "Supply", color: "orange" },
  { value: "service", label: "Service", color: "green" },
];

// Cost method options
const COST_METHODS = [
  { value: "average", label: "Average Cost" },
  { value: "standard", label: "Standard Cost" },
  { value: "fifo", label: "FIFO" },
];

export default function AdminItems() {
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [categoryTree, setCategoryTree] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [expandedCategories, setExpandedCategories] = useState(new Set());
  const [filters, setFilters] = useState({
    search: "",
    itemType: "all",
    activeOnly: true,
  });

  // Modal states
  const [showItemModal, setShowItemModal] = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);

  // Recost states
  const [recosting, setRecosting] = useState(false);
  const [recostResult, setRecostResult] = useState(null);

  const token = localStorage.getItem("adminToken");

  useEffect(() => {
    fetchCategories();
    fetchItems();
  }, [selectedCategory, filters.itemType, filters.activeOnly]);

  const fetchCategories = async () => {
    if (!token) return;
    try {
      // Fetch flat list
      const res = await fetch(`${API_URL}/api/v1/items/categories?include_inactive=true`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch categories");
      const data = await res.json();
      setCategories(data);

      // Fetch tree structure
      const treeRes = await fetch(`${API_URL}/api/v1/items/categories/tree`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (treeRes.ok) {
        const treeData = await treeRes.json();
        setCategoryTree(treeData);
      }
    } catch (err) {
      console.error("Category fetch error:", err);
    }
  };

  const fetchItems = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", "200");
      params.set("active_only", filters.activeOnly.toString());
      if (selectedCategory) params.set("category_id", selectedCategory.toString());
      if (filters.itemType !== "all") params.set("item_type", filters.itemType);

      const res = await fetch(`${API_URL}/api/v1/items?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch items");
      const data = await res.json();
      setItems(data.items || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredItems = items.filter((item) => {
    if (!filters.search) return true;
    const search = filters.search.toLowerCase();
    return (
      item.sku?.toLowerCase().includes(search) ||
      item.name?.toLowerCase().includes(search) ||
      item.upc?.toLowerCase().includes(search)
    );
  });

  // Toggle category expand/collapse
  const toggleExpand = (categoryId) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(categoryId)) {
        next.delete(categoryId);
      } else {
        next.add(categoryId);
      }
      return next;
    });
  };

  // Category tree component
  const CategoryNode = ({ node, depth = 0 }) => {
    const hasChildren = node.children?.length > 0;
    const isExpanded = expandedCategories.has(node.id);
    const isSelected = selectedCategory === node.id;

    return (
      <div>
        <div
          className={`flex items-center rounded-lg text-sm transition-colors ${
            isSelected
              ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
              : "text-gray-400 hover:bg-gray-800 hover:text-white"
          }`}
          style={{ paddingLeft: `${8 + depth * 12}px` }}
        >
          {/* Expand/Collapse toggle */}
          {hasChildren ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleExpand(node.id);
              }}
              className="p-1 hover:text-white"
            >
              <span className="text-xs">{isExpanded ? "▼" : "▶"}</span>
            </button>
          ) : (
            <span className="w-5" /> // Spacer for alignment
          )}

          {/* Category name - click to filter */}
          <button
            onClick={() => setSelectedCategory(isSelected ? null : node.id)}
            className="flex-1 text-left py-2 pr-2"
          >
            {node.name}
          </button>
        </div>

        {/* Children - only show if expanded */}
        {hasChildren && isExpanded && (
          <div>
            {node.children.map((child) => (
              <CategoryNode key={child.id} node={child} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    );
  };

  // Stats calculations
  const stats = {
    total: items.length,
    finishedGoods: items.filter((i) => i.item_type === "finished_good").length,
    components: items.filter((i) => i.item_type === "component").length,
    supplies: items.filter((i) => i.item_type === "supply").length,
    needsReorder: items.filter((i) => i.needs_reorder).length,
  };

  const getItemTypeStyle = (type) => {
    const found = ITEM_TYPES.find((t) => t.value === type);
    if (!found) return "bg-gray-500/20 text-gray-400";
    return {
      blue: "bg-blue-500/20 text-blue-400",
      purple: "bg-purple-500/20 text-purple-400",
      orange: "bg-orange-500/20 text-orange-400",
      green: "bg-green-500/20 text-green-400",
    }[found.color];
  };

  // Save item
  const handleSaveItem = async (itemData) => {
    try {
      const url = editingItem
        ? `${API_URL}/api/v1/items/${editingItem.id}`
        : `${API_URL}/api/v1/items`;
      const method = editingItem ? "PATCH" : "POST";

      const res = await fetch(url, {
        method,
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(itemData),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to save item");
      }

      setShowItemModal(false);
      setEditingItem(null);
      fetchItems();
    } catch (err) {
      alert(err.message);
    }
  };

  // Save category
  const handleSaveCategory = async (catData) => {
    try {
      const url = editingCategory
        ? `${API_URL}/api/v1/items/categories/${editingCategory.id}`
        : `${API_URL}/api/v1/items/categories`;
      const method = editingCategory ? "PATCH" : "POST";

      const res = await fetch(url, {
        method,
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(catData),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to save category");
      }

      setShowCategoryModal(false);
      setEditingCategory(null);
      fetchCategories();
    } catch (err) {
      alert(err.message);
    }
  };

  // Recost all items
  const handleRecostAll = async () => {
    if (!confirm("Recost all items? This will update standard costs from BOM/Routing (manufactured) or average cost (purchased).")) {
      return;
    }
    setRecosting(true);
    setRecostResult(null);
    try {
      const params = new URLSearchParams();
      if (selectedCategory) params.set("category_id", selectedCategory.toString());
      if (filters.itemType !== "all") params.set("item_type", filters.itemType);

      const res = await fetch(`${API_URL}/api/v1/items/recost-all?${params}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to recost items");
      }

      const data = await res.json();
      setRecostResult(data);
      fetchItems(); // Refresh list to show new costs
    } catch (err) {
      alert(err.message);
    } finally {
      setRecosting(false);
    }
  };

  return (
    <div className="flex gap-6 h-full">
      {/* Left Sidebar - Categories */}
      <div className="w-64 flex-shrink-0">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-white">Categories</h2>
            <button
              onClick={() => {
                setEditingCategory(null);
                setShowCategoryModal(true);
              }}
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              + Add
            </button>
          </div>

          <button
            onClick={() => setSelectedCategory(null)}
            className={`w-full text-left px-3 py-2 rounded-lg text-sm mb-2 transition-colors ${
              selectedCategory === null
                ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
                : "text-gray-400 hover:bg-gray-800 hover:text-white"
            }`}
          >
            All Items
          </button>

          <div className="space-y-1">
            {categoryTree.map((node) => (
              <CategoryNode key={node.id} node={node} />
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white">Items</h1>
            <p className="text-gray-400 mt-1">
              Manage products, components, supplies, and services
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleRecostAll}
              disabled={recosting}
              className="px-4 py-2 bg-gray-800 border border-gray-700 text-gray-300 rounded-lg hover:bg-gray-700 hover:text-white disabled:opacity-50"
            >
              {recosting ? "Recosting..." : "Recost All"}
            </button>
            <button
              onClick={() => {
                setEditingItem(null);
                setShowItemModal(true);
              }}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-500 hover:to-purple-500"
            >
              + Add Item
            </button>
          </div>
        </div>

        {/* Recost Result */}
        {recostResult && (
          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-green-400 font-medium">
                  Recost complete: {recostResult.updated} items updated, {recostResult.skipped} skipped
                </p>
                {recostResult.items?.length > 0 && (
                  <div className="mt-2 text-sm text-gray-400 max-h-32 overflow-auto">
                    {recostResult.items.slice(0, 10).map((item, i) => (
                      <div key={i}>
                        {item.sku}: ${item.old_cost.toFixed(2)} → ${item.new_cost.toFixed(2)} ({item.cost_source})
                      </div>
                    ))}
                    {recostResult.items.length > 10 && (
                      <div className="text-gray-500">...and {recostResult.items.length - 10} more</div>
                    )}
                  </div>
                )}
              </div>
              <button
                onClick={() => setRecostResult(null)}
                className="text-gray-500 hover:text-white"
              >
                x
              </button>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-4 bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by SKU, name, or UPC..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500"
            />
          </div>
          <select
            value={filters.itemType}
            onChange={(e) => setFilters({ ...filters, itemType: e.target.value })}
            className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
          >
            <option value="all">All Types</option>
            {ITEM_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-gray-400">
            <input
              type="checkbox"
              checked={filters.activeOnly}
              onChange={(e) => setFilters({ ...filters, activeOnly: e.target.checked })}
              className="rounded"
            />
            Active only
          </label>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-5 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-400 text-sm">Total Items</p>
            <p className="text-2xl font-bold text-white">{stats.total}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-400 text-sm">Finished Goods</p>
            <p className="text-2xl font-bold text-blue-400">{stats.finishedGoods}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-400 text-sm">Components</p>
            <p className="text-2xl font-bold text-purple-400">{stats.components}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-400 text-sm">Supplies</p>
            <p className="text-2xl font-bold text-orange-400">{stats.supplies}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-400 text-sm">Needs Reorder</p>
            <p className="text-2xl font-bold text-red-400">{stats.needsReorder}</p>
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

        {/* Items Table */}
        {!loading && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-800/50">
                <tr>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    SKU
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    Name
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    Type
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    Category
                  </th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    Std Cost
                  </th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    Price
                  </th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    Suggested
                  </th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    On Hand
                  </th>
                  <th className="text-center py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    Status
                  </th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr
                    key={item.id}
                    className="border-b border-gray-800 hover:bg-gray-800/50"
                  >
                    <td className="py-3 px-4 text-white font-mono text-sm">
                      {item.sku}
                    </td>
                    <td className="py-3 px-4 text-gray-300">{item.name}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-1 rounded-full text-xs ${getItemTypeStyle(
                          item.item_type
                        )}`}
                      >
                        {ITEM_TYPES.find((t) => t.value === item.item_type)?.label ||
                          item.item_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-400">
                      {item.category_name || "-"}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-400">
                      {item.standard_cost
                        ? `$${parseFloat(item.standard_cost).toFixed(2)}`
                        : "-"}
                    </td>
                    <td className="py-3 px-4 text-right text-green-400">
                      {item.selling_price
                        ? `$${parseFloat(item.selling_price).toFixed(2)}`
                        : "-"}
                    </td>
                    <td className="py-3 px-4 text-right text-yellow-400">
                      {item.suggested_price
                        ? `$${parseFloat(item.suggested_price).toFixed(2)}`
                        : "-"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span
                        className={
                          item.needs_reorder ? "text-red-400" : "text-gray-300"
                        }
                      >
                        {item.on_hand_qty != null
                          ? parseFloat(item.on_hand_qty).toFixed(0)
                          : "-"}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`px-2 py-1 rounded-full text-xs ${
                          item.active
                            ? "bg-green-500/20 text-green-400"
                            : "bg-gray-500/20 text-gray-400"
                        }`}
                      >
                        {item.active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => {
                          setEditingItem(item);
                          setShowItemModal(true);
                        }}
                        className="text-blue-400 hover:text-blue-300 text-sm"
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
                {filteredItems.length === 0 && (
                  <tr>
                    <td colSpan={10} className="py-12 text-center text-gray-500">
                      No items found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Item Modal */}
      {showItemModal && (
        <ItemModal
          item={editingItem}
          categories={categories}
          onSave={handleSaveItem}
          onClose={() => {
            setShowItemModal(false);
            setEditingItem(null);
          }}
        />
      )}

      {/* Category Modal */}
      {showCategoryModal && (
        <CategoryModal
          category={editingCategory}
          categories={categories}
          onSave={handleSaveCategory}
          onClose={() => {
            setShowCategoryModal(false);
            setEditingCategory(null);
          }}
        />
      )}
    </div>
  );
}

// Item Create/Edit Modal
function ItemModal({ item, categories, onSave, onClose }) {
  const [form, setForm] = useState({
    sku: item?.sku || "",
    name: item?.name || "",
    description: item?.description || "",
    item_type: item?.item_type || "finished_good",
    category_id: item?.category_id || "",
    unit: item?.unit || "EA",
    cost_method: item?.cost_method || "average",
    standard_cost: item?.standard_cost || "",
    selling_price: item?.selling_price || "",
    reorder_point: item?.reorder_point || "",
    lead_time_days: item?.lead_time_days || "",
    min_order_qty: item?.min_order_qty || "",
    upc: item?.upc || "",
    weight_oz: item?.weight_oz || "",
    active: item?.active ?? true,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = { ...form };
    // Convert empty strings to null for optional numeric fields
    ["standard_cost", "selling_price", "reorder_point", "lead_time_days", "min_order_qty", "weight_oz"].forEach((f) => {
      if (data[f] === "") data[f] = null;
      else if (data[f]) data[f] = parseFloat(data[f]);
    });
    if (data.category_id === "") data.category_id = null;
    else if (data.category_id) data.category_id = parseInt(data.category_id);
    onSave(data);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-auto">
        <div className="p-6 border-b border-gray-800">
          <h2 className="text-xl font-bold text-white">
            {item ? "Edit Item" : "Add New Item"}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">SKU *</label>
              <input
                type="text"
                value={form.sku}
                onChange={(e) => setForm({ ...form, sku: e.target.value.toUpperCase() })}
                required
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={2}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
            />
          </div>

          {/* Classification */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Item Type</label>
              <select
                value={form.item_type}
                onChange={(e) => setForm({ ...form, item_type: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              >
                {ITEM_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Category</label>
              <select
                value={form.category_id}
                onChange={(e) => setForm({ ...form, category_id: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              >
                <option value="">-- None --</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.full_path || c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Unit</label>
              <input
                type="text"
                value={form.unit}
                onChange={(e) => setForm({ ...form, unit: e.target.value.toUpperCase() })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              />
            </div>
          </div>

          {/* Costing */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Cost Method</label>
              <select
                value={form.cost_method}
                onChange={(e) => setForm({ ...form, cost_method: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              >
                {COST_METHODS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Standard Cost</label>
              <input
                type="number"
                step="0.01"
                value={form.standard_cost}
                onChange={(e) => setForm({ ...form, standard_cost: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Selling Price</label>
              <input
                type="number"
                step="0.01"
                value={form.selling_price}
                onChange={(e) => setForm({ ...form, selling_price: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              />
            </div>
          </div>

          {/* Purchasing */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Lead Time (days)</label>
              <input
                type="number"
                value={form.lead_time_days}
                onChange={(e) => setForm({ ...form, lead_time_days: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Min Order Qty</label>
              <input
                type="number"
                step="0.01"
                value={form.min_order_qty}
                onChange={(e) => setForm({ ...form, min_order_qty: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Reorder Point</label>
              <input
                type="number"
                step="0.01"
                value={form.reorder_point}
                onChange={(e) => setForm({ ...form, reorder_point: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              />
            </div>
          </div>

          {/* Additional */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">UPC/Barcode</label>
              <input
                type="text"
                value={form.upc}
                onChange={(e) => setForm({ ...form, upc: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Weight (oz)</label>
              <input
                type="number"
                step="0.01"
                value={form.weight_oz}
                onChange={(e) => setForm({ ...form, weight_oz: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="active"
              checked={form.active}
              onChange={(e) => setForm({ ...form, active: e.target.checked })}
              className="rounded"
            />
            <label htmlFor="active" className="text-gray-400">
              Active
            </label>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-4 pt-4 border-t border-gray-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-500 hover:to-purple-500"
            >
              {item ? "Save Changes" : "Create Item"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Category Create/Edit Modal
function CategoryModal({ category, categories, onSave, onClose }) {
  const [form, setForm] = useState({
    code: category?.code || "",
    name: category?.name || "",
    parent_id: category?.parent_id || "",
    description: category?.description || "",
    sort_order: category?.sort_order || 0,
    is_active: category?.is_active ?? true,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = { ...form };
    if (data.parent_id === "") data.parent_id = null;
    else if (data.parent_id) data.parent_id = parseInt(data.parent_id);
    data.sort_order = parseInt(data.sort_order) || 0;
    onSave(data);
  };

  // Filter out current category and its children for parent selection
  const availableParents = categories.filter((c) => c.id !== category?.id);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-md">
        <div className="p-6 border-b border-gray-800">
          <h2 className="text-xl font-bold text-white">
            {category ? "Edit Category" : "Add New Category"}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Code *</label>
            <input
              type="text"
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
              required
              placeholder="e.g. FILAMENT"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Name *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Parent Category</label>
            <select
              value={form.parent_id}
              onChange={(e) => setForm({ ...form, parent_id: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
            >
              <option value="">-- Root Level --</option>
              {availableParents.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_path || c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={2}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Sort Order</label>
              <input
                type="number"
                value={form.sort_order}
                onChange={(e) => setForm({ ...form, sort_order: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              />
            </div>
            <div className="flex items-center pt-6">
              <input
                type="checkbox"
                id="cat_active"
                checked={form.is_active}
                onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                className="rounded"
              />
              <label htmlFor="cat_active" className="text-gray-400 ml-2">
                Active
              </label>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-4 pt-4 border-t border-gray-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-500 hover:to-purple-500"
            >
              {category ? "Save Changes" : "Create Category"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
