import { useState, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function AdminProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    search: "",
    category: "all",
    type: "all",
  });

  const token = localStorage.getItem("adminToken");

  useEffect(() => {
    fetchProducts();
  }, [filters.category, filters.type]);

  const fetchProducts = async () => {
    if (!token) return;

    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", "200");
      if (filters.category !== "all") params.set("category", filters.category);

      const res = await fetch(`${API_URL}/api/v1/products?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) throw new Error("Failed to fetch products");

      const data = await res.json();
      setProducts(data.items || data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter((p) => {
    if (!filters.search) return true;
    const search = filters.search.toLowerCase();
    return (
      p.sku?.toLowerCase().includes(search) ||
      p.name?.toLowerCase().includes(search) ||
      p.category?.toLowerCase().includes(search)
    );
  }).filter((p) => {
    if (filters.type === "all") return true;
    if (filters.type === "materials") return p.is_raw_material;
    if (filters.type === "products") return !p.is_raw_material;
    return true;
  });

  const categories = [...new Set(products.map((p) => p.category).filter(Boolean))];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">Products</h1>
          <p className="text-gray-400 mt-1">Manage products and raw materials</p>
        </div>
        <button
          className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-500 hover:to-purple-500"
        >
          + Add Product
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 bg-gray-900 border border-gray-800 rounded-xl p-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search by SKU, name, or category..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500"
          />
        </div>
        <select
          value={filters.type}
          onChange={(e) => setFilters({ ...filters, type: e.target.value })}
          className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
        >
          <option value="all">All Types</option>
          <option value="products">Products Only</option>
          <option value="materials">Raw Materials</option>
        </select>
        <select
          value={filters.category}
          onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
        >
          <option value="all">All Categories</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total Products</p>
          <p className="text-2xl font-bold text-white">{products.filter(p => !p.is_raw_material).length}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Raw Materials</p>
          <p className="text-2xl font-bold text-white">{products.filter(p => p.is_raw_material).length}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Active</p>
          <p className="text-2xl font-bold text-green-400">{products.filter(p => p.active).length}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Inactive</p>
          <p className="text-2xl font-bold text-gray-400">{products.filter(p => !p.active).length}</p>
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

      {/* Products Table */}
      {!loading && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-800/50">
              <tr>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">SKU</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Name</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Category</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Type</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Unit</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Cost</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Price</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">Status</th>
                <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredProducts.map((product) => (
                <tr key={product.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                  <td className="py-3 px-4 text-white font-mono text-sm">{product.sku}</td>
                  <td className="py-3 px-4 text-gray-300">{product.name}</td>
                  <td className="py-3 px-4 text-gray-400">{product.category}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      product.is_raw_material
                        ? "bg-orange-500/20 text-orange-400"
                        : "bg-blue-500/20 text-blue-400"
                    }`}>
                      {product.is_raw_material ? "Material" : "Product"}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-400">{product.unit}</td>
                  <td className="py-3 px-4 text-gray-400">${parseFloat(product.cost || 0).toFixed(2)}</td>
                  <td className="py-3 px-4 text-green-400">${parseFloat(product.selling_price || 0).toFixed(2)}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      product.active
                        ? "bg-green-500/20 text-green-400"
                        : "bg-gray-500/20 text-gray-400"
                    }`}>
                      {product.active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button className="text-blue-400 hover:text-blue-300 text-sm">
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
              {filteredProducts.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-gray-500">
                    No products found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
