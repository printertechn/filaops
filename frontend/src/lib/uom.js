/**
 * Canonical UoM (Unit of Measure) conversions
 * Base unit for mass: grams (G)
 * Base unit for length: meters (M)
 *
 * This module consolidates UoM conversion logic that was previously
 * duplicated across BOMEditor.jsx and POCreateModal.jsx
 */

// Conversion factors: CONVERSIONS[fromUnit][toUnit] = factor
const CONVERSIONS = {
  // Mass conversions
  G: { KG: 0.001, LB: 0.00220462, OZ: 0.035274, G: 1 },
  KG: { G: 1000, LB: 2.20462, OZ: 35.274, KG: 1 },
  LB: { G: 453.592, KG: 0.453592, OZ: 16, LB: 1 },
  OZ: { G: 28.3495, KG: 0.0283495, LB: 0.0625, OZ: 1 },
  // Length conversions
  M: { CM: 100, MM: 1000, FT: 3.28084, IN: 39.3701, M: 1 },
  CM: { M: 0.01, MM: 10, FT: 0.0328084, IN: 0.393701, CM: 1 },
  MM: { M: 0.001, CM: 0.1, FT: 0.00328084, IN: 0.0393701, MM: 1 },
  FT: { M: 0.3048, CM: 30.48, MM: 304.8, IN: 12, FT: 1 },
  IN: { M: 0.0254, CM: 2.54, MM: 25.4, FT: 0.0833333, IN: 1 },
  // Count (no conversion needed)
  EA: { EA: 1 },
  PCS: { PCS: 1, EA: 1 },
};

/**
 * Convert a quantity from one unit to another
 * @param {number} qty - The quantity to convert
 * @param {string} fromUnit - Source unit (e.g., 'KG', 'G', 'LB')
 * @param {string} toUnit - Target unit (e.g., 'G', 'KG', 'OZ')
 * @returns {number} Converted quantity, or original if no conversion found
 */
export function convertUOM(qty, fromUnit, toUnit) {
  if (!qty || qty === 0) return 0;
  if (!fromUnit || !toUnit) return qty;

  const from = fromUnit.toUpperCase();
  const to = toUnit.toUpperCase();

  if (from === to) return qty;

  const factor = CONVERSIONS[from]?.[to];
  if (!factor) {
    console.warn(`No UoM conversion factor for ${from} → ${to}`);
    return qty;
  }

  return qty * factor;
}

/**
 * Format a weight value for display
 * @param {number} grams - Weight in grams
 * @param {string} displayUnit - Unit to display (default: 'G')
 * @param {number} decimals - Decimal places (default: 2)
 * @returns {string} Formatted weight string
 */
export function formatWeight(grams, displayUnit = 'G', decimals = 2) {
  const converted = convertUOM(grams, 'G', displayUnit);
  return `${converted.toFixed(decimals)} ${displayUnit}`;
}

/**
 * Convert to base unit (grams for mass, meters for length)
 * @param {number} qty - Quantity in source unit
 * @param {string} unit - Source unit
 * @returns {number} Quantity in base unit
 */
export function toBaseUnit(qty, unit) {
  if (!qty || !unit) return qty;
  const u = unit.toUpperCase();

  // Mass -> grams
  if (['G', 'KG', 'LB', 'OZ'].includes(u)) {
    return convertUOM(qty, u, 'G');
  }
  // Length -> meters
  if (['M', 'CM', 'MM', 'FT', 'IN'].includes(u)) {
    return convertUOM(qty, u, 'M');
  }
  // Count units stay as-is
  return qty;
}

/**
 * Check if a unit is a mass unit
 * @param {string} unit - Unit to check
 * @returns {boolean}
 */
export function isMassUnit(unit) {
  return ['G', 'KG', 'LB', 'OZ'].includes(unit?.toUpperCase());
}

/**
 * Check if a unit is a length unit
 * @param {string} unit - Unit to check
 * @returns {boolean}
 */
export function isLengthUnit(unit) {
  return ['M', 'CM', 'MM', 'FT', 'IN'].includes(unit?.toUpperCase());
}

/**
 * Get all available units for a given unit type
 * @param {string} unit - Any unit to determine the type
 * @returns {string[]} Array of compatible units
 */
export function getCompatibleUnits(unit) {
  const u = unit?.toUpperCase();
  if (isMassUnit(u)) return ['G', 'KG', 'LB', 'OZ'];
  if (isLengthUnit(u)) return ['M', 'CM', 'MM', 'FT', 'IN'];
  return ['EA', 'PCS'];
}
