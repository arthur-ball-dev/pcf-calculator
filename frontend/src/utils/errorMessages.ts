/**
 * Error Message Mapping Utility
 *
 * Maps technical API error messages to user-friendly, actionable messages.
 * Improves UX by providing clear guidance instead of raw error codes.
 *
 * TASK-FE-007: Calculate Flow with Polling (Error Message User-Friendliness)
 */

/**
 * Map technical API error to user-friendly message
 *
 * @param apiError - Raw error message from API
 * @returns User-friendly error message with actionable guidance
 *
 * @example
 * getUserFriendlyError('Invalid emission factor for component: Cotton')
 * // Returns: "Unable to calculate emissions. The component 'Cotton' is missing emission data. Please contact support."
 */
export function getUserFriendlyError(apiError: string): string {
  // PRIORITY 1: Specific calculation/data errors (most specific)

  // Invalid emission factor errors
  if (apiError.toLowerCase().includes('invalid emission factor')) {
    const componentMatch = apiError.match(/component[:\s]+['"]?([^'"]+)['"]?/i);
    const component = componentMatch?.[1];

    if (component) {
      return `Unable to calculate emissions. The component '${component}' is missing emission data. Please contact support.`;
    }
    return 'Unable to calculate emissions. A component is missing emission data. Please contact support.';
  }

  // Missing emission factor errors
  if (apiError.toLowerCase().includes('missing emission factor')) {
    const componentMatch = apiError.match(/for[:\s]+['"]?([^'"]+)['"]?/i);
    const component = componentMatch?.[1];

    if (component) {
      return `Unable to calculate emissions. No emission factor found for '${component}'. Please contact support.`;
    }
    return 'Unable to calculate emissions. Missing emission factor data. Please contact support.';
  }

  // Product not found errors
  if (apiError.toLowerCase().includes('product not found')) {
    return 'The selected product could not be found. Please select a valid product and try again.';
  }

  // Invalid BOM errors
  if (
    apiError.toLowerCase().includes('invalid bom') ||
    apiError.toLowerCase().includes('invalid bill of materials')
  ) {
    return 'The Bill of Materials contains invalid data. Please review your component selections and quantities.';
  }

  // Empty BOM errors
  if (
    apiError.toLowerCase().includes('empty bom') ||
    apiError.toLowerCase().includes('no components')
  ) {
    return 'The Bill of Materials is empty. Please add at least one component before calculating.';
  }

  // Calculation failed (generic)
  if (apiError.toLowerCase().includes('calculation failed')) {
    return 'The calculation could not be completed. Please verify your data and try again, or contact support if the problem persists.';
  }

  // PRIORITY 2: HTTP status and network errors (medium specificity)

  // Network errors
  if (
    apiError.toLowerCase().includes('network error') ||
    apiError.toLowerCase().includes('failed to fetch') ||
    apiError.toLowerCase().includes('network request failed')
  ) {
    return 'Unable to connect to the server. Please check your internet connection and try again.';
  }

  // Authorization errors
  if (
    apiError.toLowerCase().includes('unauthorized') ||
    apiError.toLowerCase().includes('401') ||
    apiError.toLowerCase().includes('forbidden') ||
    apiError.toLowerCase().includes('403')
  ) {
    return 'You do not have permission to perform this action. Please contact support.';
  }

  // Rate limiting
  if (apiError.toLowerCase().includes('rate limit') || apiError.toLowerCase().includes('429')) {
    return 'Too many requests. Please wait a moment and try again.';
  }

  // Server errors (5xx)
  if (
    apiError.toLowerCase().includes('internal server error') ||
    apiError.toLowerCase().includes('500') ||
    apiError.toLowerCase().includes('503')
  ) {
    return 'The server encountered an error. Please try again later or contact support if the problem persists.';
  }

  // Database errors
  if (apiError.toLowerCase().includes('database error')) {
    return 'A database error occurred. Please try again later or contact support.';
  }

  // Validation errors
  if (apiError.toLowerCase().includes('validation error')) {
    return 'The request contains invalid data. Please review your inputs and try again.';
  }

  // PRIORITY 3: Timeout errors (least specific - check last)
  // Timeout errors are checked last because they're generic and could co-occur with more specific errors
  if (apiError.toLowerCase().includes('timeout')) {
    return 'The calculation is taking longer than expected. The server may be busy. Please try again in a few moments.';
  }

  // Default fallback
  return 'An unexpected error occurred during calculation. Please try again or contact support if the problem persists.';
}
