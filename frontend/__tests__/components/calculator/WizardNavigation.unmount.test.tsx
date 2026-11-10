/**
 * WizardNavigation: a Next click whose deferred navigation is still pending when the
 * component unmounts must not run after it.
 *
 * CI (PRs #116 and #117) failed with an unhandled "ReferenceError: window is not
 * defined" from WizardNavigation.tsx: handleNext schedules goNext() two animation
 * frames later and setIsNavigating(false) 100 ms after that, and neither was
 * cancelled on unmount, so they fired after the test environment was torn down.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '../../testUtils';
import WizardNavigation from '@/components/calculator/WizardNavigation';
import { useWizardStore } from '@/store/wizardStore';

describe('WizardNavigation after unmount', () => {
  const goNext = vi.fn();

  beforeEach(() => {
    vi.useFakeTimers({
      toFake: ['setTimeout', 'clearTimeout', 'requestAnimationFrame', 'cancelAnimationFrame'],
    });
    goNext.mockClear();
    useWizardStore.setState({ currentStep: 'select', canProceed: true, canGoBack: false, goNext });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('runs the deferred navigation while mounted', () => {
    const setIsNavigating = vi.fn();
    render(<WizardNavigation isNavigating={false} setIsNavigating={setIsNavigating} />);

    fireEvent.click(screen.getByRole('button', { name: 'Next step' }));
    vi.advanceTimersByTime(200);

    expect(goNext).toHaveBeenCalledTimes(1);
    expect(setIsNavigating.mock.calls).toEqual([[true], [false]]);
  });

  it('does not navigate when unmounted before the animation frames run', () => {
    const setIsNavigating = vi.fn();
    const { unmount } = render(
      <WizardNavigation isNavigating={false} setIsNavigating={setIsNavigating} />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Next step' }));
    unmount();
    vi.advanceTimersByTime(200);

    expect(goNext).not.toHaveBeenCalled();
    expect(setIsNavigating.mock.calls).toEqual([[true]]);
  });

  it('does not reset the navigating flag when unmounted during the 100 ms delay', () => {
    const setIsNavigating = vi.fn();
    const { unmount } = render(
      <WizardNavigation isNavigating={false} setIsNavigating={setIsNavigating} />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Next step' }));
    // Two animation frames (about 16 ms each with fake timers), not the 100 ms timer.
    vi.advanceTimersByTime(40);
    expect(goNext).toHaveBeenCalledTimes(1);

    unmount();
    vi.advanceTimersByTime(200);

    expect(setIsNavigating.mock.calls).toEqual([[true]]);
  });
});
