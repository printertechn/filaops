/* ============================================================================
 * ORIGINAL IMPLEMENTATION - COMMENTED OUT FOR TESTING NEW VERSION
 * ============================================================================
 *
 * The original implementation has been commented out to test a new version
 * with resize functionality and snap-to-grid. If the new version doesn't work,
 * uncomment this section and remove the new implementation below.
 *
 * ============================================================================
 */

/*
import { useState, useEffect, useRef, useCallback } from "react";
// ... [ORIGINAL CODE COMMENTED OUT] ...
*/

/* ============================================================================
 * NEW IMPLEMENTATION WITH WORK SCHEDULE, AUTO-ARRANGE, KEYBOARD SHORTCUTS
 * ============================================================================ */

import { useState, useEffect, useCallback, useMemo } from "react";
import {
  DndContext,
  DragOverlay,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  useDraggable,
  useDroppable,
} from "@dnd-kit/core";
import { useToast } from "./Toast";
import { useApi } from "../lib/useApi";
import {
  makeCalendar,
  fmtTime as libFmtTime,
  parseHHMM,
  toHours,
} from "../lib/time";

/** View + sizing */
const VIEW = Object.freeze({ DAY: "day", WEEK: "week", MONTH: "month" });
const VIEW_CONFIG = {
  [VIEW.DAY]: { slotIntervalHours: 2, slotsPerView: 12, slotWidthPx: 80 },
  [VIEW.WEEK]: { slotIntervalHours: 24, slotsPerView: 7, slotWidthPx: 100 },
  [VIEW.MONTH]: { slotIntervalHours: 24, slotsPerView: 30, slotWidthPx: 60 },
};
const HOUR_MS = 60 * 60 * 1000;
const LS_KEY = "ganttWorkScheduleV1";

/** Utilities */
const msFromHours = (h) => Math.round(h * HOUR_MS);
const fmtDur = (ms) => {
  const h = Math.floor(ms / HOUR_MS);
  const m = Math.round((ms % HOUR_MS) / (60 * 1000));
  return h > 0 ? `${h}h${m ? ` ${m}m` : ""}` : `${m}m`;
};

// why: normalize inputs (Date|string|number) to epoch ms
const toMs = (v) => {
  if (v instanceof Date) return v.getTime();
  if (typeof v === "number") return v;
  // treat anything else as date-like
  const t = new Date(v);
  return Number.isFinite(t.getTime()) ? t.getTime() : Date.now();
};

const startOfDayMs = (v) => {
  const d = new Date(toMs(v));
  d.setHours(0, 0, 0, 0);
  return d.getTime();
};

/** Sidebar item */
function DraggableOrder({ order }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({ id: order.id.toString() });
  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : undefined;
  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      data-testid={`order-${order.id}`}
      className={`bg-gray-800 border border-gray-700 rounded-lg p-3 cursor-move hover:border-blue-500 transition-colors ${
        isDragging ? "opacity-50" : ""
      }`}
    >
      <div className="text-white font-medium text-sm mb-1">{order.code}</div>
      <div className="text-gray-400 text-xs mb-1">
        {order.product_name || "N/A"}
      </div>
      <div className="text-gray-500 text-xs">Qty: {order.quantity_ordered}</div>
    </div>
  );
}

/** Resize handle component */
function ResizeHandle({ edge, onResizeStart }) {
  return (
    <div
      onPointerDown={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onResizeStart(edge, e.clientX);
      }}
      className={`absolute top-0 ${
        edge === "start" ? "left-0" : "right-0"
      } h-full w-2 cursor-ew-resize`}
      style={{ touchAction: "none" }}
      title={`Drag to resize ${edge === "start" ? "start" : "end"}`}
    />
  );
}

/** Timeline block (draggable + resizable) with inline tooltip */
function DraggableOrderBlock({
  order,
  leftPx,
  widthPx,
  hasConflict,
  onScheduleOrder,
  onResizeStart,
  isResizing,
  tooltip, // {start,end,durationText}
  selected,
  onSelect,
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({ id: order.id.toString() });
  const dragProps = isResizing ? {} : { ...listeners, ...attributes };
  const style = {
    position: "absolute",
    left: `${Math.max(0, leftPx)}px`,
    width: `${Math.max(50, widthPx)}px`,
    top: `4px`,
    bottom: `4px`,
    transform: transform
      ? `translate3d(${transform.x}px, ${transform.y}px, 0)`
      : undefined,
    zIndex: isDragging ? 100 : selected ? 50 : 10,
    opacity: isDragging ? 0.5 : 1,
    outline: selected ? "2px solid rgba(147,197,253,0.9)" : "none",
    borderRadius: "6px",
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...dragProps}
      data-testid={`block-${order.id}`}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(order.id);
        onScheduleOrder && onScheduleOrder(order);
      }}
      className={`${
        hasConflict
          ? "bg-red-600 hover:bg-red-500 border-red-400"
          : "bg-blue-600 hover:bg-blue-500 border-blue-400"
      } border rounded px-1.5 py-0.5 cursor-move transition-colors shadow-sm relative select-none`}
      title={`${order.code} - ${order.product_name || "N/A"}`}
    >
      <ResizeHandle edge="start" onResizeStart={onResizeStart} />
      <ResizeHandle edge="end" onResizeStart={onResizeStart} />

      <div className="text-white text-xs font-medium truncate leading-tight">
        {order.code} {hasConflict && "⚠️"}
      </div>
      {widthPx > 70 && (
        <div
          className={`text-xs truncate leading-tight ${
            hasConflict ? "text-red-100" : "text-blue-100"
          }`}
        >
          {order.product_name || "N/A"}
        </div>
      )}
      {widthPx > 100 && (
        <div
          className={`text-xs leading-tight ${
            hasConflict ? "text-red-200" : "text-blue-200"
          }`}
        >
          Qty: {order.quantity_ordered}
        </div>
      )}
      {tooltip && (
        <div className="absolute -top-6 right-0 text-[10px] bg-gray-900/90 border border-gray-700 rounded px-1 py-0.5 text-gray-200 pointer-events-none whitespace-nowrap">
          {tooltip.start} – {tooltip.end} • {tooltip.durationText}
        </div>
      )}
    </div>
  );
}

/** Column droppable */
function DroppableSlot({ machineId, slotIndex, slotWidth, isHovered }) {
  const { setNodeRef, isOver } = useDroppable({
    id: `machine-${machineId}-slot-${slotIndex}`,
  });
  return (
    <div
      ref={setNodeRef}
      data-testid={`slot-${machineId}-${slotIndex}`}
      className={`absolute border-r border-gray-800 min-h-full cursor-pointer ${
        isHovered || isOver
          ? "bg-blue-500/20 border-blue-500 z-30"
          : "bg-transparent hover:bg-gray-800/20"
      }`}
      style={{
        left: `${slotIndex * slotWidth}px`,
        width: `${slotWidth}px`,
        height: "100%",
      }}
    />
  );
}

/** Work Schedule Modal */
function WorkScheduleModal({ open, schedule, onClose, onSave }) {
  const dayLabels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const [draft, setDraft] = useState(schedule);
  const [err, setErr] = useState("");

  // Reset draft when modal opens with new schedule
  useEffect(() => {
    if (open) {
      setDraft(schedule);
      setErr("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]); // Only reset when modal opens, not on every schedule change

  if (!open) return null;

  const validate = () => {
    const ps = parseHHMM(draft.start);
    const pe = parseHHMM(draft.end);
    if (!ps || !pe) return "Use HH:MM (24h) format.";
    const startH = toHours(ps);
    const endH = toHours(pe);
    if (endH <= startH) return "End time must be after start time.";
    if (!draft.days.some(Boolean)) return "Select at least one working day.";
    return "";
  };

  const save = () => {
    const v = validate();
    if (v) {
      setErr(v);
      return;
    }
    onSave(draft);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      {/* Panel */}
      <div className="relative bg-gray-900 border border-gray-800 rounded-xl w-full max-w-lg mx-4 shadow-2xl">
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <div className="text-white font-semibold">Work Schedule</div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 text-sm px-2 py-1 rounded border border-gray-700"
          >
            ×
          </button>
        </div>

        <div className="p-4 space-y-4">
          <div>
            <div className="text-gray-300 text-sm mb-2">Working days</div>
            <div className="flex flex-wrap gap-2">
              {dayLabels.map((label, idx) => (
                <label
                  key={label}
                  className="flex items-center gap-2 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-200"
                >
                  <input
                    type="checkbox"
                    checked={!!draft.days[idx]}
                    onChange={(e) =>
                      setDraft((d) => {
                        const days = d.days.slice();
                        days[idx] = e.target.checked;
                        return { ...d, days };
                      })
                    }
                    className="accent-blue-500"
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-gray-300 text-sm mb-1">
                Start time (24h)
              </label>
              <input
                type="text"
                placeholder="08:00"
                value={draft.start}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, start: e.target.value }))
                }
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              />
            </div>
            <div className="flex-1">
              <label className="block text-gray-300 text-sm mb-1">
                End time (24h)
              </label>
              <input
                type="text"
                placeholder="22:00"
                value={draft.end}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, end: e.target.value }))
                }
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              />
            </div>
          </div>

          {err && <div className="text-red-400 text-sm">{err}</div>}

          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={onClose}
              className="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-sm border border-gray-700"
            >
              Cancel
            </button>
            <button
              onClick={save}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm"
            >
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ProductionGanttScheduler({
  productionOrders,
  onScheduleUpdate,
  onScheduleOrder,
  // eslint-disable-next-line no-unused-vars
  onStartOrder: _onStartOrder,
  // eslint-disable-next-line no-unused-vars
  onCompleteOrder: _onCompleteOrder,
  // eslint-disable-next-line no-unused-vars
  onScrapOrder: _onScrapOrder,
}) {
  const api = useApi();
  const toast = useToast();
  const [machines, setMachines] = useState([]);
  const [viewMode, setViewMode] = useState(VIEW.WEEK);
  const [selectedDate, setSelectedDate] = useState(() => {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d;
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [draggedOrder, setDraggedOrder] = useState(null);
  const [hoveredSlot, setHoveredSlot] = useState(null);
  const [fullOrderDetails, setFullOrderDetails] = useState(() => new Map());

  const [autoArrangeEnabled, setAutoArrangeEnabled] = useState(true);
  const [resizing, setResizing] = useState(null); // {orderId,machineId,edge,startMs,endMs,originX,pxPerHour}
  const [previewTimes, setPreviewTimes] = useState(() => new Map());
  const [selectedOrderId, setSelectedOrderId] = useState(null);

  // Work Schedule (default Mon–Sat 08:00–22:00)
  const defaultSchedule = useMemo(
    () => ({
      days: [false, true, true, true, true, true, true],
      start: "08:00",
      end: "22:00",
    }),
    []
  );
  const [workSchedule, setWorkSchedule] = useState(() => {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (
          Array.isArray(parsed.days) &&
          parsed.days.length === 7 &&
          parsed.start &&
          parsed.end
        ) {
          return parsed;
        }
      }
    } catch {
      // Ignore parse errors
    }
    return defaultSchedule;
  });
  const [scheduleOpen, setScheduleOpen] = useState(false);

  // Snap granularity (default 15 minutes)
  const [snapMinutes, setSnapMinutes] = useState(15);

  // Calendar helpers from shared lib
  const calendar = useMemo(
    () => makeCalendar(workSchedule, snapMinutes),
    [workSchedule, snapMinutes]
  );
  const NOW_MS = useMemo(() => calendar.snap(Date.now()), [calendar]);
  const fmtTime = libFmtTime;

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor)
  );

  /** Persist schedule on save */
  const handleSaveSchedule = (newSchedule) => {
    setWorkSchedule(newSchedule);
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(newSchedule));
    } catch {
      // Ignore storage errors
    }
    setScheduleOpen(false);
    toast.success("Work schedule updated");
  };

  /** Fetch machines/resources (API client) */
  const fetchMachines = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const allWorkCenters = await api.get(
        `/api/v1/work-centers/?active_only=true`
      );
      const workCenters = allWorkCenters.filter(
        (wc) => wc.center_type === "machine" || wc.resource_count > 0
      );

      const resourceFetches = workCenters.map((wc) =>
        api
          .get(`/api/v1/work-centers/${wc.id}/resources?active_only=true`)
          .then((resources) =>
            resources.map((r) => ({ ...r, work_center: wc }))
          )
          .catch(() => [])
      );
      const settled = await Promise.all(resourceFetches);
      const allResources = settled.flat();
      setMachines(allResources);
    } catch (err) {
      const msg = err?.message || "Failed to load machines";
      setError(msg);
      console.error("Failed to fetch machines:", err);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [api, toast]);

  useEffect(() => {
    fetchMachines();
  }, [fetchMachines]);

  /** Full details for scheduled orders */
  const scheduledIds = useMemo(
    () =>
      productionOrders
        .filter((o) => o.scheduled_start && o.scheduled_end)
        .map((o) => o.id),
    [productionOrders]
  );

  useEffect(() => {
    if (scheduledIds.length === 0) return;
    let cancelled = false;
    (async () => {
      const fetches = scheduledIds.map((id) =>
        api
          .get(`/api/v1/production-orders/${id}`)
          .then((order) => [id, order])
          .catch((err) => {
            console.warn(`Failed to fetch order ${id}:`, err);
            return null;
          })
      );
      const settled = await Promise.all(fetches);
      if (cancelled) return;
      setFullOrderDetails((prev) => {
        const next = new Map(prev);
        for (const pair of settled) {
          if (!pair) continue;
          const [id, order] = pair;
          next.set(id, order);
        }
        return next;
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [scheduledIds, api]);

  /** Merge list + details */
  const enrichedOrders = useMemo(
    () =>
      productionOrders.map((o) =>
        fullOrderDetails.get(o.id) ? { ...o, ...fullOrderDetails.get(o.id) } : o
      ),
    [productionOrders, fullOrderDetails]
  );

  /** Buckets */
  const scheduledOrders = useMemo(
    () =>
      enrichedOrders.filter(
        (o) =>
          o.scheduled_start &&
          o.scheduled_end &&
          (o.status === "released" ||
            o.status === "scheduled" ||
            o.status === "in_progress")
      ),
    [enrichedOrders]
  );
  const unscheduledOrders = useMemo(
    () =>
      enrichedOrders.filter(
        (o) =>
          (!o.scheduled_start || !o.scheduled_end) &&
          (o.status === "released" || o.status === "scheduled")
      ),
    [enrichedOrders]
  );
  const inProgressOrders = useMemo(
    () => enrichedOrders.filter((o) => o.status === "in_progress"),
    [enrichedOrders]
  );

  /** View params */
  const { slotIntervalHours, slotsPerView, slotWidthPx } =
    VIEW_CONFIG[viewMode];

  /** px/hour for resize */
  const pxPerHour = useMemo(() => {
    if (viewMode === VIEW.DAY) return slotWidthPx / slotIntervalHours;
    return slotWidthPx / 24;
  }, [viewMode, slotIntervalHours, slotWidthPx]);

  /** Timeline slots (hourly base) */
  const timeSlots = useMemo(() => {
    const slots = [];
    const baseMs = startOfDayMs(selectedDate);
    const hours =
      viewMode === VIEW.DAY ? 24 : viewMode === VIEW.WEEK ? 168 : 720;
    for (let i = 0; i < hours; i++) {
      slots.push(new Date(baseMs + i * HOUR_MS)); // keep Date objects for rendering labels
    }
    return slots;
  }, [selectedDate, viewMode]);

  /** Header/droppable columns */
  const filteredSlots = useMemo(() => {
    const arr = [];
    for (let i = 0; i < timeSlots.length; i += slotIntervalHours) {
      arr.push(timeSlots[i]);
      if (arr.length >= slotsPerView) break;
    }
    return arr;
  }, [timeSlots, slotIntervalHours, slotsPerView]);

  /** Orders per resource (sorted) */
  const ordersByResource = useMemo(() => {
    const map = new Map();
    for (const o of scheduledOrders) {
      const resId = o.operations?.[0]?.resource_id ?? o.resource_id ?? null;
      if (!resId) continue;
      if (!map.has(resId)) map.set(resId, []);
      map.get(resId).push(o);
    }
    for (const list of map.values()) {
      list.sort(
        (a, b) => new Date(a.scheduled_start) - new Date(b.scheduled_start)
      );
    }
    return map;
  }, [scheduledOrders]);

  /** Conflicts for badges */
  const conflictIdsByMachine = useMemo(() => {
    const result = new Map();
    for (const [machineId, list] of ordersByResource.entries()) {
      const conflicts = new Set();
      let lastEnd = null;
      let lastOrder = null;
      for (const o of list) {
        const s = new Date(o.scheduled_start).getTime();
        const e = new Date(o.scheduled_end).getTime();
        if (lastEnd !== null && s < lastEnd) {
          conflicts.add(o.id);
          if (lastOrder) conflicts.add(lastOrder.id);
          if (e > lastEnd) {
            lastEnd = e;
            lastOrder = o;
          }
        } else {
          lastEnd = e;
          lastOrder = o;
        }
      }
      result.set(machineId, conflicts);
    }
    return result;
  }, [ordersByResource]);

  /** Duration calc */
  const calculateOrderDurationHours = useCallback((order) => {
    const qty = Math.max(1, Number(order.quantity_ordered ?? 1));
    if (order.operations?.length) {
      const totalMinutes = order.operations.reduce(
        (sum, op) =>
          sum +
          Number(op.planned_setup_minutes ?? 0) +
          Number(op.planned_run_minutes ?? 0),
        0
      );
      if (totalMinutes > 0) {
        const perUnit = totalMinutes / qty;
        if (perUnit >= 60) return totalMinutes / 60;
      }
    }
    if (order.estimated_time_minutes) {
      const perUnit = Number(order.estimated_time_minutes);
      if (!Number.isNaN(perUnit) && perUnit > 0) return (perUnit * qty) / 60;
    }
    return 2 * qty;
  }, []);

  /** API schedule */
  const scheduleOrder = useCallback(
    async (orderId, machineId, startMs, endMs) => {
      try {
        await api.put(`/api/v1/production-orders/${orderId}/schedule`, {
          scheduled_start: new Date(startMs).toISOString(),
          scheduled_end: new Date(endMs).toISOString(),
          resource_id: machineId,
          notes: "Scheduled via Gantt chart",
        });
        // Refresh order details
        try {
          const full = await api.get(`/api/v1/production-orders/${orderId}`);
          setFullOrderDetails((prev) => {
            const next = new Map(prev);
            next.set(orderId, full);
            return next;
          });
        } catch (err) {
          console.warn(`Failed to refresh order ${orderId} details:`, err);
        }
      } catch (err) {
        console.error(`Failed to schedule order ${orderId}:`, err);
        throw err; // Re-throw so caller can show toast
      }
    },
    [api]
  );

  /** Auto-push overlaps */
  const pushOverlaps = useCallback(
    async (machineId, primaryOrderId, primaryStartMs, primaryEndMs) => {
      const list = (ordersByResource.get(machineId) ?? [])
        .slice()
        .sort(
          (a, b) => new Date(a.scheduled_start) - new Date(b.scheduled_start)
        );
      let cursorEnd = primaryEndMs;
      let changed = 0;
      for (const o of list) {
        if (o.id === primaryOrderId) continue;
        const s = new Date(o.scheduled_start).getTime();
        const e = new Date(o.scheduled_end).getTime();
        const overlaps = s < cursorEnd && e > s;
        const isAfterOrAtPrimary = s >= primaryStartMs;
        if (overlaps && isAfterOrAtPrimary) {
          const duration = Math.max(30 * 60 * 1000, e - s);
          const { startMs, endMs } = calendar.scheduleWithinCalendar(
            cursorEnd,
            duration,
            NOW_MS
          );
          try {
            await scheduleOrder(o.id, machineId, startMs, endMs);
            cursorEnd = endMs;
            changed++;
          } catch (err) {
            console.error("Auto-push failed", o.id, err);
            cursorEnd = e; // continue
          }
        } else if (s >= cursorEnd) break;
      }
      return changed;
    },
    [ordersByResource, scheduleOrder, calendar, NOW_MS]
  );

  /** Auto-compact forward */
  const compactGapsForward = useCallback(
    async (machineId, fromOrderId, startCursorMs) => {
      const list = (ordersByResource.get(machineId) ?? [])
        .slice()
        .sort(
          (a, b) => new Date(a.scheduled_start) - new Date(b.scheduled_start)
        );
      let cursor = startCursorMs;
      let found = false;
      for (const o of list) {
        if (o.id === fromOrderId) {
          const e = new Date(o.scheduled_end).getTime();
          cursor = Math.max(cursor, e);
          found = true;
          break;
        }
      }
      if (!found) return 0;

      let moved = 0;
      for (const o of list) {
        if (o.id === fromOrderId) continue;
        const s = new Date(o.scheduled_start).getTime();
        const e = new Date(o.scheduled_end).getTime();
        const duration = Math.max(30 * 60 * 1000, e - s);
        if (s > cursor) {
          const { startMs, endMs } = calendar.scheduleWithinCalendar(
            cursor,
            duration,
            NOW_MS
          );
          try {
            await scheduleOrder(o.id, machineId, startMs, endMs);
            cursor = endMs;
            moved++;
          } catch (err) {
            console.error("Auto-pull failed", o.id, err);
            cursor = e;
          }
        } else {
          cursor = Math.max(cursor, e);
        }
      }
      return moved;
    },
    [ordersByResource, scheduleOrder, calendar, NOW_MS]
  );

  /** DnD */
  const handleDragStart = (event) => {
    const id = Number(event.active?.id);
    const order = [...scheduledOrders, ...unscheduledOrders].find(
      (o) => o.id === id
    );
    setDraggedOrder(order ?? null);
    if (order) setSelectedOrderId(order.id);
  };
  const handleDragEnd = async (event) => {
    const over = event.over;
    setDraggedOrder(null);
    setHoveredSlot(null);
    if (!over) return;

    const orderId = Number(event.active?.id);
    const order =
      [...scheduledOrders, ...unscheduledOrders].find(
        (o) => o.id === orderId
      ) ?? null;
    if (!order) return;

    const parts = over.id.toString().split("-");
    if (parts.length < 4 || parts[0] !== "machine" || parts[2] !== "slot")
      return;

    const machineId = Number(parts[1]);
    const slotIndex = Number(parts[3]);
    if (Number.isNaN(machineId) || Number.isNaN(slotIndex)) return;

    const rawStart = new Date(filteredSlots[slotIndex]).getTime();
    const durationMs = msFromHours(calculateOrderDurationHours(order));
    const { startMs, endMs } = calendar.scheduleWithinCalendar(
      rawStart,
      durationMs,
      NOW_MS
    );

    try {
      await scheduleOrder(orderId, machineId, startMs, endMs);
      if (autoArrangeEnabled) {
        const pushed = await pushOverlaps(machineId, orderId, startMs, endMs);
        const pulled = await compactGapsForward(machineId, orderId, endMs);
        if (pushed + pulled > 0)
          toast.success(`Auto-arranged ${pushed + pulled} job(s)`);
      }
      toast.success("Order scheduled");
      onScheduleUpdate && onScheduleUpdate();
    } catch (err) {
      toast.error(`Failed to schedule: ${err.message}`);
    }
  };

  /** Resizing */
  const beginResize = useCallback(
    (order, machineId, edge, clientX) => {
      const startMs = new Date(order.scheduled_start).getTime();
      const endMs = new Date(order.scheduled_end).getTime();
      setResizing({
        orderId: order.id,
        machineId,
        edge,
        startMs,
        endMs,
        originX: clientX,
        pxPerHour,
      });
      setPreviewTimes((prev) => {
        const next = new Map(prev);
        next.set(order.id, { start: startMs, end: endMs });
        return next;
      });
      setSelectedOrderId(order.id);
    },
    [pxPerHour]
  );

  useEffect(() => {
    if (!resizing) return;

    const onMove = (e) => {
      const dx = e.clientX - resizing.originX;
      const deltaHours = dx / resizing.pxPerHour;
      const deltaMs = deltaHours * HOUR_MS;
      let newStart = resizing.startMs;
      let newEnd = resizing.endMs;

      if (resizing.edge === "start") {
        newStart = calendar.snap(resizing.startMs + deltaMs);
        newStart = Math.max(newStart, NOW_MS);
        if (newStart > newEnd - 30 * 60 * 1000)
          newStart = newEnd - 30 * 60 * 1000;
      } else {
        newEnd = calendar.snap(resizing.endMs + deltaMs);
        if (newEnd < newStart + 30 * 60 * 1000)
          newEnd = newStart + 30 * 60 * 1000;
      }

      setPreviewTimes((prev) => {
        const next = new Map(prev);
        next.set(resizing.orderId, { start: newStart, end: newEnd });
        return next;
      });
    };

    const onUp = async () => {
      const preview = previewTimes.get(resizing.orderId);
      const machineId = resizing.machineId;
      setResizing(null);
      if (!preview) {
        setPreviewTimes((prev) => {
          const next = new Map(prev);
          next.delete(resizing.orderId);
          return next;
        });
        return;
      }
      const duration = Math.max(30 * 60 * 1000, preview.end - preview.start);
      const { startMs, endMs } = calendar.scheduleWithinCalendar(
        preview.start,
        duration,
        NOW_MS
      );
      try {
        await scheduleOrder(resizing.orderId, machineId, startMs, endMs);
        if (autoArrangeEnabled) {
          const pushed = await pushOverlaps(
            machineId,
            resizing.orderId,
            startMs,
            endMs
          );
          const pulled = await compactGapsForward(
            machineId,
            resizing.orderId,
            endMs
          );
          if (pushed + pulled > 0)
            toast.success(`Auto-arranged ${pushed + pulled} job(s)`);
        }
        onScheduleUpdate && onScheduleUpdate();
      } catch (err) {
        toast.error(`Failed to schedule: ${err.message}`);
      }
      setPreviewTimes((prev) => {
        const next = new Map(prev);
        next.delete(resizing.orderId);
        return next;
      });
    };

    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp, { once: true });
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
  }, [
    resizing,
    previewTimes,
    calendar,
    NOW_MS,
    scheduleOrder,
    autoArrangeEnabled,
    pushOverlaps,
    compactGapsForward,
    onScheduleUpdate,
    toast,
  ]);

  /** Keyboard nudge: ←/→ move; Alt=resize end; Alt+Shift=resize start; Shift=×4 */
  useEffect(() => {
    if (!selectedOrderId) return;
    const order = scheduledOrders.find((o) => o.id === selectedOrderId);
    if (!order) return;
    const machineId = order.operations?.[0]?.resource_id ?? order.resource_id;
    if (!machineId) return;

    const handler = async (e) => {
      const left = e.key === "ArrowLeft";
      const right = e.key === "ArrowRight";
      if (!left && !right) return;

      const factor = e.shiftKey ? 4 : 1;
      const stepMs = snapMinutes * 60 * 1000;
      const step = factor * stepMs * (left ? -1 : 1);

      const curStart = new Date(order.scheduled_start).getTime();
      const curEnd = new Date(order.scheduled_end).getTime();
      const curDuration = Math.max(30 * 60 * 1000, curEnd - curStart);

      if (e.altKey && e.shiftKey) {
        // resize START
        const newStartTent = curStart + step;
        const { startMs, endMs } = calendar.scheduleWithinCalendar(
          newStartTent,
          curEnd - newStartTent,
          NOW_MS
        );
        try {
          await scheduleOrder(order.id, machineId, startMs, endMs);
          if (autoArrangeEnabled) {
            const pushed = await pushOverlaps(
              machineId,
              order.id,
              startMs,
              endMs
            );
            const pulled = await compactGapsForward(machineId, order.id, endMs);
            if (pushed + pulled > 0)
              toast.success(`Auto-arranged ${pushed + pulled} job(s)`);
          }
          onScheduleUpdate && onScheduleUpdate();
        } catch (err) {
          toast.error(`Failed to resize: ${err.message}`);
        }
        e.preventDefault();
        return;
      }

      if (e.altKey) {
        // resize END
        const newEndTent = curEnd + step;
        const { startMs, endMs } = calendar.scheduleWithinCalendar(
          curStart,
          newEndTent - curStart,
          NOW_MS
        );
        try {
          await scheduleOrder(order.id, machineId, startMs, endMs);
          if (autoArrangeEnabled) {
            const pushed = await pushOverlaps(
              machineId,
              order.id,
              startMs,
              endMs
            );
            const pulled = await compactGapsForward(machineId, order.id, endMs);
            if (pushed + pulled > 0)
              toast.success(`Auto-arranged ${pushed + pulled} job(s)`);
          }
          onScheduleUpdate && onScheduleUpdate();
        } catch (err) {
          toast.error(`Failed to resize: ${err.message}`);
        }
        e.preventDefault();
        return;
      }

      // move
      const tentativeStart = curStart + step;
      const { startMs, endMs } = calendar.scheduleWithinCalendar(
        tentativeStart,
        curDuration,
        NOW_MS
      );
      try {
        await scheduleOrder(order.id, machineId, startMs, endMs);
        if (autoArrangeEnabled) {
          const pushed = await pushOverlaps(
            machineId,
            order.id,
            startMs,
            endMs
          );
          const pulled = await compactGapsForward(machineId, order.id, endMs);
          if (pushed + pulled > 0)
            toast.success(`Auto-arranged ${pushed + pulled} job(s)`);
        }
        onScheduleUpdate && onScheduleUpdate();
      } catch (err) {
        toast.error(`Failed to move: ${err.message}`);
      }
      e.preventDefault();
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [
    selectedOrderId,
    scheduledOrders,
    calendar,
    scheduleOrder,
    autoArrangeEnabled,
    pushOverlaps,
    compactGapsForward,
    onScheduleUpdate,
    toast,
    snapMinutes,
    NOW_MS,
  ]);

  // Position helpers (number-safe version)
  const computeLeftWidth = useCallback(
    (startMsInput, endMsInput) => {
      const viewStartMs = startOfDayMs(selectedDate);
      const startMs = toMs(startMsInput);
      const endMs = toMs(endMsInput);

      if (viewMode === VIEW.DAY) {
        const startHours = (startMs - viewStartMs) / HOUR_MS; // hours offset from day start
        const durHours = (endMs - startMs) / HOUR_MS;
        const startUnits = startHours / slotIntervalHours;
        const durationUnits = durHours / slotIntervalHours;
        return {
          leftPx: startUnits * slotWidthPx,
          widthPx: durationUnits * slotWidthPx,
        };
      } else {
        const DAY_MS = 24 * HOUR_MS;
        const startUnits = (startMs - viewStartMs) / DAY_MS; // days
        const durationUnits = (endMs - startMs) / DAY_MS; // days
        return {
          leftPx: startUnits * slotWidthPx,
          widthPx: durationUnits * slotWidthPx,
        };
      }
    },
    [selectedDate, viewMode, slotIntervalHours, slotWidthPx]
  );

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
        <div className="text-gray-400">Loading scheduler...</div>
      </div>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragOver={(e) => setHoveredSlot(e.over?.id?.toString() || null)}
    >
      <div
        className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden flex flex-col w-full max-w-full"
        style={{ height: "calc(100vh - 350px)", maxHeight: "700px" }}
        onClick={() => setSelectedOrderId(null)}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-800 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
            >
              <option value={VIEW.DAY}>Day View</option>
              <option value={VIEW.WEEK}>Week View</option>
              <option value={VIEW.MONTH}>Month View</option>
            </select>

            <input
              type="date"
              value={
                new Date(startOfDayMs(selectedDate)).toISOString().split("T")[0]
              }
              onChange={(e) => setSelectedDate(new Date(e.target.value))}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
            />

            <button
              onClick={() => {
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                setSelectedDate(today);
              }}
              className="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-sm transition-colors"
            >
              Today
            </button>

            {/* Snap */}
            <label className="text-xs text-gray-400 ml-2">Snap</label>
            <select
              value={snapMinutes}
              onChange={(e) => setSnapMinutes(Number(e.target.value))}
              className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1 text-white text-xs"
              title="Resize & auto-arrange snap granularity"
            >
              <option value={15}>15m</option>
              <option value={30}>30m</option>
              <option value={60}>60m</option>
            </select>

            {/* Auto-arrange toggle */}
            <label
              className="text-xs text-gray-400 ml-3 flex items-center gap-1"
              title="Push overlaps and pull gaps; respects your working calendar and 'now'"
            >
              <input
                type="checkbox"
                className="accent-blue-500"
                checked={autoArrangeEnabled}
                onChange={(e) => setAutoArrangeEnabled(e.target.checked)}
              />
              Auto-arrange
            </label>

            {/* Work Schedule button */}
            <button
              onClick={() => setScheduleOpen(true)}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm"
              title="Adjust working days and hours"
            >
              Work Schedule
            </button>

            {/* Keyboard help */}
            <div className="text-[10px] text-gray-500 ml-3">
              ←/→ move • Alt+←/→ resize end • Alt+Shift+←/→ resize start •
              Shift=×4
            </div>
          </div>

          <div className="text-sm text-gray-400">
            {unscheduledOrders.length} unscheduled • {scheduledOrders.length}{" "}
            scheduled • {inProgressOrders.length} in progress
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-900/20 border-b border-red-500/30 text-red-400 text-sm flex-shrink-0">
            {error}
          </div>
        )}

        <div className="flex flex-1 overflow-hidden min-w-0">
          {/* Sidebar */}
          <div className="w-56 bg-gray-900 border-r border-gray-800 p-3 overflow-y-auto flex-shrink-0 min-w-0">
            <h3 className="text-white font-semibold mb-2 text-xs sticky top-0 bg-gray-900 pb-2">
              Unscheduled ({unscheduledOrders.length})
            </h3>
            <div className="space-y-2">
              {unscheduledOrders.map((order) => (
                <DraggableOrder key={order.id} order={order} />
              ))}
              {unscheduledOrders.length === 0 && (
                <p className="text-gray-500 text-sm text-center py-4">
                  All orders scheduled
                </p>
              )}
            </div>
          </div>

          {/* Gantt */}
          <div className="flex-1 overflow-auto min-w-0 max-w-full">
            <div className="inline-block" style={{ minWidth: "max-content" }}>
              {/* Time header */}
              <div className="sticky top-0 z-20 bg-gray-900 border-b border-gray-800">
                <div className="flex">
                  <div className="w-40 border-r border-gray-800 p-2 text-gray-400 text-xs font-medium bg-gray-900 flex-shrink-0">
                    Machine
                  </div>
                  <div className="flex">
                    {filteredSlots.map((slot, i) => (
                      <div
                        key={i}
                        className="border-r border-gray-800 px-1 py-2 text-gray-400 text-xs text-center flex-shrink-0"
                        style={{
                          width: `${slotWidthPx}px`,
                          minWidth: `${slotWidthPx}px`,
                        }}
                      >
                        {viewMode === VIEW.MONTH || viewMode === VIEW.WEEK
                          ? new Date(slot).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                            })
                          : new Date(slot).toLocaleTimeString("en-US", {
                              hour: "numeric",
                              minute: "2-digit",
                              hour12: true,
                            })}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Rows */}
              <div className="relative">
                {machines.map((machine) => {
                  const machineOrders = (
                    ordersByResource.get(machine.id) ?? []
                  ).slice();
                  const conflictIds =
                    conflictIdsByMachine.get(machine.id) ?? new Set();

                  return (
                    <div
                      key={machine.id}
                      className="border-b border-gray-800 flex relative"
                      style={{ minHeight: 70 }}
                    >
                      {/* Machine label */}
                      <div className="w-40 border-r border-gray-800 p-2 bg-gray-900/50 sticky left-0 z-10 flex-shrink-0">
                        <div className="font-medium text-white text-xs">
                          {machine.code}
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5 truncate">
                          {machine.name}
                        </div>
                        <div
                          className={`text-xs mt-0.5 ${
                            machine.status === "available"
                              ? "text-green-400"
                              : machine.status === "busy"
                              ? "text-yellow-400"
                              : "text-red-400"
                          }`}
                        >
                          {machine.status || "unknown"}
                        </div>
                        {conflictIds.size > 0 && (
                          <div className="text-xs mt-1 text-red-400 font-semibold">
                            ⚠️ {conflictIds.size} conflict
                            {conflictIds.size > 1 ? "s" : ""}
                          </div>
                        )}
                      </div>

                      {/* Timeline */}
                      <div
                        className="relative"
                        style={{
                          width: `${slotsPerView * slotWidthPx}px`,
                          minWidth: `${slotsPerView * slotWidthPx}px`,
                        }}
                      >
                        {/* Droppable columns */}
                        {filteredSlots.map((_, slotIndex) => {
                          const slotId = `machine-${machine.id}-slot-${slotIndex}`;
                          const isHovered = hoveredSlot === slotId;
                          return (
                            <DroppableSlot
                              key={slotIndex}
                              machineId={machine.id}
                              slotIndex={slotIndex}
                              slotWidth={slotWidthPx}
                              isHovered={isHovered}
                            />
                          );
                        })}

                        {/* Blocks */}
                        {machineOrders.map((order) => {
                          const preview = previewTimes.get(order.id);
                          const startMs = preview
                            ? preview.start
                            : new Date(order.scheduled_start).getTime();
                          const endMs = preview
                            ? preview.end
                            : new Date(order.scheduled_end).getTime();

                          const assignedResource =
                            order.operations?.[0]?.resource_id ??
                            order.resource_id;
                          if (assignedResource !== machine.id) return null;

                          const { leftPx, widthPx } = computeLeftWidth(
                            startMs,
                            endMs
                          );
                          if (leftPx + widthPx < 0) return null;

                          const hasConflict = conflictIds.has(order.id);
                          const tooltip = preview
                            ? {
                                start: fmtTime(startMs),
                                end: fmtTime(endMs),
                                durationText: fmtDur(endMs - startMs),
                              }
                            : null;

                          return (
                            <DraggableOrderBlock
                              key={order.id}
                              order={{
                                ...order,
                                scheduled_start: new Date(startMs),
                                scheduled_end: new Date(endMs),
                              }}
                              leftPx={leftPx}
                              widthPx={widthPx}
                              hasConflict={hasConflict}
                              onScheduleOrder={onScheduleOrder}
                              onResizeStart={(edge, clientX) =>
                                beginResize(order, machine.id, edge, clientX)
                              }
                              isResizing={resizing?.orderId === order.id}
                              tooltip={tooltip}
                              selected={selectedOrderId === order.id}
                              onSelect={setSelectedOrderId}
                            />
                          );
                        })}
                      </div>
                    </div>
                  );
                })}

                {machines.length === 0 && (
                  <div className="p-8 text-center text-gray-500">
                    No machines available. Add work centers and resources in
                    Manufacturing → Work Centers.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Drag Overlay with live tooltip respecting working hours */}
        <DragOverlay>
          {draggedOrder ? (
            <div className="bg-blue-700 border border-blue-400 rounded px-3 py-2 shadow-lg relative">
              <div className="text-white text-sm font-semibold">
                {draggedOrder.code}
              </div>
              <div className="text-blue-100 text-xs">
                {draggedOrder.product_name || "N/A"}
              </div>
              {(() => {
                let tip = null;
                if (hoveredSlot) {
                  const parts = hoveredSlot.split("-");
                  if (
                    parts.length === 4 &&
                    parts[0] === "machine" &&
                    parts[2] === "slot"
                  ) {
                    const slotIndex = Number(parts[3]);
                    if (!Number.isNaN(slotIndex)) {
                      const rawStart = new Date(
                        filteredSlots[slotIndex]
                      ).getTime();
                      const durMs = msFromHours(
                        calculateOrderDurationHours(draggedOrder)
                      );
                      const { startMs, endMs } =
                        calendar.scheduleWithinCalendar(
                          rawStart,
                          durMs,
                          NOW_MS
                        );
                      tip = `${fmtTime(startMs)} – ${fmtTime(endMs)} • ${fmtDur(
                        endMs - startMs
                      )}`;
                    }
                  }
                }
                return tip ? (
                  <div className="absolute -top-6 right-0 text-[10px] bg-gray-900/90 border border-gray-700 rounded px-1 py-0.5 text-gray-200">
                    {tip}
                  </div>
                ) : null;
              })()}
            </div>
          ) : null}
        </DragOverlay>
      </div>

      {/* Work Schedule Modal */}
      <WorkScheduleModal
        open={scheduleOpen}
        schedule={workSchedule}
        onClose={() => setScheduleOpen(false)}
        onSave={handleSaveSchedule}
      />
    </DndContext>
  );
}
