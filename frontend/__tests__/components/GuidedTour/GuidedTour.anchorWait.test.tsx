/**
 * GuidedTour anchor wait tests
 *
 * TASK-FE-FIX-001: The tour must auto-start for first-time visitors even when
 * the data-tour anchors render after a loading state (e.g. ProductList shows a
 * skeleton while emission factors load). Previously the anchors were checked
 * once, 150 ms after mount, so a slow network meant no tour at all.
 */

import { useEffect, useState } from 'react';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '../../testUtils';
import { TourProvider } from '@/contexts/TourContext';
import { GuidedTour } from '@/components/Tour/GuidedTour';
import { TOUR_STEPS } from '@/config/tourSteps';

// Replace react-joyride with a stub that exposes which steps it was given
vi.mock('react-joyride', () => ({
  default: ({ steps }: { steps: Array<{ target: string }> }) => (
    <div data-testid="joyride-stub">{steps.map((s) => s.target).join(',')}</div>
  ),
}));

/** Renders a skeleton first, then the product-select anchor after `delayMs` */
function LateAnchors({ delayMs }: { delayMs: number }) {
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    const id = setTimeout(() => setLoaded(true), delayMs);
    return () => clearTimeout(id);
  }, [delayMs]);
  return loaded ? (
    <div data-tour="product-select">Product search</div>
  ) : (
    <div data-testid="skeleton">Loading...</div>
  );
}

function renderTour(children: React.ReactNode) {
  return render(
    <TourProvider>
      {children}
      <GuidedTour />
    </TourProvider>
  );
}

describe('TASK-FE-FIX-001: GuidedTour waits for data-tour anchors', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  test('starts the tour when anchors are already rendered', async () => {
    renderTour(<div data-tour="product-select">Product search</div>);

    const stub = await screen.findByTestId('joyride-stub');
    expect(stub).toHaveTextContent('[data-tour="product-select"]');
  });

  test('starts the tour when anchors appear after a loading state', async () => {
    renderTour(<LateAnchors delayMs={1500} />);

    expect(screen.getByTestId('skeleton')).toBeInTheDocument();
    await waitFor(
      () => expect(screen.getByTestId('joyride-stub')).toHaveTextContent('[data-tour="product-select"]'),
      { timeout: 4000 }
    );
  });

  test('does not start the tour for returning users', async () => {
    window.localStorage.setItem('pcf-calculator-tour-completed', 'true');
    renderTour(<LateAnchors delayMs={200} />);

    await screen.findByText('Product search');
    await new Promise((resolve) => setTimeout(resolve, 500));
    expect(screen.queryByTestId('joyride-stub')).not.toBeInTheDocument();
  });

  test('renders nothing when no anchors ever appear', async () => {
    renderTour(<div>No tour targets here</div>);

    await new Promise((resolve) => setTimeout(resolve, 500));
    expect(screen.queryByTestId('joyride-stub')).not.toBeInTheDocument();
  });
});

describe('TASK-FE-FIX-001: tour step title contrast', () => {
  test('step title sets a dark text color for the white tooltip', () => {
    render(<>{TOUR_STEPS[0].content}</>);

    const title = screen.getByRole('heading', { name: /Step 1: Select a Product/ });
    expect(title).toHaveClass('text-gray-900');
  });
});
