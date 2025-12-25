import { useState, useEffect, useCallback } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  useDraggable,
  useDroppable,
} from "@dnd-kit/core";
import { API_URL } from "../config/api";

/**
 * Production Scheduler - Simple Gantt-style drag-and-drop scheduling
 *
 * - Machines/resources on Y-axis
 * - Time slots on X-axis
 * - Drag orders from sidebar onto grid to schedule
 */

// Droppable cell component
function DroppableCell({ id, children, isHovered }) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <td
      ref={setNodeRef}
      className={`border-r border-gray-800 px-1 py-2 min-w-[80px] h-16 align-top ${
        isOver || isHovered ? "bg-blue-900/40" : "bg-gray-900 hover:bg-gray-800/30"
      }`}
    >
      {children}
    </td>
  );
}

// Draggable order card for sidebar
function DraggableOrder({ order }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `order-${order.id}`,
    data: { order },
  });

  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className={`bg-gray-800 border border-gray-700 rounded-lg p-3 cursor-grab hover:border-blue-500 transition-colors ${
        isDragging ? "opacity-50" : ""
      }`}
    >
      <div className="font-medium text-white text-sm">{order.code}</div>
      <div className="text-xs text-gray-400 mt-1">{order.product_name || "N/A"}</div>
      <div className="text-xs text-gray-500 mt-1">Qty: {order.quantity_ordered}</div>
    </div>
  );
}

export default function ProductionScheduler({ onScheduleUpdate }) {
  const [machines, setMachines] = useState([]);
  const [scheduledOrders, setScheduledOrders] = useState([]);
  const [unscheduledOrders, setUnscheduledOrders] = useState([]);
  const [viewMode, setViewMode] = useState("day");
  const [selectedDate, setSelectedDate] = useState(() => {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d;
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [draggedOrder, setDraggedOrder] = useState(null);

  const token = localStorage.getItem("adminToken");

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  );

  // Fetch machines/resources
  const fetchMachines = useCallback(async () => {
    try {
      const wcRes = await fetch(`${API_URL}/api/v1/work-centers/?active_only=true`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!wcRes.ok) throw new Error("Failed to fetch work centers");
      const workCenters = await wcRes.json();

      // Filter to machine-type work centers
      const machineWCs = workCenters.filter(
        (wc) => wc.center_type === "machine" || wc.resource_count > 0
      );

      // Fetch resources for each
      const allResources = [];
      for (const wc of machineWCs) {
        try {
          const res = await fetch(
            `${API_URL}/api/v1/work-centers/${wc.id}/resources?active_only=true`,
            { headers: { Authorization: `Bearer ${token}` } }
          );
          if (res.ok) {
            const resources = await res.json();
            allResources.push(...resources.map((r) => ({ ...r, work_center: wc })));
          }
        } catch {
          // Skip failed fetches
        }
      }
      setMachines(allResources);
    } catch (err) {
      setError(err.message);
    }
  }, [token]);

  // Fetch production orders
  const fetchOrders = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch released and in_progress orders
      const res = await fetch(
        `${API_URL}/api/v1/production-orders/?limit=200`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error("Failed to fetch orders");

      const data = await res.json();
      const orders = Array.isArray(data) ? data : data.items || [];

      // Filter to schedulable statuses
      const schedulable = orders.filter(
        (o) => o.status === "released" || o.status === "in_progress"
      );

      // Separate scheduled vs unscheduled
      const scheduled = schedulable.filter((o) => o.scheduled_start && o.scheduled_end);
      const unscheduled = schedulable.filter((o) => !o.scheduled_start || !o.scheduled_end);

      setScheduledOrders(scheduled);
      setUnscheduledOrders(unscheduled);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchMachines();
    fetchOrders();
  }, [fetchMachines, fetchOrders]);

  // Generate time slots based on view mode
  const getTimeSlots = useCallback(() => {
    const slots = [];
    const start = new Date(selectedDate);
    start.setHours(0, 0, 0, 0);

    if (viewMode === "day") {
      // Show 12 2-hour slots
      for (let i = 0; i < 12; i++) {
        const time = new Date(start);
        time.setHours(i * 2);
        slots.push({ time, label: time.toLocaleTimeString("en-US", { hour: "numeric" }) });
      }
    } else if (viewMode === "week") {
      // Show 7 days
      for (let i = 0; i < 7; i++) {
        const time = new Date(start);
        time.setDate(time.getDate() + i);
        slots.push({
          time,
          label: time.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" }),
        });
      }
    } else {
      // Month: show ~30 days
      for (let i = 0; i < 30; i++) {
        const time = new Date(start);
        time.setDate(time.getDate() + i);
        slots.push({
          time,
          label: time.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        });
      }
    }
    return slots;
  }, [selectedDate, viewMode]);

  const timeSlots = getTimeSlots();

  // Find orders for a specific machine
  const getOrdersForMachine = useCallback(
    (machineId) => {
      return scheduledOrders.filter((order) => {
        // Check if any operation is assigned to this resource
        if (order.operations?.length > 0) {
          return order.operations.some((op) => op.resource_id === machineId);
        }
        // Fallback: check resource_id on order itself
        return order.resource_id === machineId;
      });
    },
    [scheduledOrders]
  );

  // Check if an order falls within a time slot
  const orderInSlot = useCallback(
    (order, slotTime) => {
      if (!order.scheduled_start || !order.scheduled_end) return false;

      const start = new Date(order.scheduled_start);
      const end = new Date(order.scheduled_end);

      if (viewMode === "day") {
        // 2-hour slots
        const slotEnd = new Date(slotTime);
        slotEnd.setHours(slotEnd.getHours() + 2);
        return start < slotEnd && end > slotTime;
      } else {
        // Day slots
        const slotEnd = new Date(slotTime);
        slotEnd.setDate(slotEnd.getDate() + 1);
        return start < slotEnd && end > slotTime;
      }
    },
    [viewMode]
  );

  // Schedule an order via API - uses the standard PUT endpoint
  const scheduleOrder = async (orderId, machineId, startTime) => {
    try {
      // Calculate end time based on estimated duration or default 2 hours
      const order = [...scheduledOrders, ...unscheduledOrders].find((o) => o.id === orderId);
      const durationHours = order?.estimated_time_minutes
        ? order.estimated_time_minutes / 60
        : 2;

      const endTime = new Date(startTime);
      endTime.setHours(endTime.getHours() + Math.ceil(durationHours));

      // Use the existing PUT endpoint to update schedule
      const res = await fetch(`${API_URL}/api/v1/production-orders/${orderId}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          scheduled_start: startTime.toISOString(),
          scheduled_end: endTime.toISOString(),
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to schedule order");
      }

      // Refresh data
      await fetchOrders();
      if (onScheduleUpdate) onScheduleUpdate();
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  // Handle drag start
  const handleDragStart = (event) => {
    const orderId = parseInt(event.active.id.replace("order-", ""));
    const order = [...scheduledOrders, ...unscheduledOrders].find((o) => o.id === orderId);
    setDraggedOrder(order || null);
  };

  // Handle drag end
  const handleDragEnd = async (event) => {
    setDraggedOrder(null);

    const { active, over } = event;
    if (!over) return;

    // Parse drop target ID: "cell-{machineId}-{slotIndex}"
    const overId = String(over.id);
    if (!overId.startsWith("cell-")) return;

    const parts = overId.split("-");
    if (parts.length !== 3) return;

    const machineId = parseInt(parts[1]);
    const slotIndex = parseInt(parts[2]);

    if (isNaN(machineId) || isNaN(slotIndex)) return;

    const orderId = parseInt(active.id.replace("order-", ""));
    const slot = timeSlots[slotIndex];
    if (!slot) return;

    await scheduleOrder(orderId, machineId, slot.time);
  };

  if (loading && machines.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
        <div className="text-gray-400">Loading scheduler...</div>
      </div>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="space-y-4">
        {/* Controls */}
        <div className="flex justify-between items-center">
          <div className="flex gap-3 items-center">
            <h2 className="text-xl font-bold text-white">Production Scheduler</h2>
            <select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-white text-sm"
            >
              <option value="day">Day</option>
              <option value="week">Week</option>
              <option value="month">Month</option>
            </select>
            <input
              type="date"
              value={selectedDate.toISOString().split("T")[0]}
              onChange={(e) => setSelectedDate(new Date(e.target.value))}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-white text-sm"
            />
            <button
              onClick={() => {
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                setSelectedDate(today);
              }}
              className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm"
            >
              Today
            </button>
          </div>
          <div className="text-sm text-gray-400">
            {unscheduledOrders.length} unscheduled • {scheduledOrders.length} scheduled
          </div>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-4">
          {/* Sidebar: Unscheduled Orders */}
          <div className="w-56 bg-gray-900 border border-gray-800 rounded-xl p-3 flex-shrink-0">
            <h3 className="text-white font-semibold text-sm mb-3">
              Unscheduled ({unscheduledOrders.length})
            </h3>
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {unscheduledOrders.map((order) => (
                <DraggableOrder key={order.id} order={order} />
              ))}
              {unscheduledOrders.length === 0 && (
                <p className="text-gray-500 text-sm text-center py-4">All orders scheduled</p>
              )}
            </div>
          </div>

          {/* Gantt Grid */}
          <div className="flex-1 bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse min-w-max">
                <thead className="bg-gray-800 sticky top-0 z-10">
                  <tr>
                    <th className="sticky left-0 z-20 bg-gray-800 border-r border-gray-700 px-4 py-2 text-left text-white font-semibold min-w-[160px]">
                      Machine
                    </th>
                    {timeSlots.map((slot, i) => (
                      <th
                        key={i}
                        className="border-r border-gray-700 px-2 py-2 text-center text-gray-400 text-xs min-w-[80px] whitespace-nowrap"
                      >
                        {slot.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {machines.length === 0 ? (
                    <tr>
                      <td colSpan={timeSlots.length + 1} className="p-8 text-center text-gray-500">
                        No machines found. Add work centers and resources in Manufacturing settings.
                      </td>
                    </tr>
                  ) : (
                    machines.map((machine) => {
                      const machineOrders = getOrdersForMachine(machine.id);

                      return (
                        <tr key={machine.id} className="border-b border-gray-800">
                          <td className="sticky left-0 z-10 bg-gray-900 border-r border-gray-700 px-4 py-3">
                            <div className="font-medium text-white text-sm">{machine.code}</div>
                            <div className="text-xs text-gray-400">{machine.name}</div>
                            <div
                              className={`text-xs mt-1 ${
                                machine.status === "available"
                                  ? "text-green-400"
                                  : machine.status === "busy"
                                  ? "text-yellow-400"
                                  : "text-gray-500"
                              }`}
                            >
                              {machine.status || "unknown"}
                            </div>
                          </td>
                          {timeSlots.map((slot, slotIndex) => {
                            const cellId = `cell-${machine.id}-${slotIndex}`;
                            const ordersInSlot = machineOrders.filter((o) =>
                              orderInSlot(o, slot.time)
                            );

                            return (
                              <DroppableCell key={cellId} id={cellId}>
                                {ordersInSlot.map((order) => (
                                  <div
                                    key={order.id}
                                    className="bg-blue-600 text-white text-xs p-1 rounded mb-1 truncate"
                                    title={`${order.code} - ${order.product_name || "N/A"}`}
                                  >
                                    {order.code}
                                  </div>
                                ))}
                              </DroppableCell>
                            );
                          })}
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Drag overlay */}
        <DragOverlay>
          {draggedOrder && (
            <div className="bg-blue-600 text-white p-3 rounded-lg shadow-xl border border-blue-400">
              <div className="font-semibold">{draggedOrder.code}</div>
              <div className="text-sm opacity-80">{draggedOrder.product_name || "N/A"}</div>
            </div>
          )}
        </DragOverlay>
      </div>
    </DndContext>
  );
}
