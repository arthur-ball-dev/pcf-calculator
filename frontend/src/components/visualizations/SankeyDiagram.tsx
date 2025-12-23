/**
 * SankeyDiagram Component
 *
 * Interactive Sankey diagram for visualizing carbon flow from materials
 * through manufacturing to final product using Nivo ResponsiveSankey.
 *
 * Features:
 * - Color coding by emission category
 * - Interactive tooltips with CO2e values
 * - Clickable category nodes for drill-down
 * - Responsive sizing with mobile optimization
 * - Horizontal scrolling for complex charts on mobile
 * - Empty/loading/error states
 * - WCAG 2.1 AA accessible
 *
 * TASK-FE-008: Nivo Sankey Implementation
 * TASK-FE-P8-002: Category Drill-Down click handler
 * TASK-FE-P7-013: Visualization Responsiveness
 * TASK-FE-P7-026: Eliminated TypeScript any usages
 */

import { useState, useMemo, useCallback } from 'react';
import { ResponsiveSankey } from '@nivo/sankey';
import { ArrowLeft } from 'lucide-react';
import { transformToSankeyData, transformToExpandedSankeyData } from '../../utils/sankeyTransform';
import SankeyTooltip from './SankeyTooltip';
import { ResponsiveChartContainer } from './ResponsiveChartContainer';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';
import { useBreakpoints, BREAKPOINTS } from '../../hooks/useBreakpoints';
import type { Calculation } from '../../types/store.types';
import type {
  PCFSankeyClickData,
  PCFSankeyNodeDatum,
  PCFSankeyLayerProps,
  isSankeyLink,
} from '../../types/nivo.d';

/**
 * Truncate label text for mobile display
 * @param text - Original label text
 * @param maxLength - Maximum characters before truncation
 * @returns Truncated text with ellipsis if needed
 */
function truncateLabel(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text;
  }
  return text.slice(0, maxLength) + '...';
}

/**
 * Split text into lines at word boundaries (including "/" as a break point)
 * Won't break words
 */
function wrapLabel(text: string, maxCharsPerLine: number): string[] {
  if (text.length <= maxCharsPerLine) {
    return [text];
  }

  // Split on spaces and "/" (keeping "/" with the preceding word)
  const parts = text.split(/(?<=\/)|(?= )/);
  const lines: string[] = [];
  let currentLine = '';

  for (const part of parts) {
    const trimmedPart = part.trim();
    if (!trimmedPart) continue;

    if (currentLine.length === 0) {
      currentLine = trimmedPart;
    } else if (currentLine.length + trimmedPart.length <= maxCharsPerLine) {
      currentLine += (part.startsWith(' ') ? ' ' : '') + trimmedPart;
    } else {
      lines.push(currentLine);
      currentLine = trimmedPart;
    }
  }

  if (currentLine.length > 0) {
    lines.push(currentLine);
  }

  return lines.length > 0 ? lines : [text];
}

/**
 * Create a custom labels layer factory that uses sankeyData for label lookup
 * @param labelMap - Map of node IDs to display labels
 * @param isMobile - Whether the viewport is mobile-sized
 */
function createLabelsLayer(labelMap: Map<string, string>, isMobile: boolean) {
  return function LabelsLayer({ nodes }: Pick<PCFSankeyLayerProps, 'nodes'>) {
    return (
      <g>
        {nodes.map((node) => {
          // Look up the display label from our map
          let label = labelMap.get(node.id) || node.id;

          // Truncate labels on mobile to prevent overlap
          if (isMobile) {
            label = truncateLabel(label, 10);
          }

          const lines = wrapLabel(label, 12);
          const lineHeight = 14;
          const totalHeight = lines.length * lineHeight;
          const startY = -totalHeight / 2 + lineHeight / 2;

          // Position label to the left or right of node
          const isLeftSide = node.x < 200;
          const labelX = isLeftSide ? node.x - 10 : node.x + node.width + 10;
          const textAnchor = isLeftSide ? 'end' : 'start';

          return (
            <text
              key={node.id}
              x={labelX}
              y={node.y + node.height / 2}
              textAnchor={textAnchor}
              dominantBaseline="central"
              style={{
                fontSize: isMobile ? 11 : 12,
                fontFamily: 'Inter, system-ui, sans-serif',
                fill: '#333333',
              }}
            >
              {lines.map((line, i) => (
                <tspan
                  key={i}
                  x={labelX}
                  dy={i === 0 ? startY : lineHeight}
                >
                  {line}
                </tspan>
              ))}
            </text>
          );
        })}
      </g>
    );
  };
}

/**
 * Node click event data
 */
export interface SankeyNodeClickData {
  id: string;
  label: string;
  nodeColor?: string;
  metadata?: {
    co2e: number;
    unit: string;
    category: string;
  };
}

interface SankeyDiagramProps {
  calculation: Calculation | null;
  width?: number;
  height?: number;
  /** Callback when a category node is clicked (not triggered for 'total' node) */
  onNodeClick?: (node: SankeyNodeClickData) => void;
}

/** Categories that are drillable (not including 'total') */
const DRILLABLE_CATEGORIES = ['materials', 'energy', 'transport', 'other', 'process', 'waste'];

/**
 * Responsive height values per spec (TASK-FE-P7-013):
 * - Mobile (<=640px): 350px
 * - Tablet (641px-1023px): 400px
 * - Desktop (>=1024px): 500px
 */
const RESPONSIVE_HEIGHTS = {
  mobile: 350,
  tablet: 400,
  desktop: 500,
} as const;

/**
 * Get the current viewport's responsive height using matchMedia
 * This provides consistent height values for both the container and inner elements
 */
function getResponsiveHeight(heightProp?: number): number {
  if (heightProp) return heightProp;

  // Check if window and matchMedia are available (SSR safety and test environment safety)
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return RESPONSIVE_HEIGHTS.desktop;
  }

  const isMobile = window.matchMedia(`(max-width: ${BREAKPOINTS.sm}px)`).matches;
  const isTabletOrSmaller = window.matchMedia(`(max-width: ${BREAKPOINTS.lg - 1}px)`).matches;

  if (isMobile) return RESPONSIVE_HEIGHTS.mobile;
  if (isTabletOrSmaller) return RESPONSIVE_HEIGHTS.tablet;
  return RESPONSIVE_HEIGHTS.desktop;
}

/**
 * Type guard to check if Sankey click data is a link (has source object with id)
 */
function isClickDataLink(data: PCFSankeyClickData): boolean {
  return (
    data !== null &&
    typeof data === 'object' &&
    'source' in data &&
    typeof (data as { source: unknown }).source === 'object' &&
    (data as { source: { id?: unknown } }).source !== null &&
    typeof (data as { source: { id: unknown } }).source.id === 'string'
  );
}

/**
 * SankeyDiagram Component
 *
 * Visualizes carbon emissions flow using Sankey diagram.
 *
 * @param calculation - Calculation result with breakdown data
 * @param width - Optional fixed width (default: responsive)
 * @param height - Optional fixed height (default: responsive, min 400px)
 * @param onNodeClick - Optional callback when a category node is clicked
 */
export default function SankeyDiagram({
  calculation,
  width,
  height,
  onNodeClick,
}: SankeyDiagramProps) {
  // State for expanded category (null = overview, string = expanded category)
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  // Get responsive breakpoint info
  const { isMobile } = useBreakpoints();

  // Calculate the actual container height for passing to inner elements
  const containerHeight = getResponsiveHeight(height);

  // Transform calculation data to Sankey format (overview or expanded)
  const sankeyData = useMemo(() => {
    if (expandedCategory) {
      return transformToExpandedSankeyData(calculation, expandedCategory);
    }
    return transformToSankeyData(calculation);
  }, [calculation, expandedCategory]);

  // Create label map and custom labels layer for text wrapping
  const customLabelsLayer = useMemo(() => {
    const labelMap = new Map<string, string>();
    sankeyData.nodes.forEach((node) => {
      labelMap.set(node.id, node.label);
    });
    return createLabelsLayer(labelMap, isMobile);
  }, [sankeyData, isMobile]);

  // Calculate minimum width based on node count for horizontal scroll
  const minWidth = useMemo(() => {
    const nodeCount = sankeyData.nodes.length;
    // Ensure minimum width for readability on complex charts
    return Math.max(400, nodeCount * 50);
  }, [sankeyData.nodes.length]);

  // Calculate node dimensions
  const nodeDimensions = useMemo(() => {
    const nodeCount = sankeyData.nodes.length;
    return {
      nodeThickness: Math.max(12, Math.min(18, 200 / nodeCount)),
      nodeSpacing: Math.max(8, Math.min(24, 150 / nodeCount)),
    };
  }, [sankeyData.nodes.length]);

  // Calculate responsive margins
  // Mobile needs adequate margins for labels that extend outside nodes
  const margins = useMemo(() => {
    if (isMobile) {
      return {
        top: 10,
        right: expandedCategory ? 70 : 50,
        bottom: 10,
        left: expandedCategory ? 80 : 60,
      };
    }
    return {
      top: 20,
      right: expandedCategory ? 85 : 65,
      bottom: 20,
      left: expandedCategory ? 100 : 85,
    };
  }, [isMobile, expandedCategory]);

  // Handle click on node or link - expand category
  // TASK-FE-P7-026: Properly typed handler - no any types
  const handleNodeClick = useCallback(
    (data: PCFSankeyClickData) => {
      if (!data) return;

      let nodeId: string | null = null;

      // Check if this is a link click (has 'source' object with 'id')
      // Links have: { source: { id: 'materials', ... }, target: { id: 'total', ... }, value, ... }
      if (isClickDataLink(data)) {
        // Link click - use the source node's id
        const linkData = data as { source: { id: string } };
        nodeId = linkData.source.id;
        console.log('Link click detected, source node:', nodeId);
      } else if ('id' in data && typeof data.id === 'string') {
        // Node click - use the node's id directly
        nodeId = data.id;
        console.log('Node click detected, node:', nodeId);
      }

      if (!nodeId) {
        console.log('Could not determine node ID from click data');
        return;
      }

      // If in overview mode and clicked a drillable category, try to expand it
      if (!expandedCategory && DRILLABLE_CATEGORIES.includes(nodeId)) {
        // Check if expanding would produce valid data before drilling down
        const expandedData = transformToExpandedSankeyData(calculation, nodeId);

        // Only drill down if the expanded view would have valid nodes
        if (expandedData.nodes.length > 0) {
          console.log('Expanding category:', nodeId);
          setExpandedCategory(nodeId);
        } else {
          console.log('No breakdown data for category:', nodeId, '- skipping drill-down');
        }

        // Always trigger external callback if provided (for analytics, etc.)
        if (onNodeClick) {
          const fullNode = sankeyData.nodes.find((n) => n.id === nodeId);
          if (fullNode) {
            onNodeClick({
              id: fullNode.id,
              label: fullNode.label,
              nodeColor: fullNode.nodeColor,
              metadata: fullNode.metadata,
            });
          }
        }
      }
    },
    [expandedCategory, onNodeClick, sankeyData.nodes, calculation]
  );

  // Handle back button click
  const handleBackClick = useCallback(() => {
    setExpandedCategory(null);
  }, []);

  // Get title for expanded view
  const expandedTitle = expandedCategory
    ? `${expandedCategory === 'other' ? 'Processing/Other' : expandedCategory.charAt(0).toUpperCase() + expandedCategory.slice(1)} Breakdown`
    : null;

  // Accessibility label for the chart
  const ariaLabel = expandedCategory
    ? `${expandedTitle} showing ${sankeyData.nodes.length - 1} items`
    : `Carbon flow diagram showing emissions breakdown with ${sankeyData.nodes.length} categories. Click on a category to see detailed breakdown.`;

  // Render the inner content (shared between normal and empty states)
  const renderInnerContent = () => {
    // Handle empty calculation
    if (!calculation) {
      return (
        <div
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#666',
            fontSize: '14px',
          }}
        >
          No calculation data available
        </div>
      );
    }

    // Handle pending/in-progress status
    if (calculation.status === 'pending' || calculation.status === 'in_progress') {
      return (
        <div
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#666',
            fontSize: '14px',
          }}
        >
          Calculating...
        </div>
      );
    }

    // Handle failed status
    if (calculation.status === 'failed') {
      return (
        <div
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#d32f2f',
            fontSize: '14px',
          }}
        >
          Calculation failed: {calculation.error_message || 'Unknown error'}
        </div>
      );
    }

    // Handle missing breakdown data
    if (sankeyData.nodes.length === 0) {
      return (
        <div
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#666',
            fontSize: '14px',
          }}
        >
          No breakdown data available
        </div>
      );
    }

    // Render Sankey chart
    return (
      <div style={{ width: '100%', height: '100%' }}>
        <ResponsiveSankey
          data={sankeyData}
          margin={margins}
          align="justify"
          colors={(node) => node.nodeColor || '#cccccc'}
          nodeOpacity={1}
          nodeHoverOpacity={1}
          nodeThickness={nodeDimensions.nodeThickness}
          nodeSpacing={nodeDimensions.nodeSpacing}
          nodeBorderWidth={0}
          nodeBorderColor={{ from: 'color', modifiers: [['darker', 0.8]] }}
          linkOpacity={0.6}
          linkHoverOpacity={0.9}
          linkBlendMode="multiply"
          enableLinkGradient={true}
          enableLabels={false}
          layers={['links', 'nodes', customLabelsLayer, 'legends']}
          nodeTooltip={SankeyTooltip}
          onClick={handleNodeClick}
          theme={{
            background: 'transparent',
            text: {
              fontSize: isMobile ? 11 : 12,
              fontFamily: 'Inter, system-ui, sans-serif',
              fill: '#333333',
            },
            tooltip: {
              container: {
                background: 'white',
                fontSize: '12px',
                borderRadius: '4px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              },
            },
          }}
        />
      </div>
    );
  };

  // Main render - ResponsiveChartContainer wraps everything including sankey-container
  return (
    <ResponsiveChartContainer
      minHeight={height ?? RESPONSIVE_HEIGHTS.desktop}
      mobileHeight={RESPONSIVE_HEIGHTS.mobile}
      tabletHeight={RESPONSIVE_HEIGHTS.tablet}
      enableScroll={isMobile}
      minWidth={isMobile ? minWidth : undefined}
      aria-label={ariaLabel}
    >
      <div
        data-testid="sankey-container"
        role="img"
        aria-label={ariaLabel}
        className={cn('relative', !expandedCategory && onNodeClick && 'cursor-pointer')}
        style={{ width: width ? `${width}px` : '100%', height: containerHeight }}
      >
        {/* Back button when in expanded view */}
        {expandedCategory && (
          <div className="flex items-center gap-2 mb-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleBackClick}
              className="flex items-center gap-1"
              data-testid="sankey-back-button"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Overview
            </Button>
            <span className="text-sm font-medium text-muted-foreground">
              {expandedTitle}
            </span>
          </div>
        )}

        {/* Hint text when in overview */}
        {!expandedCategory && sankeyData.nodes.length > 0 && (
          <p className="text-xs text-muted-foreground text-center mb-1">
            Click on a category to drill down
          </p>
        )}

        {/* Inner content */}
        <div style={{ width: '100%', height: expandedCategory ? 'calc(100% - 40px)' : sankeyData.nodes.length > 0 ? 'calc(100% - 20px)' : '100%' }}>
          {renderInnerContent()}
        </div>
      </div>
    </ResponsiveChartContainer>
  );
}
