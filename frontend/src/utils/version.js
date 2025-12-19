/**
 * Version utility functions
 */

import { API_URL } from '../config/api';

/**
 * Get current version from backend API
 * @returns {Promise<string>} Current version (e.g., "1.5.0")
 */
export async function getCurrentVersion() {
  try {
    const response = await fetch(`${API_URL}/api/v1/system/version`);
    if (!response.ok) {
      throw new Error('Failed to fetch version');
    }
    const data = await response.json();
    return data.version;
  } catch (error) {
    console.error('Failed to get version from backend:', error);
    // Fallback to package.json version
    return "1.5.0";
  }
}

/**
 * Get current version synchronously (uses fallback)
 * @returns {string} Current version (e.g., "1.5.0")
 */
export function getCurrentVersionSync() {
  // Synchronous fallback for components that need immediate value
  return "1.5.0";
}

/**
 * Compare two semantic versions
 * @param {string} v1 - First version (e.g., "1.1.0")
 * @param {string} v2 - Second version (e.g., "1.2.0")
 * @returns {number} -1 if v1 < v2, 0 if v1 === v2, 1 if v1 > v2
 */
export function compareVersions(v1, v2) {
  // Remove 'v' prefix if present
  const cleanV1 = v1.replace(/^v/, "");
  const cleanV2 = v2.replace(/^v/, "");

  const parts1 = cleanV1.split(".").map(Number);
  const parts2 = cleanV2.split(".").map(Number);

  // Ensure both arrays have the same length
  const maxLength = Math.max(parts1.length, parts2.length);
  while (parts1.length < maxLength) parts1.push(0);
  while (parts2.length < maxLength) parts2.push(0);

  for (let i = 0; i < maxLength; i++) {
    if (parts1[i] < parts2[i]) return -1;
    if (parts1[i] > parts2[i]) return 1;
  }

  return 0;
}

/**
 * Check if version v1 is less than v2
 * @param {string} v1 - First version
 * @param {string} v2 - Second version
 * @returns {boolean} True if v1 < v2
 */
export function isVersionLessThan(v1, v2) {
  return compareVersions(v1, v2) < 0;
}

/**
 * Check if version v1 is greater than v2
 * @param {string} v1 - First version
 * @param {string} v2 - Second version
 * @returns {boolean} True if v1 > v2
 */
export function isVersionGreaterThan(v1, v2) {
  return compareVersions(v1, v2) > 0;
}

/**
 * Format version for display (removes 'v' prefix if present)
 * @param {string} version - Version string
 * @returns {string} Formatted version
 */
export function formatVersion(version) {
  return version.replace(/^v/, "");
}

