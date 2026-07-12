/**
 * Parse a listing timestamp to epoch milliseconds, tolerant of the SQLite
 * "YYYY-MM-DD HH:MM:SS" (space-separated) form.
 *
 * That form is NOT valid ISO 8601, so Safari/WebKit returns `Invalid Date`
 * for it (Chrome/Node are lenient), which made the "Newly Listed" sort produce
 * NaN comparisons and arbitrary order in local mode (audit D11). Normalizing the
 * space to a 'T' makes every engine parse it. Already-ISO / offset strings
 * (the cloud path) pass through untouched. Unparseable input returns 0.
 *
 * @param {string | null | undefined} value
 * @returns {number} epoch ms, or 0 when the value is missing/unparseable
 */
export function listingTime(value) {
  if (!value) return 0;
  const iso = value.includes("T") ? value : value.replace(" ", "T");
  const t = new Date(iso).getTime();
  return Number.isNaN(t) ? 0 : t;
}
