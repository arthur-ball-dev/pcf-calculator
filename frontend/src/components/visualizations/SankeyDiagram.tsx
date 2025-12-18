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
 * - Responsive sizing
 * - Empty/loading/error states
 * - WCAG 2.1 AA accessible
 *
 * TASK-FE-008: Nivo Sankey Implementation
 * TASK-FE-P8-002: Category Drill-Down click handler
 */

import { useState, useMemo, useCallback } from 'react';
import { ResponsiveSankey } from '@nivo/sankey';
import { ArrowLeft } from 'lucide-react';
import { transformToSankeyData, transformToExpandedSankeyData } from '../../utils/sankeyTransform';
import SankeyTooltip from './SankeyTooltip';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';
import type { Calculation } from '../../types/store.types';

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
 */
function createLabelsLayer(labelMap: Map<string, string>) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return function LabelsLayer({ nodes }: { nodes: readonly any[] }) {
    return (
      <g>
        {nodes.map((node) => {
          // Look up the display label from our map
          const label = labelMap.get(node.id) || node.id;
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
                fontSize: 12,
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
    return createLabelsLayer(labelMap);
  }, [sankeyData]);

  // Calculate responsive dimensions based on content
  // Uses the same nodeThickness/nodeSpacing formulas as the Sankey component for consistency
  const dimensions = useMemo(() => {
    // Default to 100% width for responsive sizing when no explicit width provided
    const responsiveWidth = width || '100%';

    if (height) {
      return { width: responsiveWidth, height, chartHeight: height };
    }

    const nodeCount = sankeyData.nodes.length;
    if (nodeCount === 0) {
      return { width: responsiveWidth, height: 200, chartHeight: 200 };
    }

    // Same formulas used in ResponsiveSankey props below
    const nodeThickness = Math.max(12, Math.min(18, 200 / nodeCount));
    const nodeSpacing = Math.max(8, Math.min(24, 150 / nodeCount));

    // Calculate max label lines based on actual label lengths and wrap threshold
    const wrapThreshold = 12; // Same as wrapLabel function
    const maxLabelLines = Math.max(
      ...sankeyData.nodes.map(node => Math.ceil(node.label.length / wrapThreshold))
    );
    const lineHeight = 14; // Same as in createLabelsLayer
    const labelHeight = maxLabelLines * lineHeight;

    // Total content height = space for nodes + spacing between nodes
    const nodesContentHeight = (nodeThickness * nodeCount) + (nodeSpacing * (nodeCount - 1));

    // Add overflow space for labels that extend beyond node bounds
    const labelOverflow = Math.max(0, labelHeight - nodeThickness);

    // Vertical margins match ResponsiveSankey margin prop (top: 20, bottom: 20)
    const verticalMargin = 40;

    // Chart height is the actual Sankey visualization space needed
    const chartHeight = Math.max(400, nodesContentHeight + labelOverflow + verticalMargin);

    // Header height for back button and hint text when in expanded mode
    const headerHeight = expandedCategory ? 48 : 24; // back button ~48px, hint text ~24px

    // Total container height = chart + header
    const totalHeight = chartHeight + headerHeight;

    return {
      width: responsiveWidth,
      height: totalHeight,
      chartHeight: chartHeight,
    };
  }, [width, height, sankeyData.nodes, expandedCategory]);

  // Handle click on node or link - expand category
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleNodeClick = useCallback(
    (data: any) => {
      if (!data) return;

      let nodeId: string | null = null;

      // Check if this is a link click (has 'source' object with 'id')
      // Links have: { source: { id: 'materials', ... }, target: { id: 'total', ... }, value, ... }
      if (data.source && typeof data.source === 'object' && data.source.id) {
        // Link click - use the source node's id
        nodeId = data.source.id as string;
        console.log('Link click detected, source node:', nodeId);
      } else if (data.id) {
        // Node click - use the node's id directly
        nodeId = data.id as string;
        console.log('Node click detected, node:', nodeId);
      }

      if (!nodeId) {
        console.log('Could not determine node ID from click data');
        return;
      }

      // If in overview mode and clicked a drillable category, expand it
      if (!expandedCategory && DRILLABLE_CATEGORIES.includes(nodeId)) {
        console.log('Expanding category:', nodeId);
        setExpandedCategory(nodeId);

        // Also trigger external callback if provided
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
    [expandedCategory, onNodeClick, sankeyData.nodes]
  );

  // Handle back button click
  const handleBackClick = useCallback(() => {
    setExpandedCategory(null);
  }, []);

  // Handle empty calculation
  if (!calculation) {
    return (
      <div
        data-testid="sankey-container"
        style={{
          width: dimensions.width,
          height: dimensions.height,
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
        data-testid="sankey-container"
        style={{
          width: dimensions.width,
          height: dimensions.height,
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
        data-testid="sankey-container"
        style={{
          width: dimensions.width,
          height: dimensions.height,
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
        data-testid="sankey-container"
        style={{
          width: dimensions.width,
          height: dimensions.height,
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

  // Get title for expanded view
  const expandedTitle = expandedCategory
    ? `${expandedCategory === 'other' ? 'Processing/Other' : expandedCategory.charAt(0).toUpperCase() + expandedCategory.slice(1)} Breakdown`
    : null;

  // Render Sankey diagram
  return (
    <div
      data-testid="sankey-container"
      role="img"
      aria-label={
        expandedCategory
          ? `${expandedTitle} showing ${sankeyData.nodes.length - 1} items`
          : `Carbon flow diagram showing emissions breakdown with ${sankeyData.nodes.length} categories. Click on a category to see detailed breakdown.`
      }
      className={cn('relative', !expandedCategory && onNodeClick && 'cursor-pointer')}
      style={{ width: dimensions.width, height: dimensions.height }}
    >
      {/* Back button when in expanded view */}
      {expandedCategory && (
        <div className="flex items-center gap-2 mb-4">
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
      {!expandedCategory && (
        <p className="text-xs text-muted-foreground text-center mb-2">
          Click on a category to drill down
        </p>
      )}

      <div
        style={{
          width: '100%',
          height: dimensions.chartHeight,
        }}
      >
        <ResponsiveSankey
          data={sankeyData}
          margin={{
            top: 20,
            right: expandedCategory ? 85 : 65,
            bottom: 20,
            left: expandedCategory ? 100 : 85
          }}
          align="justify"
          colors={(node) => node.nodeColor || '#cccccc'}
          nodeOpacity={1}
          nodeHoverOpacity={1}
          nodeThickness={Math.max(12, Math.min(18, 200 / sankeyData.nodes.length))}
          nodeSpacing={Math.max(8, Math.min(24, 150 / sankeyData.nodes.length))}
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
              fontSize: 12,
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
    </div>
  );
}
