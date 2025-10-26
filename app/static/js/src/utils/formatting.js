/**
 * Data formatting utilities
 */

/**
 * Format time in seconds to MM:SS
 */
export function formatTime(seconds) {
  if (!seconds && seconds !== 0) return '--:--';

  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);

  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format number with commas
 */
export function formatNumber(num, decimals = 0) {
  if (num === null || num === undefined) return '-';

  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}

/**
 * Format score based on metric type
 */
export function formatScore(score, metricType = 'score', decimals = 1) {
  if (score === null || score === undefined) return '-';

  if (metricType === 'time') {
    return formatTime(score);
  }

  return formatNumber(score, decimals);
}

/**
 * Format date
 */
export function formatDate(dateString, options = {}) {
  if (!dateString) return '-';

  const date = new Date(dateString);
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  };

  return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(date);
}

/**
 * Format date and time
 */
export function formatDateTime(dateString) {
  return formatDate(dateString, {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Pluralize word based on count
 */
export function pluralize(count, singular, plural = null) {
  if (count === 1) return singular;
  return plural || `${singular}s`;
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text, maxLength, ellipsis = '...') {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength - ellipsis.length) + ellipsis;
}

/**
 * Capitalize first letter
 */
export function capitalize(text) {
  if (!text) return '';
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/**
 * Convert camelCase to Title Case
 */
export function camelToTitle(text) {
  if (!text) return '';
  return text
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim();
}
