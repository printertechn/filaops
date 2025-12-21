/**
 * Listens for 'api:error' and shows a toast. Central place -> fewer silent failures.
 */
import { useEffect } from "react";
import { on } from "../lib/events";
import { useToast } from "./Toast";

export default function ApiErrorToaster() {
  const toast = useToast();
  useEffect(() => {
    return on("api:error", (e) => {
      const method = e?.method || "GET";
      const url = e?.url || "";
      const status = e?.status ?? "";
      const msg = e?.message || "Request failed";
      toast.error(`${method} ${status} • ${msg}`);
      // why: visible debugging without opening the console
    });
  }, [toast]);
  return null;
}

