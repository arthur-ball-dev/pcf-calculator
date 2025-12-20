import { useState, useEffect } from 'react';

/**
 * Custom hook for responsive design that tracks media query matches.
 * Uses window.matchMedia API with SSR safety.
 *
 * @param query - CSS media query string (e.g., '(max-width: 640px)')
 * @returns boolean - true if media query matches, false otherwise
 *
 * @example
 * const isMobile = useMediaQuery('(max-width: 640px)');
 * const isLandscape = useMediaQuery('(orientation: landscape)');
 */
export function useMediaQuery(query: string): boolean {
  // SSR safety: default to false when window is undefined
  // Don't call matchMedia during initialization to avoid double calls
  const [matches, setMatches] = useState<boolean>(false);

  useEffect(() => {
    // SSR safety check
    if (typeof window === 'undefined') {
      return;
    }

    const mediaQueryList = window.matchMedia(query);

    // Handler for media query changes
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // Set initial value
    setMatches(mediaQueryList.matches);

    // Modern browsers
    mediaQueryList.addEventListener('change', handleChange);

    // Cleanup
    return () => {
      mediaQueryList.removeEventListener('change', handleChange);
    };
  }, [query]);

  return matches;
}

export default useMediaQuery;
