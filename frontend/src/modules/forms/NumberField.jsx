/**
 * Stable number input: avoids locale drift and precision fights.
 */
import { parseDecimal, toFixedSafe } from "../../lib/number";

export default function NumberField({
  value,
  onChange,
  min,
  max,
  step = 0.01,
  placeholder,
  ...rest
}) {
  return (
    <input
      {...rest}
      inputMode="decimal"
      placeholder={placeholder ?? "0.00"}
      value={value ?? ""}
      onChange={(e) => {
        const next = parseDecimal(e.target.value);
        if (next === null) return onChange(""); // keep raw empty
        if (min !== undefined && next < min) return onChange(min);
        if (max !== undefined && next > max) return onChange(max);
        onChange(next);
      }}
      onBlur={(e) => {
        const n = parseDecimal(e.target.value);
        if (n !== null)
          e.target.value = toFixedSafe(
            n,
            String(step).split(".")[1]?.length ?? 2
          );
      }}
      className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm w-full"
    />
  );
}

