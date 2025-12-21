/**
 * Currency input: user-friendly editing, nicely formatted on blur.
 */
import { parseDecimal, formatCurrency } from "../../lib/number";

export default function CurrencyField({
  value,
  onChange,
  currency = "USD",
  locale = "en-US",
  ...rest
}) {
  return (
    <input
      {...rest}
      inputMode="decimal"
      value={value ?? ""}
      onChange={(e) => onChange(parseDecimal(e.target.value) ?? "")}
      onBlur={(e) => {
        const n = parseDecimal(e.target.value);
        if (n !== null) e.target.value = formatCurrency(n, currency, locale);
      }}
      className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm w-full"
    />
  );
}

