/**
 * EmissionsTreemap Component
 *
 * Hierarchical Scope 1/2/3 emissions breakdown visualization with drill-down navigation.
 * Uses Nivo TreeMap for professional-grade carbon footprint analysis.
 *
 * Features:
 * - GHG Protocol compliant colors
 * - Drill-down navigation with breadcrumb trail
 * - Accessible hidden data table for screen readers
 * - Responsive design
 * - Performance optimized for up to 500 nodes
 *
 * TASK-UI-P5-001: Advanced Visualizations (Treemap + Area)
 */

import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { ResponsiveTreeMap } from '@nivo/treemap';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChevronLeft } from 'lucide-react';

// ============================================================================
// GHG Protocol Colors
// ============================================================================

const SCOPE_COLORS: Record<string, string> = {
  'Scope 1': '#fa5252', // Red - Direct emissions
  'Scope 2': '#339af0', // Blue - Energy indirect
  'Scope 3': '#51cf66', // Green - Other indirect (updated from gray for better visibility)
};

const CATEGORY_COLORS = [
  '#ff6b6b', '#f06595', '#cc5de8', '#845ef7',
  '#5c7cfa', '#339af0', '#22b8cf', '#20c997',
  '#51cf66', '#94d82d', '#fcc419', '#ff922b',
];

// ============================================================================
// Types
// ============================================================================

export interface TreemapNode {
  name: string;
  value?: number;
  color?: string;
  children?: TreemapNode[];
  metadata?: {
    percentage?: number;
    trend?: 'up' | 'down' | 'stable';
    dataQuality?: 'high' | 'medium' | 'low';
    category?: string;
  };
}

export interface EmissionsTreemapProps {
  /** Hierarchical treemap data */
  data: TreemapNode | null | undefined;
  /** Unit label for values (default: 'kg CO2e') */
  unit?: string;
  /** Callback when a node is clicked */
  onNodeClick?: (node: TreemapNode, path: string[]) => void;
  /** Enable drill-down navigation (default: true) */
  enableDrillDown?: boolean;
  /** Additional CSS class */
  className?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Check if data is empty or invalid
 */
function isEmptyData(data: TreemapNode | null | undefined): boolean {
  if (!data) return true;
  if (!data.children) return true;
  if (data.children.length === 0) return true;
  return false;
}

/**
 * Format value for display with K/M suffixes
 */
function formatValue(value: number, unit: string): string {
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M ${unit}`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K ${unit}`;
  return `${value.toFixed(2)} ${unit}`;
}

/**
 * Assign colors to nodes based on scope or category
 */
function assignColors(node: TreemapNode, depth: number = 0): TreemapNode {
  let color = node.color;

  if (!color) {
    // Check for scope colors first
    if (SCOPE_COLORS[node.name]) {
      color = SCOPE_COLORS[node.name];
    } else {
      // Use category color palette
      color = CATEGORY_COLORS[depth % CATEGORY_COLORS.length];
    }
  }

  return {
    ...node,
    color,
    children: node.children?.map((child, i) => assignColors(child, i)),
  };
}

/**
 * Navigate to a specific path in the data hierarchy
 */
function getNodeAtPath(data: TreemapNode, path: string[]): TreemapNode {
  let node = data;
  for (const pathItem of path) {
    const child = node.children?.find((c) => c.name === pathItem);
    if (child) {
      node = child;
    } else {
      break;
    }
  }
  return node;
}

// ============================================================================
// Component
// ============================================================================

function EmissionsTreemap({
  data,
  unit = 'kg CO2e',
  onNodeClick,
  enableDrillDown = true,
  className,
}: EmissionsTreemapProps) {
  const [drillPath, setDrillPath] = useState<string[]>([]);
  const liveRegionRef = useRef<HTMLDivElement>(null);
  const prevDataRef = useRef<TreemapNode | null | undefined>(data);
  const containerRef = useRef<HTMLDivElement>(null);
  const prevDrillPathLength = useRef<number>(0);

  // Reset drill path when data changes
  useEffect(() => {
    // Compare by checking if the data name changed or if it's a completely different object
    if (
      data?.name !== prevDataRef.current?.name ||
      JSON.stringify(data) !== JSON.stringify(prevDataRef.current)
    ) {
      setDrillPath([]);
    }
    prevDataRef.current = data;
  }, [data]);

  // Focus management after drill-down: blur active element so tab starts from beginning
  useEffect(() => {
    if (drillPath.length !== prevDrillPathLength.current) {
      // Focus the container (tabIndex=-1 makes it focusable but not in tab order)
      // This resets focus so Tab will go to the first tabbable element
      if (containerRef.current) {
        containerRef.current.focus();
      }
    }
    prevDrillPathLength.current = drillPath.length;
  }, [drillPath.length]);

  // Get current data based on drill path
  const currentData = useMemo(() => {
    if (!data) return null;
    return getNodeAtPath(data, drillPath);
  }, [data, drillPath]);

  // Assign colors to nodes
  const coloredData = useMemo(() => {
    if (!currentData) return null;
    return assignColors(currentData);
  }, [currentData]);

  // Format value helper bound to unit
  const formatNodeValue = useCallback(
    (value: number) => formatValue(value, unit),
    [unit]
  );

  // Handle drill down
  const handleClick = useCallback(
    (node: { data: TreemapNode }) => {
      if (!enableDrillDown) return;

      const nodeData = node.data;

      // Only drill if node has children with items
      if (nodeData.children && nodeData.children.length > 0) {
        setDrillPath((prev) => [...prev, nodeData.name]);

        // Announce navigation to screen readers
        if (liveRegionRef.current) {
          liveRegionRef.current.textContent = `Navigated to ${nodeData.name}`;
        }
      }

      onNodeClick?.(nodeData, [...drillPath, nodeData.name]);
    },
    [enableDrillDown, drillPath, onNodeClick]
  );

  // Handle drill up
  const handleDrillUp = useCallback(() => {
    setDrillPath((prev) => prev.slice(0, -1));

    // Announce navigation to screen readers
    if (liveRegionRef.current) {
      liveRegionRef.current.textContent =
        drillPath.length === 1
          ? 'Returned to Overview'
          : `Returned to ${drillPath[drillPath.length - 2]}`;
    }
  }, [drillPath]);

  // Handle breadcrumb navigation
  const handleBreadcrumbClick = useCallback((index: number) => {
    if (index === 0) {
      // Overview clicked - go back to root
      setDrillPath([]);
    } else {
      // Navigate to specific level
      setDrillPath((prev) => prev.slice(0, index));
    }
  }, []);

  // Handle breadcrumb keyboard navigation
  const handleBreadcrumbKeyDown = useCallback(
    (index: number, event: React.KeyboardEvent) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        handleBreadcrumbClick(index);
      }
    },
    [handleBreadcrumbClick]
  );

  // Render empty state
  if (isEmptyData(data)) {
    return (
      <Card className={className} data-testid="emissions-treemap">
        <CardHeader>
          <CardTitle className="text-lg">Emissions Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className="h-[400px] flex items-center justify-center text-muted-foreground"
            data-testid="treemap-container"
            aria-label="Emissions breakdown treemap visualization"
          >
            <p>No emissions data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      ref={containerRef}
      className={className}
      data-testid="emissions-treemap"
      tabIndex={-1}
    >
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Emissions Breakdown</CardTitle>
        {drillPath.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDrillUp}
            data-testid="drill-up-button"
            aria-label={`Go back to ${drillPath.length === 1 ? 'Overview' : drillPath[drillPath.length - 2]}`}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back to {drillPath.length === 1 ? 'Overview' : drillPath[drillPath.length - 2]}
          </Button>
        )}
      </CardHeader>

      <CardContent>
        {/* Live region for screen reader announcements */}
        <div
          ref={liveRegionRef}
          className="sr-only"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        />

        {/* Breadcrumb */}
        {drillPath.length > 0 && (
          <nav
            className="text-sm text-muted-foreground mb-2"
            data-testid="breadcrumb"
            aria-label="Breadcrumb navigation"
          >
            {['Overview', ...drillPath].map((crumb, index) => (
              <span key={index}>
                {index > 0 && ' > '}
                <button
                  type="button"
                  onClick={() => handleBreadcrumbClick(index)}
                  onKeyDown={(e) => handleBreadcrumbKeyDown(index, e)}
                  className="hover:underline focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded px-1"
                  aria-label={`Navigate to ${crumb}`}
                >
                  {crumb}
                </button>
              </span>
            ))}
          </nav>
        )}

        {/* Treemap */}
        <div
          className="h-[400px]"
          style={{ height: '400px' }}
          data-testid="treemap-container"
          aria-label="Interactive emissions breakdown treemap. Use mouse to navigate nodes. Click to drill down into categories."
        >
          {coloredData && (
            <ResponsiveTreeMap
              data={coloredData}
              identity="name"
              value="value"
              valueFormat={(value) => formatNodeValue(value)}
              margin={{ top: 10, right: 10, bottom: 10, left: 10 }}
              labelSkipSize={40}
              labelTextColor={{ from: 'color', modifiers: [['darker', 3]] }}
              parentLabelPosition="left"
              parentLabelTextColor={{ from: 'color', modifiers: [['darker', 3]] }}
              borderColor={{ from: 'color', modifiers: [['darker', 0.3]] }}
              colors={{ datum: 'data.color' }}
              animate={true}
              motionConfig="gentle"
              onClick={handleClick}
              nodeOpacity={1}
              borderWidth={2}
              innerPadding={3}
              outerPadding={3}
              tile="squarify"
              tooltip={({ node }) => (
                <div
                  className="bg-white px-3 py-2 rounded shadow-lg border"
                  data-testid="treemap-tooltip"
                >
                  <strong>{node.id}</strong>
                  <div className="text-sm text-gray-600">
                    {formatNodeValue(node.value as number)}
                  </div>
                  {/* Show drill-down hint if enableDrillDown is true and node has children property */}
                  {enableDrillDown && node.data.children && (
                    <div className="text-xs text-gray-400 mt-1">
                      Click to drill down
                    </div>
                  )}
                </div>
              )}
            />
          )}
        </div>

        {/* Accessibility: Hidden data table */}
        <div
          className="sr-only"
          role="table"
          aria-label="Emissions breakdown data"
        >
          <div role="rowgroup">
            <div role="row">
              <span role="columnheader">Category</span>
              <span role="columnheader">Emissions</span>
            </div>
          </div>
          <div role="rowgroup">
            {coloredData?.children?.map((child) => (
              <div key={child.name} role="row">
                <span role="cell">{child.name}</span>
                <span role="cell">{formatNodeValue(child.value || 0)}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default EmissionsTreemap;