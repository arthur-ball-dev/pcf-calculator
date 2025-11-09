/**
 * useAnnouncer Hook
 *
 * TASK-FE-010: Screen Reader Announcement Hook
 *
 * Provides a function to announce messages to screen readers using an aria-live region.
 * The announcer element is created in the document body and is visually hidden but
 * accessible to assistive technologies.
 *
 * Usage:
 * ```typescript
 * const { announce } = useAnnouncer();
 * announce('Step 2 of 4: Edit BOM');
 * ```
 *
 * WCAG 2.1 AA Requirements:
 * - Provides screen reader announcements for dynamic content changes
 * - Uses aria-live="polite" for non-intrusive announcements
 * - Uses aria-atomic="true" for complete message reading
 * - Visually hidden with sr-only class
 */

import { useEffect, useRef, useCallback } from 'react';

export interface AnnouncerReturn {
  announce: (message: string) => void;
}

/**
 * Custom hook for screen reader announcements
 *
 * Creates an aria-live region for announcing dynamic content changes to screen readers.
 * The announcer element is appended to document.body and removed on unmount.
 *
 * @returns Object with announce function
 */
export function useAnnouncer(): AnnouncerReturn {
  const announcerRef = useRef<HTMLDivElement | null>(null);

  /**
   * Create and append announcer element to document body
   */
  useEffect(() => {
    // Create announcer div
    const announcer = document.createElement('div');

    // Set ARIA attributes for screen reader announcement
    announcer.setAttribute('role', 'status');
    announcer.setAttribute('aria-live', 'polite');
    announcer.setAttribute('aria-atomic', 'true');

    // Add sr-only class for visual hiding
    announcer.className = 'sr-only';

    // Append to body
    document.body.appendChild(announcer);

    // Store reference
    announcerRef.current = announcer;

    // Cleanup: remove announcer on unmount
    return () => {
      if (announcerRef.current && announcerRef.current.parentNode) {
        announcerRef.current.parentNode.removeChild(announcerRef.current);
      }
      announcerRef.current = null;
    };
  }, []);

  /**
   * Announce a message to screen readers
   *
   * Updates the text content of the aria-live region, which triggers
   * screen readers to announce the new message.
   *
   * @param message - Message to announce to screen readers
   */
  const announce = useCallback((message: string) => {
    if (announcerRef.current) {
      announcerRef.current.textContent = message;
    }
  }, []);

  return { announce };
}
