import { useEffect, useMemo, useRef, useState } from "react";

/**
 * Lightweight form flow helper:
 * - debounced async validate (per-field or whole form)
 * - dirty/pristine, disabling on submit, derived field recompute
 */
export function useFormFlow({
  initial,
  validate,
  onSubmit,
  debounceMs = 250,
}) {
  const [values, setValues] = useState(() => ({ ...initial }));
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [touched, setTouched] = useState({});
  const timer = useRef(0);

  const dirty = useMemo(() => {
    return JSON.stringify(initial) !== JSON.stringify(values);
  }, [initial, values]);

  const set = (patch) => {
    setValues((v) => ({ ...v, ...patch }));
  };

  const onChange = (name) => (eOrValue) => {
    const next =
      typeof eOrValue === "object" && eOrValue?.target
        ? eOrValue.target.value
        : eOrValue;
    setValues((v) => ({ ...v, [name]: next }));
    setTouched((t) => ({ ...t, [name]: true }));
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(async () => {
      if (validate) {
        try {
          setErrors(await validate({ ...values, [name]: next }));
        } catch {
          /* keep old errors */
        }
      }
    }, debounceMs);
  };

  const handleSubmit = async (e) => {
    e?.preventDefault?.();
    if (validate) {
      const errs = await validate(values);
      setErrors(errs || {});
      if (errs && Object.keys(errs).length) return;
    }
    setSubmitting(true);
    try {
      await onSubmit(values);
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(
    () => () => {
      if (timer.current) window.clearTimeout(timer.current);
    },
    []
  );

  return {
    values,
    set,
    onChange,
    errors,
    setErrors,
    submitting,
    dirty,
    touched,
    handleSubmit,
  };
}

