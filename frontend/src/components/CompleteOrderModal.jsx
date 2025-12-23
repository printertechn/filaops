import { useState, useEffect } from "react";
import { API_URL } from "../config/api";
import { useToast } from "./Toast";

export default function CompleteOrderModal({
  productionOrder,
  onClose,
  onComplete,
}) {
  const toast = useToast();
  const [quantityCompleted, setQuantityCompleted] = useState(
    productionOrder.quantity_ordered || 1
  );
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [bomMaterials, setBomMaterials] = useState([]);
  const [selectedSpools, setSelectedSpools] = useState({}); // { materialProductId: spoolId }
  const [availableSpoolsByMaterial, setAvailableSpoolsByMaterial] = useState({}); // { materialProductId: [spools] }
  const [loadingMaterials, setLoadingMaterials] = useState(false);

  const token = localStorage.getItem("adminToken");

  const quantityOrdered = productionOrder.quantity_ordered || 1;
  const isOverrun = quantityCompleted > quantityOrdered;

  // Fetch BOM materials on mount
  useEffect(() => {
    fetchBomMaterials();
  }, [productionOrder.id]);

  const fetchBomMaterials = async () => {
    if (!token || !productionOrder.product_id) return;
    
    setLoadingMaterials(true);
    try {
      // Get BOM for the product
      const bomRes = await fetch(
        `${API_URL}/api/v1/admin/bom/product/${productionOrder.product_id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (bomRes.ok) {
        const bom = await bomRes.json();
        if (bom && bom.lines) {
          // Filter for filament/supply materials (production stage)
          const materials = bom.lines
            .filter((line) => line.consume_stage === "production" && !line.is_cost_only)
            .map((line) => ({
              component_id: line.component_id,
              component_sku: line.component_sku,
              component_name: line.component_name,
              quantity: parseFloat(line.quantity || 0),
              unit: line.unit || "EA",
            }));
          
          setBomMaterials(materials);
          
          // Fetch available spools for each material
          const spoolsMap = {};
          for (const material of materials) {
            try {
              const spoolsRes = await fetch(
                `${API_URL}/api/v1/spools/product/${material.component_id}/available`,
                { headers: { Authorization: `Bearer ${token}` } }
              );
              if (spoolsRes.ok) {
                const spoolsData = await spoolsRes.json();
                spoolsMap[material.component_id] = spoolsData.spools || [];
                // Auto-select first available spool if only one
                if (spoolsData.spools && spoolsData.spools.length === 1) {
                  setSelectedSpools((prev) => ({
                    ...prev,
                    [material.component_id]: spoolsData.spools[0].id,
                  }));
                }
              } else {
                spoolsMap[material.component_id] = [];
              }
            } catch (err) {
              // Non-critical - spool selection is optional
              spoolsMap[material.component_id] = [];
            }
          }
          setAvailableSpoolsByMaterial(spoolsMap);
        }
      }
    } catch (err) {
      // Non-critical - spool tracking is optional
    } finally {
      setLoadingMaterials(false);
    }
  };

  const handleSubmit = async () => {
    if (quantityCompleted < 1) {
      toast.error("Quantity must be at least 1");
      return;
    }

    setSubmitting(true);
    try {
      const params = new URLSearchParams({
        quantity_completed: quantityCompleted.toString(),
      });

      // Prepare request body with optional notes and spool selections
      const requestBody = {};
      if (notes.trim()) {
        requestBody.notes = notes.trim();
      }
      if (Object.keys(selectedSpools).length > 0) {
        requestBody.spools_used = Object.entries(selectedSpools).map(([productId, spoolId]) => ({
          product_id: parseInt(productId),
          spool_id: spoolId,
        }));
      }

      const res = await fetch(
        `${API_URL}/api/v1/production-orders/${productionOrder.id}/complete?${params}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
        }
      );

      if (res.ok) {
        if (isOverrun) {
          toast.success(
            `Order completed with ${
              quantityCompleted - quantityOrdered
            } extra units (MTS overrun)`
          );
        } else {
          toast.success("Production order completed");
        }
        onComplete();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to complete order");
      }
    } catch (err) {
      toast.error(err.message || "Network error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-bold text-white">
              Complete Production Order
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              {productionOrder.code} -{" "}
              {productionOrder.product_name || productionOrder.product_sku}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl"
          >
            &times;
          </button>
        </div>

        {/* Order Details */}
        <div className="bg-gray-800/50 rounded-lg p-4 mb-6">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-400">Quantity Ordered:</span>
            <span className="text-white font-medium">
              {quantityOrdered} units
            </span>
          </div>
          {productionOrder.scheduled_start && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Scheduled:</span>
              <span className="text-white">
                {new Date(productionOrder.scheduled_start).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>

        {/* Quantity Completed */}
        <div className="mb-4">
          <label className="block text-sm text-gray-400 mb-2">
            Quantity Completed *
          </label>
          <input
            type="number"
            value={quantityCompleted}
            onChange={(e) =>
              setQuantityCompleted(parseInt(e.target.value) || 0)
            }
            min="1"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white text-lg"
          />
          <p className="text-gray-500 text-sm mt-1">
            Enter actual quantity produced (can exceed ordered qty for MTS
            overruns)
          </p>
        </div>

        {/* Spool Selection */}
        {bomMaterials.length > 0 && (
          <div className="mb-4">
            <label className="block text-sm text-gray-400 mb-2">
              Material Spools Used (Optional)
            </label>
            <div className="space-y-3 bg-gray-800/50 rounded-lg p-3">
              {loadingMaterials ? (
                <div className="text-gray-500 text-sm">Loading materials...</div>
              ) : (
                bomMaterials.map((material) => {
                  const availableSpools = availableSpoolsByMaterial[material.component_id] || [];
                  const requiredWeight = material.quantity * quantityCompleted;
                  
                  return (
                    <div key={material.component_id} className="border-b border-gray-700 pb-3 last:border-0 last:pb-0">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="text-white text-sm font-medium">
                            {material.component_name || material.component_sku}
                          </div>
                          <div className="text-gray-500 text-xs">
                            Required: {requiredWeight.toFixed(3)} {material.unit}
                          </div>
                        </div>
                      </div>
                      {availableSpools.length > 0 ? (
                        <select
                          value={selectedSpools[material.component_id] || ""}
                          onChange={(e) => {
                            setSelectedSpools((prev) => ({
                              ...prev,
                              [material.component_id]: e.target.value ? parseInt(e.target.value) : null,
                            }));
                          }}
                          className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
                        >
                          <option value="">No spool selected</option>
                          {availableSpools.map((spool) => (
                            <option key={spool.id} value={spool.id}>
                              {spool.spool_number} - {spool.current_weight_kg.toFixed(3)}kg remaining ({spool.weight_remaining_percent.toFixed(1)}%)
                            </option>
                          ))}
                        </select>
                      ) : (
                        <div className="text-gray-500 text-xs">No active spools available</div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
            <p className="text-gray-500 text-xs mt-2">
              Select spools to track material consumption and weight remaining
            </p>
          </div>
        )}

        {/* Notes */}
        <div className="mb-4">
          <label className="block text-sm text-gray-400 mb-2">
            Completion Notes (Optional)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add any notes about the completion (e.g., quality issues, early completion, etc.)"
            rows={3}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white resize-none"
          />
        </div>

        {/* Overrun Info Banner */}
        {isOverrun && (
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mb-6">
            <div className="flex gap-3">
              <svg
                className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>
                <p className="text-blue-400 font-medium">MTS Overrun</p>
                <p className="text-blue-400/80 text-sm">
                  {quantityCompleted - quantityOrdered} extra unit
                  {quantityCompleted - quantityOrdered > 1 ? "s" : ""} will be
                  added to inventory as Make-to-Stock.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Under completion warning */}
        {quantityCompleted < quantityOrdered && quantityCompleted > 0 && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-6">
            <div className="flex gap-3">
              <svg
                className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <div>
                <p className="text-yellow-400 font-medium">
                  Partial Completion
                </p>
                <p className="text-yellow-400/80 text-sm">
                  Only {quantityCompleted} of {quantityOrdered} ordered will be
                  completed. Consider scrapping if the remainder failed.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={quantityCompleted < 1 || submitting}
            className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? "Processing..." : "Complete Order"}
          </button>
        </div>
      </div>
    </div>
  );
}
