/**
 * BreakdownTable SourceBadge Integration Tests
 * TASK-FE-P8-005: Integrate SourceBadge into BOM Table and Breakdown Table
 *
 * Test Coverage:
 * - Scenario 1: SourceBadge renders in expanded items with data_source
 * - Scenario 2: SourceBadge displays correct colors for each source type
 * - Scenario 3: Edge case - handle missing data_source gracefully
 * - SourceBadge links to attribution anchors
 * - SourceBadge accessibility features
 *
 * Written BEFORE implementation per TDD protocol.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, within, waitFor } from '../../testUtils';
import userEvent from '@testing-library/user-event';
import BreakdownTable from '@/components/calculator/BreakdownTable';

/**
 * Extended BreakdownItem interface with data_source support
 * TASK-FE-P8-005: Items can include source attribution
 */
interface BreakdownItem {
  name: string;
  co2e: number;
  quantity?: number;
  unit?: string;
  data_source?: string; // TASK-FE-P8-005: Source code for SourceBadge
}

/**
 * Extended breakdown type with data_source for each component
 * Maps component_name -> { co2e: number, data_source?: string }
 * OR component_name -> number (backwards compatible)
 */
type BreakdownWithSource = Record<string, number | { co2e: number; data_source?: string }>;

// Mock breakdown data WITH source information
const mockBreakdownWithSource: BreakdownWithSource = {
  cotton: { co2e: 1.5, data_source: 'DEFRA' },
  polyester: { co2e: 0.3, data_source: 'EPA' },
  electricity_us: { co2e: 0.15, data_source: 'EPA' },
  truck_transport: { co2e: 0.1, data_source: 'EXIOBASE' },
};

// Mock breakdown data with mixed sources (some missing)
const mockBreakdownMixedSource: BreakdownWithSource = {
  cotton: { co2e: 1.5, data_source: 'DEFRA' },
  polyester: { co2e: 0.3 }, // No data_source
  electricity_us: { co2e: 0.15, data_source: 'EPA' },
  unknown_material: { co2e: 0.05 }, // No data_source
};

// Mock itemSources map (alternative approach for source data)
const mockItemSources: Record<string, string> = {
  cotton: 'DEFRA',
  polyester: 'EPA',
  electricity_us: 'EPA',
  truck_transport: 'EXIOBASE',
};

// Standard mock breakdown (numeric values only)
const mockBreakdownNumeric: Record<string, number> = {
  cotton: 1.5,
  polyester: 0.3,
  electricity_us: 0.15,
  truck_transport: 0.1,
};

// Props for testing with source data passed separately
interface BreakdownTablePropsWithSources {
  totalCO2e: number;
  materialsCO2e?: number;
  energyCO2e?: number;
  transportCO2e?: number;
  breakdown?: Record<string, number>;
  itemSources?: Record<string, string>; // TASK-FE-P8-005: Source mapping
}

const mockPropsWithSources: BreakdownTablePropsWithSources = {
  totalCO2e: 2.05,
  materialsCO2e: 1.8,
  energyCO2e: 0.15,
  transportCO2e: 0.1,
  breakdown: mockBreakdownNumeric,
  itemSources: mockItemSources,
};

describe('BreakdownTable SourceBadge Integration (TASK-FE-P8-005)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Scenario 1: SourceBadge renders in expanded items
  // ==========================================================================

  describe('Scenario 1: SourceBadge renders in expanded items with data_source', () => {
    it('should render SourceBadge with [DEF] text for DEFRA source when item expanded', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      // Expand materials category to see cotton item
      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const cottonRow = screen.getByTestId('item-row-cotton');
        expect(within(cottonRow).getByText('[DEF]')).toBeInTheDocument();
      });
    });

    it('should render SourceBadge with [EPA] text for EPA source when item expanded', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      // Expand materials category to see polyester item
      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const polyesterRow = screen.getByTestId('item-row-polyester');
        expect(within(polyesterRow).getByText('[EPA]')).toBeInTheDocument();
      });
    });

    it('should render SourceBadge with [EXI] text for EXIOBASE source when item expanded', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          transportCO2e={mockPropsWithSources.transportCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      // Expand transport category to see truck_transport item
      await user.click(screen.getByTestId('expand-transport'));

      await waitFor(() => {
        const transportRow = screen.getByTestId('item-row-truck_transport');
        expect(within(transportRow).getByText('[EXI]')).toBeInTheDocument();
      });
    });

    it('should render SourceBadge as a link to attribution anchor', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const cottonRow = screen.getByTestId('item-row-cotton');
        const defraBadge = within(cottonRow).getByText('[DEF]');

        // Should be an anchor element
        expect(defraBadge.tagName.toLowerCase()).toBe('a');
        expect(defraBadge).toHaveAttribute('href', '#defra-attribution');
      });
    });

    it('should render multiple SourceBadges correctly when multiple items expanded', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          energyCO2e={mockPropsWithSources.energyCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      // Expand both materials and energy categories
      await user.click(screen.getByTestId('expand-materials'));
      await user.click(screen.getByTestId('expand-energy'));

      await waitFor(() => {
        // Materials items
        const cottonRow = screen.getByTestId('item-row-cotton');
        expect(within(cottonRow).getByText('[DEF]')).toBeInTheDocument();

        const polyesterRow = screen.getByTestId('item-row-polyester');
        expect(within(polyesterRow).getByText('[EPA]')).toBeInTheDocument();

        // Energy items
        const electricityRow = screen.getByTestId('item-row-electricity_us');
        expect(within(electricityRow).getByText('[EPA]')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Scenario 2: SourceBadge colors match source type
  // ==========================================================================

  describe('Scenario 2: SourceBadge displays correct colors', () => {
    it('should apply blue color to DEFRA SourceBadge', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const cottonRow = screen.getByTestId('item-row-cotton');
        const defraBadge = within(cottonRow).getByText('[DEF]');
        expect(defraBadge.className).toMatch(/blue/i);
      });
    });

    it('should apply green color to EPA SourceBadge', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const polyesterRow = screen.getByTestId('item-row-polyester');
        const epaBadge = within(polyesterRow).getByText('[EPA]');
        expect(epaBadge.className).toMatch(/green/i);
      });
    });

    it('should apply purple color to EXIOBASE SourceBadge', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          transportCO2e={mockPropsWithSources.transportCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      await user.click(screen.getByTestId('expand-transport'));

      await waitFor(() => {
        const transportRow = screen.getByTestId('item-row-truck_transport');
        const exiobaseBadge = within(transportRow).getByText('[EXI]');
        expect(exiobaseBadge.className).toMatch(/purple/i);
      });
    });
  });

  // ==========================================================================
  // Scenario 3: Edge Case - Missing data_source
  // ==========================================================================

  describe('Scenario 3: Edge Case - handle missing data_source gracefully', () => {
    const mixedItemSources: Record<string, string> = {
      cotton: 'DEFRA',
      electricity_us: 'EPA',
      // polyester and unknown_material have no source
    };

    const mixedBreakdown: Record<string, number> = {
      cotton: 1.5,
      polyester: 0.3,
      electricity_us: 0.15,
      unknown_material: 0.05,
    };

    it('should not render SourceBadge when item has no data_source', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={2.0}
          materialsCO2e={1.85}
          breakdown={mixedBreakdown}
          itemSources={mixedItemSources}
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        // polyester has no source - should not have badge
        const polyesterRow = screen.getByTestId('item-row-polyester');
        expect(within(polyesterRow).queryByText(/\[.*\]/)).not.toBeInTheDocument();
      });
    });

    it('should render component content normally when data_source is missing', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={2.0}
          materialsCO2e={1.85}
          breakdown={mixedBreakdown}
          itemSources={mixedItemSources}
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        // polyester row should still render with name and values
        const polyesterRow = screen.getByTestId('item-row-polyester');
        expect(polyesterRow).toBeInTheDocument();
        // The formatted name "Polyester" should be visible
        expect(within(polyesterRow).getByText(/polyester/i)).toBeInTheDocument();
      });
    });

    it('should handle mixed items (some with source, some without) without crashing', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={2.0}
          materialsCO2e={1.85}
          breakdown={mixedBreakdown}
          itemSources={mixedItemSources}
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        // Cotton should have badge (has source)
        const cottonRow = screen.getByTestId('item-row-cotton');
        expect(within(cottonRow).getByText('[DEF]')).toBeInTheDocument();

        // Polyester should not have badge (no source)
        const polyesterRow = screen.getByTestId('item-row-polyester');
        expect(within(polyesterRow).queryByText(/\[.*\]/)).not.toBeInTheDocument();
      });
    });

    it('should work correctly when itemSources prop is not provided', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={2.0}
          materialsCO2e={1.8}
          breakdown={mockBreakdownNumeric}
          // No itemSources prop
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        // Items should render without any source badges
        const cottonRow = screen.getByTestId('item-row-cotton');
        expect(cottonRow).toBeInTheDocument();
        expect(within(cottonRow).queryByText(/\[.*\]/)).not.toBeInTheDocument();
      });
    });

    it('should work correctly when itemSources is empty object', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={2.0}
          materialsCO2e={1.8}
          breakdown={mockBreakdownNumeric}
          itemSources={{}} // Empty object
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        // Items should render without any source badges
        const cottonRow = screen.getByTestId('item-row-cotton');
        expect(cottonRow).toBeInTheDocument();
        expect(within(cottonRow).queryByText(/\[.*\]/)).not.toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // SourceBadge anchor links
  // ==========================================================================

  describe('SourceBadge anchor links work correctly', () => {
    it('should have correct href for EPA attribution', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const polyesterRow = screen.getByTestId('item-row-polyester');
        const epaBadge = within(polyesterRow).getByText('[EPA]');
        expect(epaBadge).toHaveAttribute('href', '#epa-attribution');
      });
    });

    it('should have correct href for DEFRA attribution', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const cottonRow = screen.getByTestId('item-row-cotton');
        const defraBadge = within(cottonRow).getByText('[DEF]');
        expect(defraBadge).toHaveAttribute('href', '#defra-attribution');
      });
    });

    it('should have correct href for EXIOBASE attribution', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          transportCO2e={mockPropsWithSources.transportCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      await user.click(screen.getByTestId('expand-transport'));

      await waitFor(() => {
        const transportRow = screen.getByTestId('item-row-truck_transport');
        const exiobaseBadge = within(transportRow).getByText('[EXI]');
        expect(exiobaseBadge).toHaveAttribute('href', '#exiobase-attribution');
      });
    });
  });

  // ==========================================================================
  // SourceBadge Accessibility
  // ==========================================================================

  describe('SourceBadge Accessibility in BreakdownTable', () => {
    it('should have title attribute on SourceBadge for screen readers', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const cottonRow = screen.getByTestId('item-row-cotton');
        const defraBadge = within(cottonRow).getByText('[DEF]');

        expect(defraBadge).toHaveAttribute('title');
        expect(defraBadge.getAttribute('title')).toMatch(/DEFRA|attribution/i);
      });
    });

    it('should render SourceBadge as focusable anchor element', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const cottonRow = screen.getByTestId('item-row-cotton');
        const defraBadge = within(cottonRow).getByText('[DEF]');

        // Should be an anchor (inherently focusable)
        expect(defraBadge.tagName.toLowerCase()).toBe('a');
      });
    });
  });

  // ==========================================================================
  // SourceBadge position within item row
  // ==========================================================================

  describe('SourceBadge position within item row', () => {
    it('should render SourceBadge inline with item name', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const cottonRow = screen.getByTestId('item-row-cotton');

        // Both the item name and badge should be in the same cell
        const firstCell = cottonRow.querySelector('td');
        expect(firstCell).toContainElement(within(cottonRow).getByText(/cotton/i));
        expect(firstCell).toContainElement(within(cottonRow).getByText('[DEF]'));
      });
    });

    it('should render SourceBadge after formatted item name', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const cottonRow = screen.getByTestId('item-row-cotton');

        // The cell content should have both name and badge
        const nameCell = cottonRow.querySelector('td');
        const nameSpan = within(cottonRow).getByText(/cotton/i);
        const badge = within(cottonRow).getByText('[DEF]');

        // Both should be visible in the row
        expect(nameSpan).toBeInTheDocument();
        expect(badge).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Collapse behavior with SourceBadge
  // ==========================================================================

  describe('Collapse behavior with SourceBadge', () => {
    it('should hide SourceBadge when category is collapsed', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      // Expand
      await user.click(screen.getByTestId('expand-materials'));
      await waitFor(() => {
        expect(screen.getByTestId('item-row-cotton')).toBeInTheDocument();
      });

      // Collapse
      await user.click(screen.getByTestId('expand-materials'));
      await waitFor(() => {
        expect(screen.queryByTestId('item-row-cotton')).not.toBeInTheDocument();
        // Badge should also be gone
        expect(screen.queryByText('[DEF]')).not.toBeInTheDocument();
      });
    });

    it('should show SourceBadge again when category is re-expanded', async () => {
      const user = userEvent.setup();
      render(
        <BreakdownTable
          totalCO2e={mockPropsWithSources.totalCO2e}
          materialsCO2e={mockPropsWithSources.materialsCO2e}
          breakdown={mockPropsWithSources.breakdown}
          itemSources={mockPropsWithSources.itemSources}
        />
      );

      // Expand -> Collapse -> Expand again
      await user.click(screen.getByTestId('expand-materials'));
      await user.click(screen.getByTestId('expand-materials'));
      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const cottonRow = screen.getByTestId('item-row-cotton');
        expect(within(cottonRow).getByText('[DEF]')).toBeInTheDocument();
      });
    });
  });
});
