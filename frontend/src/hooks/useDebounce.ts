/**
 * useDebounce Hook
 * TASK-FE-P5-004: Enhanced Product Search
 *
 * Generic debounce hook with configurable delay.
 * Returns a debounced value that only updates after the specified delay
 * has passed without the input value changing.
 */

import { useState, useEffect } from 'react';

/**
 * Debounce a value by a specified delay
 *
 * @param value - The value to debounce
 * @param delay - The debounce delay in milliseconds (default: 300ms)
 * @returns The debounced value
 *
 * @example
 * ```tsx
 * const [searchQuery, setSearchQuery] = useState('');
 * const debouncedQuery = useDebounce(searchQuery, 300);
 *
 * // debouncedQuery will only update 300ms after the last change to searchQuery
 * useEffect(() => {
 *   if (debouncedQuery) {
 *     // Perform search with debouncedQuery
 *   }
 * }, [debouncedQuery]);
 * ```
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  // Use function form of useState to properly handle function initial values
  // If we pass a function directly, React will call it as an initializer
  const [debouncedValue, setDebouncedValue] = useState<T>(() => value);

  useEffect(() => {
    // Set up the timeout to update debounced value after delay
    const handler = setTimeout(() => {
      // Use function form of setState to properly handle function values
      // If we pass a function directly, React will call it as a state updater
      setDebouncedValue(() => value);
    }, delay);

    // Cleanup function: clear timeout on unmount or when value/delay changes
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default useDebounce;
