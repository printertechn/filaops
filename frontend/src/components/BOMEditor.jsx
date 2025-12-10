/**
 * BOMEditor - Standalone BOM editor component
 *
 * Simple, focused editor for managing Bill of Materials.
 * Can be used from item detail pages or standalone.
 */
import { useState, useEffect } from "react";
import { API_URL } from "../config/api";

export default function BOMEditor({
  isOpen,
  onClose,
  productId,
  bomId = null, // If editing existing BOM
  onSuccess,
}) {
  const token = localStorage.getItem("adminToken");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [bom, setBom] = useState(null);
  const [lines, setLines] = useState([]);
  const [components, setComponents] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [showAddLine, setShowAddLine] = useState(false);
  const [editingLine, setEditingLine] = useState(null);

  const [newLine, setNewLine] = useState({
    component_id: "",
    quantity: 1,
    unit: "EA",
    sequence: 1,
    scrap_factor: 0,
    is_cost_only: false,
    notes: "",
  });

  useEffect(() => {
    if (isOpen) {
      if (bomId) {
        fetchBOM();
      } else if (productId) {
        fetchBOMByProduct();
      }
      fetchComponents();
      fetchMaterials();
      setError(null);
    }
  }, [isOpen, bomId, productId]);

  const fetchBOM = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/admin/bom/${bomId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setBom(data);
        setLines(data.lines || []);
      }
    } catch (err) {
      // BOM fetch failure - will show empty editor
    }
  };

  const fetchBOMByProduct = async () => {
    try {
      const res = await fetch(
        `${API_URL}/api/v1/admin/bom/product/${productId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (res.ok) {
        const data = await res.json();
        setBom(data);
        setLines(data.lines || []);
      } else if (res.status === 404) {
        // No BOM exists yet, that's okay
        setBom(null);
        setLines([]);
      }
    } catch (err) {
      // BOM fetch failure - will show empty editor
    }
  };

  const fetchComponents = async () => {
    try {
      const res = await fetch(
        `${API_URL}/api/v1/items?limit=500&active_only=true`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (res.ok) {
        const data = await res.json();
        setComponents(data.items || []);
      }
    } catch (err) {
      // Components fetch failure is non-critical - component selector will be empty
    }
  };

  const fetchMaterials = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/materials/for-bom`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMaterials(data.items || []);
      }
    } catch (err) {
      // Materials fetch failure is non-critical - material selector will be empty
    }
  };

  const allComponents = [...components, ...materials];

  const handleCreateBOM = async () => {
    if (!productId) {
      setError("Product ID is required");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/api/v1/admin/bom/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          product_id: productId,
          lines: lines.map((line, idx) => ({
            component_id: line.component_id,
            quantity: line.quantity,
            unit: line.unit || "EA",
            sequence: idx + 1,
            scrap_factor: line.scrap_factor || 0,
            is_cost_only: line.is_cost_only || false,
            notes: line.notes || "",
          })),
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to create BOM");
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

  const handleUpdateBOM = async () => {
    if (!bom) return;

    setLoading(true);
    setError(null);

    try {
      // Update BOM lines
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.id) {
          // Update existing line
          const res = await fetch(
            `${API_URL}/api/v1/admin/bom/${bom.id}/lines/${line.id}`,
            {
              method: "PUT",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({
                quantity: line.quantity,
                unit: line.unit || "EA",
                sequence: i + 1,
                scrap_factor: line.scrap_factor || 0,
                is_cost_only: line.is_cost_only || false,
                notes: line.notes || "",
              }),
            }
          );
          if (!res.ok) throw new Error("Failed to update line");
        } else {
          // Add new line
          const res = await fetch(
            `${API_URL}/api/v1/admin/bom/${bom.id}/lines`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({
                component_id: line.component_id,
                quantity: line.quantity,
                unit: line.unit || "EA",
                sequence: i + 1,
                scrap_factor: line.scrap_factor || 0,
                is_cost_only: line.is_cost_only || false,
                notes: line.notes || "",
              }),
            }
          );
          if (!res.ok) throw new Error("Failed to add line");
        }
      }

      // Recalculate BOM cost
      await fetch(`${API_URL}/api/v1/admin/bom/${bom.id}/recalculate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });

      onSuccess?.();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = () => {
    if (bom) {
      handleUpdateBOM();
    } else {
      handleCreateBOM();
    }
  };

  const addLine = () => {
    if (!newLine.component_id) {
      setError("Please select a component");
      return;
    }
    
    const component = allComponents.find(
      (c) => c.id === parseInt(newLine.component_id)
    );
    if (!component) {
      setError("Component not found. Please refresh and try again.");
      return;
    }

    // Check if component is already in BOM
    const existing = lines.find(l => l.component_id === parseInt(newLine.component_id));
    if (existing) {
      setError("This component is already in the BOM");
      return;
    }

    // Set unit based on component type (materials use "kg", others use their unit or "EA")
    const defaultUnit = component.unit || (component.item_type === "supply" ? "kg" : "EA");

    setLines([
      ...lines,
      {
        ...newLine,
        component_id: parseInt(newLine.component_id),
        component_sku: component.sku,
        component_name: component.name,
        component_unit: defaultUnit,
        component_cost: component.standard_cost || component.average_cost || 0,
        unit: newLine.unit || defaultUnit, // Use selected unit or default
      },
    ]);

    setNewLine({
      component_id: "",
      quantity: 1,
      unit: "EA",
      sequence: lines.length + 2,
      scrap_factor: 0,
      is_cost_only: false,
      notes: "",
    });
    setError(null);
    setShowAddLine(false);
  };

  const removeLine = (index) => {
    setLines(lines.filter((_, i) => i !== index));
  };

  const updateLine = (index, field, value) => {
    const updated = [...lines];
    updated[index] = { ...updated[index], [field]: value };
    setLines(updated);
  };

  if (!isOpen) return null;

  const totalCost = lines.reduce((sum, line) => {
    const qty = line.quantity * (1 + (line.scrap_factor || 0));
    return sum + qty * (line.component_cost || 0);
  }, 0);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">
              {bom ? `Edit BOM: ${bom.code || bom.name}` : "Create BOM"}
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

          {/* BOM Lines */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Components</h3>
              <button
                onClick={() => setShowAddLine(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                + Add Component
              </button>
            </div>

            {lines.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No components added yet. Click "Add Component" to get started.
              </div>
            ) : (
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border p-2 text-left">Seq</th>
                    <th className="border p-2 text-left">Component</th>
                    <th className="border p-2 text-right">Quantity</th>
                    <th className="border p-2 text-left">Unit</th>
                    <th className="border p-2 text-right">Scrap %</th>
                    <th className="border p-2 text-right">Cost</th>
                    <th className="border p-2 text-center">Cost Only</th>
                    <th className="border p-2 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((line, index) => (
                    <tr key={index}>
                      <td className="border p-2">{index + 1}</td>
                      <td className="border p-2">
                        {line.component_sku || line.component?.sku} -{" "}
                        {line.component_name || line.component?.name}
                      </td>
                      <td className="border p-2">
                        <input
                          type="number"
                          step="0.001"
                          min="0"
                          value={line.quantity}
                          onChange={(e) =>
                            updateLine(
                              index,
                              "quantity",
                              parseFloat(e.target.value) || 0
                            )
                          }
                          className="w-20 text-right border rounded px-2 py-1"
                        />
                      </td>
                      <td className="border p-2">
                        <input
                          type="text"
                          value={line.unit || "EA"}
                          onChange={(e) =>
                            updateLine(index, "unit", e.target.value)
                          }
                          className="w-16 border rounded px-2 py-1"
                          placeholder="EA"
                        />
                      </td>
                      <td className="border p-2">
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="100"
                          value={line.scrap_factor || 0}
                          onChange={(e) =>
                            updateLine(
                              index,
                              "scrap_factor",
                              parseFloat(e.target.value) || 0
                            )
                          }
                          className="w-20 text-right border rounded px-2 py-1"
                        />
                      </td>
                      <td className="border p-2 text-right">
                        $
                        {(
                          line.quantity *
                          (1 + (line.scrap_factor || 0)) *
                          (line.component_cost || 0)
                        ).toFixed(2)}
                      </td>
                      <td className="border p-2 text-center">
                        <input
                          type="checkbox"
                          checked={line.is_cost_only || false}
                          onChange={(e) =>
                            updateLine(index, "is_cost_only", e.target.checked)
                          }
                        />
                      </td>
                      <td className="border p-2 text-center">
                        <button
                          onClick={() => removeLine(index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-gray-50 font-semibold">
                    <td colSpan="5" className="border p-2 text-right">
                      Total Material Cost:
                    </td>
                    <td className="border p-2 text-right">
                      ${totalCost.toFixed(2)}
                    </td>
                    <td colSpan="2" className="border"></td>
                  </tr>
                </tfoot>
              </table>
            )}
          </div>

          {/* Add Line Form */}
          {showAddLine && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold mb-3">Add Component</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Component
                  </label>
                  <select
                    value={newLine.component_id}
                    onChange={(e) => {
                      const selectedId = e.target.value;
                      const selected = allComponents.find(c => c.id === parseInt(selectedId));
                      setNewLine({ 
                        ...newLine, 
                        component_id: selectedId,
                        unit: selected?.unit || (selected?.item_type === "supply" ? "kg" : "EA")
                      });
                    }}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="">Select component...</option>
                    <optgroup label="Components & Supplies">
                      {components.filter(c => !lines.find(l => l.component_id === c.id)).map((comp) => (
                        <option key={comp.id} value={comp.id}>
                          {comp.sku} - {comp.name} ({comp.unit || "EA"})
                        </option>
                      ))}
                    </optgroup>
                    {materials.length > 0 && (
                      <optgroup label="Materials (Filament)">
                        {materials.filter(m => !lines.find(l => l.component_id === m.id)).map((mat) => (
                          <option key={mat.id} value={mat.id}>
                            {mat.sku} - {mat.name} ({mat.unit || "kg"})
                          </option>
                        ))}
                      </optgroup>
                    )}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Quantity
                  </label>
                  <input
                    type="number"
                    step="0.001"
                    min="0"
                    value={newLine.quantity}
                    onChange={(e) =>
                      setNewLine({
                        ...newLine,
                        quantity: parseFloat(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Unit</label>
                  <input
                    type="text"
                    value={newLine.unit}
                    onChange={(e) =>
                      setNewLine({ ...newLine, unit: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="EA, kg, HR, etc."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Scrap Factor (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={newLine.scrap_factor}
                    onChange={(e) =>
                      setNewLine({
                        ...newLine,
                        scrap_factor: parseFloat(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
              </div>
              <div className="mt-3 flex items-center">
                <input
                  type="checkbox"
                  id="cost_only"
                  checked={newLine.is_cost_only}
                  onChange={(e) =>
                    setNewLine({ ...newLine, is_cost_only: e.target.checked })
                  }
                  className="mr-2"
                />
                <label htmlFor="cost_only" className="text-sm">
                  Cost only (not consumed)
                </label>
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={addLine}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Add
                </button>
                <button
                  onClick={() => setShowAddLine(false)}
                  className="px-4 py-2 bg-gray-300 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

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
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              disabled={loading || lines.length === 0}
            >
              {loading ? "Saving..." : bom ? "Update BOM" : "Create BOM"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
