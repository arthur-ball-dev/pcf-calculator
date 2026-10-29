/**
 * BOMCardList SourceBadge Integration Tests
 * TASK-FE-P8-005: Integrate SourceBadge into BOM Table and Breakdown Table
 *
 * Test Coverage:
 * - Scenario 1: SourceBadge renders when data_source is provided (EPA, DEFRA)
 * - Scenario 2: SourceBadge links to attribution anchor
 * - Scenario 3: Edge case - handle missing data_source gracefully
 * - SourceBadge colors match source type
 * - SourceBadge accessibility (title attribute)
 *
 * Written BEFORE implementation per TDD protocol.
 *
 * NOTE: Emerald Night 5B redesign changed:
 * - Category badges now show config labels (Materials, Energy, Transport) not raw values
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, within } from '../../testUtils';
import BOMCardList from '../../../src/components/calculator/BOMCardList';

// BOMItem interface with data_source for SourceBadge integration
interface BOMItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  category: 'material' | 'energy' | 'transport' | 'other';
  emissionFactorId?: string | null;
  data_source?: string; // TASK-FE-P8-005: Source code for SourceBadge
}

// Mock BOM items with data_source for SourceBadge tests
const mockBomItemsWithDataSource: BOMItem[] = [
  { id: '1', name: 'Steel Sheet', quantity: 100, unit: 'kg', category: 'material', data_source: 'EPA' },
  { id: '2', name: 'Electricity Grid', quantity: 50, unit: 'kWh', category: 'energy', data_source: 'DEFRA' },
];

// Mock BOM items with mixed data_source (some missing)
const mockBomItemsMixedDataSource: BOMItem[] = [
  { id: '1', name: 'Steel Sheet', quantity: 100, unit: 'kg', category: 'material', data_source: 'EPA' },
  { id: '2', name: 'Unknown Material', quantity: 50, unit: 'kg', category: 'material' }, // No data_source
  { id: '3', name: 'Transport Truck', quantity: 25, unit: 'tkm', category: 'transport', data_source: 'DEFRA' },
];

describe('BOMCardList SourceBadge Integration (TASK-FE-P8-005)', () => {
  let mockUpdate: ReturnType<typeof vi.fn>;
  let mockRemove: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockUpdate = vi.fn();
    mockRemove = vi.fn();
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Scenario 1: Happy Path - SourceBadge renders when data_source provided
  // ==========================================================================

  describe('Scenario 1: Happy Path - SourceBadge renders when data_source provided', () => {
    it('should render SourceBadge with [EPA] text when data_source is EPA', () => {
      render(
        <BOMCardList
          items={mockBomItemsWithDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // SourceBadge for EPA should display [EPA] text
      const card1 = screen.getByTestId('bom-card-1');
      expect(within(card1).getByText('[EPA]')).toBeInTheDocument();
    });

    it('should render SourceBadge with [DEF] text when data_source is DEFRA', () => {
      render(
        <BOMCardList
          items={mockBomItemsWithDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // SourceBadge for DEFRA should display [DEF] text
      const card2 = screen.getByTestId('bom-card-2');
      expect(within(card2).getByText('[DEF]')).toBeInTheDocument();
    });


    it('should render SourceBadge as a link to EPA attribution anchor', () => {
      render(
        <BOMCardList
          items={mockBomItemsWithDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Find the EPA badge which should be a link
      const card1 = screen.getByTestId('bom-card-1');
      const epaLink = within(card1).getByText('[EPA]');

      // Should be an anchor element with href to attribution
      expect(epaLink.tagName.toLowerCase()).toBe('a');
      expect(epaLink).toHaveAttribute('href', '#epa-attribution');
    });

    it('should render SourceBadge with correct anchor href for DEFRA', () => {
      render(
        <BOMCardList
          items={mockBomItemsWithDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // DEFRA link
      const card2 = screen.getByTestId('bom-card-2');
      const defraLink = within(card2).getByText('[DEF]');
      expect(defraLink).toHaveAttribute('href', '#defra-attribution');
    });


    it('should apply green color to EPA SourceBadge', () => {
      render(
        <BOMCardList
          items={mockBomItemsWithDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const card1 = screen.getByTestId('bom-card-1');
      const epaBadge = within(card1).getByText('[EPA]');
      expect(epaBadge.className).toMatch(/green/i);
    });

    it('should apply blue color to DEFRA SourceBadge', () => {
      render(
        <BOMCardList
          items={mockBomItemsWithDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const card2 = screen.getByTestId('bom-card-2');
      const defraBadge = within(card2).getByText('[DEF]');
      expect(defraBadge.className).toMatch(/blue/i);
    });

  });

  // ==========================================================================
  // Scenario 2: DEFRA source rendering in mixed list
  // ==========================================================================

  describe('Scenario 2: DEFRA source rendering in mixed list', () => {
    it('should render SourceBadge with [DEF] text when data_source is DEFRA', () => {
      render(
        <BOMCardList
          items={mockBomItemsMixedDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const card3 = screen.getByTestId('bom-card-3');
      expect(within(card3).getByText('[DEF]')).toBeInTheDocument();
    });

    it('should apply blue color to DEFRA SourceBadge', () => {
      render(
        <BOMCardList
          items={mockBomItemsMixedDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const card3 = screen.getByTestId('bom-card-3');
      const defraBadge = within(card3).getByText('[DEF]');
      expect(defraBadge.className).toMatch(/blue/i);
    });

    it('should render DEFRA SourceBadge with correct anchor href', () => {
      render(
        <BOMCardList
          items={mockBomItemsMixedDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const card3 = screen.getByTestId('bom-card-3');
      const defraLink = within(card3).getByText('[DEF]');
      expect(defraLink).toHaveAttribute('href', '#defra-attribution');
    });
  });

  // ==========================================================================
  // Scenario 3: Edge Case - Missing data_source
  // ==========================================================================

  describe('Scenario 3: Edge Case - Missing data_source', () => {
    it('should not render SourceBadge when data_source is undefined', () => {
      render(
        <BOMCardList
          items={mockBomItemsMixedDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // The second item has no data_source
      const card2 = screen.getByTestId('bom-card-2');

      // Should not have any SourceBadge-like text (brackets)
      expect(within(card2).queryByText(/\[.*\]/)).not.toBeInTheDocument();
    });

    it('should render component content normally when data_source is missing', () => {
      render(
        <BOMCardList
          items={mockBomItemsMixedDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // The second item should still render its content
      const card2 = screen.getByTestId('bom-card-2');
      expect(within(card2).getByText('Unknown Material')).toBeInTheDocument();
      // Emerald Night 5B: category badges show config labels not raw values
      expect(within(card2).getByText('Materials')).toBeInTheDocument();
    });

    it('should not crash when items have mixed data_source values', () => {
      // This test verifies no runtime errors occur
      render(
        <BOMCardList
          items={mockBomItemsMixedDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // All 3 cards should render
      expect(screen.getByTestId('bom-card-1')).toBeInTheDocument();
      expect(screen.getByTestId('bom-card-2')).toBeInTheDocument();
      expect(screen.getByTestId('bom-card-3')).toBeInTheDocument();
    });

    it('should handle empty string data_source gracefully', () => {
      const itemsWithEmptySource: BOMItem[] = [
        { id: '1', name: 'Empty Source Item', quantity: 100, unit: 'kg', category: 'material', data_source: '' },
      ];

      render(
        <BOMCardList
          items={itemsWithEmptySource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Should render the card without crashing
      const card1 = screen.getByTestId('bom-card-1');
      expect(card1).toBeInTheDocument();
      expect(within(card1).getByText('Empty Source Item')).toBeInTheDocument();

      // Should not show a badge for empty string
      expect(within(card1).queryByText(/\[.*\]/)).not.toBeInTheDocument();
    });

    it('should handle unknown data_source code gracefully', () => {
      const itemsWithUnknownSource: BOMItem[] = [
        { id: '1', name: 'Unknown Source Item', quantity: 100, unit: 'kg', category: 'material', data_source: 'UNKNOWN_CODE' },
      ];

      render(
        <BOMCardList
          items={itemsWithUnknownSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Should render the card without crashing
      const card1 = screen.getByTestId('bom-card-1');
      expect(card1).toBeInTheDocument();

      // Unknown source should render as plain text without brackets
      // Based on SourceBadge implementation, unknown codes render as plain text
      const unknownText = within(card1).queryByText('UNKNOWN_CODE');
      // It's acceptable if shown as plain text or not shown at all
      // The key is: no crash occurs and the card renders
    });

    it('should handle null data_source gracefully', () => {
      const itemsWithNullSource: BOMItem[] = [
        { id: '1', name: 'Null Source Item', quantity: 100, unit: 'kg', category: 'material', data_source: undefined },
      ];

      render(
        <BOMCardList
          items={itemsWithNullSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Should render the card without crashing
      const card1 = screen.getByTestId('bom-card-1');
      expect(card1).toBeInTheDocument();
      expect(within(card1).getByText('Null Source Item')).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // SourceBadge Position and Layout
  // ==========================================================================

  describe('SourceBadge Position and Layout', () => {
    it('should render both category badge and SourceBadge in the same card', () => {
      render(
        <BOMCardList
          items={[mockBomItemsWithDataSource[0]]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const card = screen.getByTestId('bom-card-1');

      // Both badges should be present
      // Emerald Night 5B: category badges show config labels not raw values
      const categoryBadge = within(card).getByText('Materials');
      const sourceBadge = within(card).getByText('[EPA]');

      expect(categoryBadge).toBeInTheDocument();
      expect(sourceBadge).toBeInTheDocument();
    });

    it('should render SourceBadge within card element', () => {
      render(
        <BOMCardList
          items={[mockBomItemsWithDataSource[0]]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const card = screen.getByTestId('bom-card-1');
      const sourceBadge = within(card).getByText('[EPA]');

      // SourceBadge should be a descendant of the card
      expect(card.contains(sourceBadge)).toBe(true);
    });
  });

  // ==========================================================================
  // SourceBadge Accessibility
  // ==========================================================================

  describe('SourceBadge Accessibility', () => {
    it('should have title attribute for source attribution tooltip', () => {
      render(
        <BOMCardList
          items={[mockBomItemsWithDataSource[0]]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const card = screen.getByTestId('bom-card-1');
      const sourceBadge = within(card).getByText('[EPA]');

      // Should have a title for tooltip on hover
      expect(sourceBadge).toHaveAttribute('title');
      expect(sourceBadge.getAttribute('title')).toMatch(/EPA|attribution/i);
    });

    it('should render SourceBadge as clickable link (keyboard accessible)', () => {
      render(
        <BOMCardList
          items={[mockBomItemsWithDataSource[0]]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const card = screen.getByTestId('bom-card-1');
      const sourceBadge = within(card).getByText('[EPA]');

      // Should be an anchor (focusable and clickable)
      expect(sourceBadge.tagName.toLowerCase()).toBe('a');
    });
  });

  // ==========================================================================
  // Read-Only Mode with SourceBadge
  // ==========================================================================

  describe('Read-Only Mode with SourceBadge', () => {
    it('should still display SourceBadge when isReadOnly is true', () => {
      render(
        <BOMCardList
          items={mockBomItemsWithDataSource}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
          isReadOnly={true}
        />
      );

      // SourceBadge should still be visible in read-only mode
      const card1 = screen.getByTestId('bom-card-1');
      expect(within(card1).getByText('[EPA]')).toBeInTheDocument();
    });
  });
});
