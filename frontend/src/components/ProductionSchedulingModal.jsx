import { useState, useEffect } from "react";
import { API_URL } from "../config/api";

/**
 * Production Scheduling Modal
 *
 * Allows scheduling a production order to a specific machine/printer
 * with start and end times.
 */
export default function ProductionSchedulingModal({
  productionOrder,
  onClose,
  onSchedule,
}) {
  const [workCenters, setWorkCenters] = useState([]);
  const [resources, setResources] = useState([]);
  const [selectedWorkCenter, setSelectedWorkCenter] = useState(null);
  const [selectedResource, setSelectedResource] = useState(null);
  const [scheduledStart, setScheduledStart] = useState("");
  const [scheduledEnd, setScheduledEnd] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const token = localStorage.getItem("adminToken");

  useEffect(() => {
    fetchWorkCenters();
  }, []);

  useEffect(() => {
    if (selectedWorkCenter) {
      fetchResources(selectedWorkCenter);
    } else {
      setResources([]);
    }
  }, [selectedWorkCenter]);

  // Set default scheduled start to now + 1 hour
  useEffect(() => {
    if (!scheduledStart && productionOrder) {
      const now = new Date();
      now.setHours(now.getHours() + 1);
      setScheduledStart(now.toISOString().slice(0, 16));
    }
  }, [productionOrder, scheduledStart]);

  const fetchWorkCenters = async () => {
    try {
      const res = await fetch(
        `${API_URL}/api/v1/work-centers/?center_type=machine&active_only=true`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (res.ok) {
        const data = await res.json();
        setWorkCenters(data);
      }
    } catch {
      // Work centers fetch failure is non-critical - work center selector will be empty
    }
  };

  const fetchResources = async (workCenterId) => {
    try {
      const res = await fetch(
        `${API_URL}/api/v1/work-centers/${workCenterId}/resources?active_only=true`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (res.ok) {
        const data = await res.json();
        // Filter to only available resources
        const available = data.filter(
          (r) => r.status === "available" || r.status === "idle"
        );
        setResources(available);
      }
    } catch {
      // Resources fetch failure is non-critical - resource selector will be empty
    }
  };

  const calculateEndTime = (startTime, estimatedHours = 2) => {
    if (!startTime) return "";
    const start = new Date(startTime);
    start.setHours(start.getHours() + estimatedHours);
    return start.toISOString().slice(0, 16);
  };

  const handleScheduledStartChange = (e) => {
    const newStart = e.target.value;
    setScheduledStart(newStart);
    // Auto-calculate end time (default 2 hours, or use estimated time from order)
    const estimatedHours = productionOrder?.estimated_time_minutes
      ? productionOrder.estimated_time_minutes / 60
      : 2;
    setScheduledEnd(calculateEndTime(newStart, estimatedHours));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Update the production order with scheduling info
      const scheduleData = {
        scheduled_start: scheduledStart
          ? new Date(scheduledStart).toISOString()
          : null,
        scheduled_end: scheduledEnd
          ? new Date(scheduledEnd).toISOString()
          : null,
      };

      const updateRes = await fetch(
        `${API_URL}/api/v1/production-orders/${productionOrder.id}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(scheduleData),
        }
      );

      if (!updateRes.ok) {
        const err = await updateRes.json();
        throw new Error(err.detail || "Failed to schedule production order");
      }

      // If a resource is selected and we want to start immediately, start production with printer assignment
      // Otherwise, just schedule it (don't start yet)
      if (selectedResource) {
        const startRes = await fetch(
          `${API_URL}/api/v1/admin/fulfillment/queue/${productionOrder.id}/start`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              printer_id: selectedResource.code, // Use resource code
              notes: notes || `Scheduled to ${selectedResource.name}`,
            }),
          }
        );

        if (!startRes.ok) {
          const err = await startRes.json();
          throw new Error(err.detail || "Failed to start production");
        }
      }

      onSchedule();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!productionOrder) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-bold text-white">
              Schedule Production
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              {productionOrder.code} - {productionOrder.product?.name || "N/A"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ×
          </button>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Work Center Selection */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Work Center (Machine Pool)
            </label>
            <select
              value={selectedWorkCenter || ""}
              onChange={(e) =>
                setSelectedWorkCenter(
                  e.target.value ? parseInt(e.target.value) : null
                )
              }
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
            >
              <option value="">Select work center...</option>
              {workCenters.map((wc) => (
                <option key={wc.id} value={wc.id}>
                  {wc.code} - {wc.name} ({wc.resource_count} machines)
                </option>
              ))}
            </select>
          </div>

          {/* Resource/Printer Selection */}
          {selectedWorkCenter && (
            <div>
              <label className="block text-sm text-gray-400 mb-1">
                Select Machine/Printer
              </label>
              {resources.length === 0 ? (
                <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3 text-yellow-400 text-sm">
                  No available machines in this work center. Add resources in
                  Manufacturing → Work Centers.
                </div>
              ) : (
                <select
                  value={selectedResource?.id || ""}
                  onChange={(e) => {
                    const resource = resources.find(
                      (r) => r.id === parseInt(e.target.value)
                    );
                    setSelectedResource(resource || null);
                  }}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                >
                  <option value="">
                    Select machine (optional - can schedule without assignment)
                  </option>
                  {resources.map((resource) => (
                    <option key={resource.id} value={resource.id}>
                      {resource.code} - {resource.name} ({resource.status})
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          {/* Scheduled Start Time */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Scheduled Start Time
            </label>
            <input
              type="datetime-local"
              value={scheduledStart}
              onChange={handleScheduledStartChange}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
            />
            <p className="text-xs text-gray-500 mt-1">
              When production should begin
            </p>
          </div>

          {/* Scheduled End Time */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Scheduled End Time
            </label>
            <input
              type="datetime-local"
              value={scheduledEnd}
              onChange={(e) => setScheduledEnd(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
            />
            <p className="text-xs text-gray-500 mt-1">
              Estimated completion time
            </p>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Notes (optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
              placeholder="Add any scheduling notes..."
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !scheduledStart}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading
                ? "Scheduling..."
                : selectedResource
                ? "Schedule & Start Now"
                : "Schedule"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
