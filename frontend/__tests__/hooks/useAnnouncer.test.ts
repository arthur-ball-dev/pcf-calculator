/**
 * useAnnouncer Hook Tests
 *
 * TASK-FE-010: Screen Reader Announcement Hook
 *
 * Tests for the useAnnouncer custom hook that provides screen reader announcements
 * via aria-live regions.
 *
 * TDD Protocol: Test written BEFORE implementation
 */

import { describe, test, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, act, cleanup } from '@testing-library/react';
import { useAnnouncer } from '@/hooks/useAnnouncer';

describe('useAnnouncer', () => {
  beforeEach(() => {
    // Clean up any existing announcer elements
    document.body.innerHTML = '';
  });

  afterEach(() => {
    cleanup();
  });

  test('creates aria-live region in document body', () => {
    renderHook(() => useAnnouncer());

    // Should create a div with role="status" and aria-live="polite"
    const announcer = document.querySelector('[role="status"]');
    expect(announcer).toBeInTheDocument();
    expect(announcer).toHaveAttribute('aria-live', 'polite');
    expect(announcer).toHaveAttribute('aria-atomic', 'true');
  });

  test('announcer element has sr-only class for visual hiding', () => {
    renderHook(() => useAnnouncer());

    const announcer = document.querySelector('[role="status"]');
    expect(announcer).toHaveClass('sr-only');
  });

  test('announce function updates announcer text content', () => {
    const { result } = renderHook(() => useAnnouncer());

    act(() => {
      result.current.announce('Test announcement');
    });

    const announcer = document.querySelector('[role="status"]');
    expect(announcer).toHaveTextContent('Test announcement');
  });

  test('multiple announcements update the same element', () => {
    const { result } = renderHook(() => useAnnouncer());

    act(() => {
      result.current.announce('First message');
    });

    let announcer = document.querySelector('[role="status"]');
    expect(announcer).toHaveTextContent('First message');

    act(() => {
      result.current.announce('Second message');
    });

    announcer = document.querySelector('[role="status"]');
    expect(announcer).toHaveTextContent('Second message');
  });

  test('announcer element is removed on unmount', () => {
    const { unmount } = renderHook(() => useAnnouncer());

    // Verify announcer exists
    let announcer = document.querySelector('[role="status"]');
    expect(announcer).toBeInTheDocument();

    // Unmount hook
    unmount();

    // Verify announcer is removed
    announcer = document.querySelector('[role="status"]');
    expect(announcer).not.toBeInTheDocument();
  });

  test('only one announcer element is created per hook instance', () => {
    renderHook(() => useAnnouncer());

    const announcers = document.querySelectorAll('[role="status"]');
    expect(announcers).toHaveLength(1);
  });

  test('multiple hook instances create separate announcer elements', () => {
    renderHook(() => useAnnouncer());
    renderHook(() => useAnnouncer());

    const announcers = document.querySelectorAll('[role="status"]');
    expect(announcers.length).toBeGreaterThanOrEqual(2);
  });

  test('announce function handles empty strings', () => {
    const { result } = renderHook(() => useAnnouncer());

    act(() => {
      result.current.announce('');
    });

    const announcer = document.querySelector('[role="status"]');
    expect(announcer).toHaveTextContent('');
  });

  test('announce function is stable across re-renders', () => {
    const { result, rerender } = renderHook(() => useAnnouncer());

    const firstAnnounce = result.current.announce;

    rerender();

    const secondAnnounce = result.current.announce;

    // Function reference should be the same
    expect(firstAnnounce).toBe(secondAnnounce);
  });

  test('announcer supports long messages', () => {
    const { result } = renderHook(() => useAnnouncer());

    const longMessage =
      'This is a very long announcement message that should still be properly announced to screen readers without any issues or truncation.';

    act(() => {
      result.current.announce(longMessage);
    });

    const announcer = document.querySelector('[role="status"]');
    expect(announcer).toHaveTextContent(longMessage);
  });

  test('announcer supports special characters and HTML entities', () => {
    const { result } = renderHook(() => useAnnouncer());

    const messageWithSpecialChars = 'Step 2 of 4: Edit BOM <>&"';

    act(() => {
      result.current.announce(messageWithSpecialChars);
    });

    const announcer = document.querySelector('[role="status"]');
    // textContent should contain the raw text, not HTML-encoded
    expect(announcer).toHaveTextContent(messageWithSpecialChars);
  });
});
