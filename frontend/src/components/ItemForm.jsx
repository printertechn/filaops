/**
 * ItemForm - Simple single-screen form for creating/editing items
 * 
 * Replaces the complex ItemWizard with a clean, focused form.
 * BOM and Routing are managed separately via dedicated editors.
 */
import { useState, useEffect } from "react";
import { API_URL } from "../config/api";

const ITEM_TYPES = [
  { value: "finished_good", label: "Finished Good" },
  { value: "component", label: "Component" },
  { value: "supply", label: "Supply" },
  { value: "service", label: "Service" },
];

const PROCUREMENT_TYPES = [
  { value: "make", label: "Make (Manufactured)" },
  { value: "buy", label: "Buy (Purchased)" },
  { value: "make_or_buy", label: "Make or Buy" },
];

export default function ItemForm({ 
  isOpen, 
  onClose, 
  onSuccess, 
  editingItem = null 
}) {
  const token = localStorage.getItem("adminToken");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [categories, setCategories] = useState([]);

  const [formData, setFormData] = useState({
    sku: editingItem?.sku || "",
    name: editingItem?.name || "",
    description: editingItem?.description || "",
    item_type: editingItem?.item_type || "finished_good",
    procurement_type: editingItem?.procurement_type || "make",
    category_id: editingItem?.category_id || null,
    unit: editingItem?.unit || "EA",
    standard_cost: editingItem?.standard_cost || "",
    selling_price: editingItem?.selling_price || "",
  });

  useEffect(() => {
    if (isOpen) {
      fetchCategories();
      if (editingItem) {
        setFormData({
          sku: editingItem.sku || "",
          name: editingItem.name || "",
          description: editingItem.description || "",
          item_type: editingItem.item_type || "finished_good",
          procurement_type: editingItem.procurement_type || "make",
          category_id: editingItem.category_id || null,
          unit: editingItem.unit || "EA",
          standard_cost: editingItem.standard_cost || "",
          selling_price: editingItem.selling_price || "",
        });
      } else {
        // Reset form for new item
        setFormData({
          sku: "",
          name: "",
          description: "",
          item_type: "finished_good",
          procurement_type: "make",
          category_id: null,
          unit: "EA",
          standard_cost: "",
          selling_price: "",
        });
      }
      setError(null);
    }
  }, [isOpen, editingItem]);

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/items/categories`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data);
      }
    } catch (err) {
      // Categories fetch failure is non-critical - user can still create items
      // Error is silently handled to avoid blocking the form
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // For PATCH, only send fields that are being updated
      const payload = {
        sku: formData.sku,
        name: formData.name,
        description: formData.description || null,
        item_type: formData.item_type,
        procurement_type: formData.procurement_type,
        unit: formData.unit,
        standard_cost: formData.standard_cost ? parseFloat(formData.standard_cost) : null,
        selling_price: formData.selling_price ? parseFloat(formData.selling_price) : null,
        category_id: formData.category_id || null,
      };

      const url = editingItem
        ? `${API_URL}/api/v1/items/${editingItem.id}`
        : `${API_URL}/api/v1/items`;
      
      const method = editingItem ? "PATCH" : "POST";

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to save item");
      }

      const data = await res.json();
      onSuccess?.(data);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">
              {editingItem ? "Edit Item" : "Create New Item"}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  SKU <span className="text-gray-400 text-xs">(auto-generated if empty)</span>
                </label>
                <input
                  type="text"
                  value={formData.sku}
                  onChange={(e) => setFormData({ ...formData, sku: e.target.value.toUpperCase() })}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Leave empty for auto-generation"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Unit <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.unit}
                  onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="EA, kg, HR, etc."
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="Item name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                rows="3"
                placeholder="Item description"
              />
            </div>

            {/* Classification */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Item Type <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={formData.item_type}
                  onChange={(e) => setFormData({ ...formData, item_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  {ITEM_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Procurement Type <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={formData.procurement_type}
                  onChange={(e) => setFormData({ ...formData, procurement_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  {PROCUREMENT_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Category
              </label>
              <select
                value={formData.category_id || ""}
                onChange={(e) => setFormData({ ...formData, category_id: e.target.value ? parseInt(e.target.value) : null })}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="">No category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Pricing */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Standard Cost
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.standard_cost}
                  onChange={(e) => setFormData({ ...formData, standard_cost: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Selling Price
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.selling_price}
                  onChange={(e) => setFormData({ ...formData, selling_price: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="0.00"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border rounded-md hover:bg-gray-50"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                disabled={loading}
              >
                {loading ? "Saving..." : editingItem ? "Update Item" : "Create Item"}
              </button>
            </div>
          </form>

          {formData.procurement_type === "make" && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-800">
              <strong>Note:</strong> This item requires a BOM and Routing. 
              Create the item first, then add BOM and Routing from the item detail page.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

