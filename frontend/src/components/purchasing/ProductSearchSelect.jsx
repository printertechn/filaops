/**
 * ProductSearchSelect - Reusable product search and selection component
 *
 * Features:
 * - Debounced search (300ms)
 * - Shows SKU, Name, Current Stock, Last Cost
 * - Category filter dropdown
 * - Keyboard navigation support
 */
import { useState, useEffect, useRef, useMemo } from "react";
import { API_URL } from "../../config/api";

export default function ProductSearchSelect({
  value,
  onChange,
  products = [],
  placeholder = "Search or select product...",
  disabled = false,
  className = "",
  onCreateNew = null, // Callback to open create new item modal, receives search text
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const [showOnlyLowStock, setShowOnlyLowStock] = useState(false);
  const containerRef = useRef(null);
  const inputRef = useRef(null);

  // Find selected product for display
  const selectedProduct = products.find(
    (p) => String(p.id) === String(value)
  );

  // Check if product needs reordering
  // Uses server-calculated `needs_reorder` flag which accounts for:
  // - Stocked items: qty <= reorder_point
  // - On-demand items: MRP shows shortage (demand > available)
  const isLowStock = (product) => {
    // Use the server-calculated flag if available
    if (product.needs_reorder !== undefined) {
      return product.needs_reorder;
    }

    // Fallback: only flag stocked items at/below reorder point
    if (product.stocking_policy === "stocked") {
      const qty = parseFloat(product.on_hand_qty || 0);
      const reorderPoint = parseFloat(product.reorder_point || 0);
      return reorderPoint > 0 ? qty <= reorderPoint : qty <= 0;
    }

    return false;
  };

  // Count low stock items for the filter badge
  const lowStockCount = useMemo(() => {
    return products.filter(isLowStock).length;
  }, [products]);

  // Filter and sort products based on search and low stock filter
  // Low stock items appear first, then sorted alphabetically by SKU
  const filteredProducts = useMemo(() => {
    let filtered = products;

    // Apply low stock filter first
    if (showOnlyLowStock) {
      filtered = filtered.filter(isLowStock);
    }

    // Then apply search filter
    if (search.trim()) {
      const searchLower = search.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.sku?.toLowerCase().includes(searchLower) ||
          p.name?.toLowerCase().includes(searchLower)
      );
    }

    // Sort: low stock first, then by SKU
    return [...filtered].sort((a, b) => {
      const aLow = isLowStock(a);
      const bLow = isLowStock(b);
      if (aLow && !bLow) return -1;
      if (!aLow && bLow) return 1;
      return (a.sku || "").localeCompare(b.sku || "");
    });
  }, [search, products, showOnlyLowStock]);


  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearch("");
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!isOpen) {
      if (e.key === "Enter" || e.key === "ArrowDown") {
        e.preventDefault();
        setIsOpen(true);
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setHighlightedIndex((prev) =>
          Math.min(prev + 1, filteredProducts.length - 1)
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setHighlightedIndex((prev) => Math.max(prev - 1, 0));
        break;
      case "Enter":
        e.preventDefault();
        if (filteredProducts[highlightedIndex]) {
          handleSelect(filteredProducts[highlightedIndex]);
        }
        break;
      case "Escape":
        e.preventDefault();
        setIsOpen(false);
        setSearch("");
        break;
    }
  };

  const handleSelect = (product) => {
    onChange(product.id, product);
    setIsOpen(false);
    setSearch("");
  };

  const handleInputChange = (e) => {
    setSearch(e.target.value);
    setHighlightedIndex(0); // Reset to first item when search changes
    if (!isOpen) {
      setIsOpen(true);
    }
  };

  const handleClear = (e) => {
    e.stopPropagation();
    onChange("", null);
    setSearch("");
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div
        className={`flex items-center bg-gray-800 border border-gray-700 rounded-lg overflow-hidden ${
          disabled ? "opacity-50 cursor-not-allowed" : "cursor-text"
        } ${isOpen ? "ring-2 ring-blue-500" : ""}`}
        onClick={() => {
          if (!disabled) {
            setIsOpen(true);
            inputRef.current?.focus();
          }
        }}
      >
        <input
          ref={inputRef}
          type="text"
          value={isOpen ? search : selectedProduct ? `${selectedProduct.sku} - ${selectedProduct.name}` : ""}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          disabled={disabled}
          className="flex-1 bg-transparent px-3 py-2 text-white placeholder-gray-500 outline-none text-sm"
        />
        {value && !isOpen && (
          <button
            type="button"
            onClick={handleClear}
            className="px-2 text-gray-400 hover:text-white"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
        <div className="px-2 text-gray-400">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full min-w-[400px] bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-72 overflow-hidden flex flex-col">
          {/* Filter toggle */}
          {lowStockCount > 0 && (
            <div className="px-3 py-2 border-b border-gray-700 flex-shrink-0">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowOnlyLowStock(!showOnlyLowStock);
                  setHighlightedIndex(0);
                }}
                className={`text-xs px-2 py-1 rounded-full transition-colors ${
                  showOnlyLowStock
                    ? "bg-red-600 text-white"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}
              >
                {showOnlyLowStock ? (
                  <>
                    <span className="inline-block w-2 h-2 rounded-full bg-white mr-1" />
                    Shortages Only ({lowStockCount})
                  </>
                ) : (
                  <>
                    <span className="inline-block w-2 h-2 rounded-full bg-red-500 mr-1" />
                    Show Shortages ({lowStockCount})
                  </>
                )}
              </button>
            </div>
          )}

          {/* Product list */}
          <div className="overflow-auto flex-1">
          {filteredProducts.length === 0 ? (
            <div className="px-3 py-4 text-center text-gray-400 text-sm">
              {search ? (
                <div>
                  <p className="mb-2">No products found for "{search}"</p>
                  {onCreateNew && (
                    <button
                      type="button"
                      onClick={() => {
                        onCreateNew(search);
                        setIsOpen(false);
                      }}
                      className="text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 mx-auto"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      Create New Item
                    </button>
                  )}
                </div>
              ) : (
                "No products available"
              )}
            </div>
          ) : (
            <>
              {filteredProducts.map((product, index) => {
                const lowStock = isLowStock(product);
                return (
                  <div
                    key={product.id}
                    onClick={() => handleSelect(product)}
                    onMouseEnter={() => setHighlightedIndex(index)}
                    className={`px-3 py-2 cursor-pointer transition-colors ${
                      index === highlightedIndex
                        ? "bg-blue-600/30"
                        : lowStock
                          ? "bg-red-600/10 hover:bg-red-600/20"
                          : "hover:bg-gray-700/50"
                    } ${String(product.id) === String(value) ? "bg-blue-600/20" : ""}`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex items-start gap-2">
                        {lowStock && (
                          <span className="flex-shrink-0 mt-0.5 w-2 h-2 rounded-full bg-red-500" title="Low Stock" />
                        )}
                        <div>
                          <div className="text-white text-sm font-medium">
                            {product.sku}
                          </div>
                          <div className="text-gray-400 text-xs truncate">
                            {product.name}
                          </div>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <div className={`text-xs ${lowStock ? "text-red-400 font-medium" : "text-gray-400"}`}>
                          Stock: {parseFloat(product.on_hand_qty || 0).toFixed(0)}
                          {/* Reorder point indicator for stocked items */}
                          {lowStock && product.shortage_source === "reorder_point" && product.reorder_point > 0 && (
                            <span> / {parseFloat(product.reorder_point).toFixed(0)}</span>
                          )}
                          {/* MRP shortage indicator */}
                          {lowStock && (product.shortage_source === "mrp" || product.shortage_source === "both") && (
                            <span className="ml-1 text-yellow-400" title="MRP shortage from production demand">
                              (MRP{product.mrp_shortage ? `: -${parseFloat(product.mrp_shortage).toFixed(0)}` : ""})
                            </span>
                          )}
                          {/* Both indicators - show reorder point too */}
                          {lowStock && product.shortage_source === "both" && product.reorder_point > 0 && (
                            <span className="text-gray-500"> /{parseFloat(product.reorder_point).toFixed(0)}</span>
                          )}
                        </div>
                        {product.last_cost && (
                          <div className="text-xs text-gray-500">
                            ${parseFloat(product.last_cost).toFixed(2)}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
              {/* Create New option at bottom when searching */}
              {onCreateNew && search && (
                <div
                  onClick={() => {
                    onCreateNew(search);
                    setIsOpen(false);
                  }}
                  className="px-3 py-2 cursor-pointer transition-colors border-t border-gray-700 hover:bg-green-600/20 text-green-400"
                >
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    <span className="text-sm font-medium">Create New Item</span>
                    <span className="text-xs text-gray-400">"{search}"</span>
                  </div>
                </div>
              )}
            </>
          )}
          </div>
        </div>
      )}
    </div>
  );
}
