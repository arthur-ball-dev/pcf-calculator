import { useState, useEffect, useMemo } from 'react';

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
  // One MediaQueryList per query. Its current value is read during render, so the first render is
  // already right; the previous version set it from an effect and rendered once more (#162).
  // No matchMedia (SSR, some test environments) reads as "no match".
  const mediaQueryList = useMemo(
    () => (typeof window !== 'undefined' && typeof window.matchMedia === 'function'
      ? window.matchMedia(query)
      : null),
    [query],
  );

  const [matches, setMatches] = useState(() => mediaQueryList?.matches ?? false);
  // A new query: take its current value straight away, during render
  const [trackedList, setTrackedList] = useState(mediaQueryList);
  if (mediaQueryList !== trackedList) {
    setTrackedList(mediaQueryList);
    setMatches(mediaQueryList?.matches ?? false);
  }

  // Later changes arrive as events
  useEffect(() => {
    if (!mediaQueryList) return;
    const handleChange = (event: MediaQueryListEvent) => setMatches(event.matches);
    mediaQueryList.addEventListener('change', handleChange);
    return () => mediaQueryList.removeEventListener('change', handleChange);
  }, [mediaQueryList]);

  return matches;
}

export default useMediaQuery;
