/**
 * Thin adapter to reuse src/lib/time.js inside the Gantt component.
 * Replace local helpers in ProductionGanttScheduler.jsx with these imports.
 */
import { makeCalendar, startOfDay, fmtTime, fmtDate } from "../../lib/time";

export function makeSchedulerCalendar(workSchedule, snapMinutes) {
  const cal = makeCalendar(workSchedule, snapMinutes);
  return {
    ...cal,
    startOfDay,
    fmtTime,
    fmtDate,
  };
}

