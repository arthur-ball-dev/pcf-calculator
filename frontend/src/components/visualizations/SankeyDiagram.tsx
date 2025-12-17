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
const DRILLABLE_CATEGORIES = ['materials', 'energy', 'transport', 'process', 'waste'];

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

  // Calculate responsive dimensions
  const dimensions = useMemo(() => {
    const calculatedHeight = height || Math.max(400, Math.min(600, (width || 800) * 0.5));
    return {
      width: width || 800,
      height: calculatedHeight,
    };
  }, [width, height]);

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
    ? `${expandedCategory.charAt(0).toUpperCase() + expandedCategory.slice(1)} Breakdown`
    : null;

  // Render Sankey diagram
  return (
    <div
      data-testid="sankey-container"
      className="relative"
    >
      {/* Back button when in expanded view */}
      {expandedCategory && (
        <div className="absolute top-0 left-0 z-10 flex items-center gap-2">
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
        role="img"
        aria-label={
          expandedCategory
            ? `${expandedTitle} showing ${sankeyData.nodes.length - 1} items`
            : `Carbon flow diagram showing emissions breakdown with ${sankeyData.nodes.length} categories. Click on a category to see detailed breakdown.`
        }
        className={cn(!expandedCategory && 'cursor-pointer')}
        style={{
          width: '100%',
          height: dimensions.height,
        }}
      >
        <ResponsiveSankey
          data={sankeyData}
          margin={{ top: expandedCategory ? 50 : 20, right: 80, bottom: 20, left: 80 }}
          align="justify"
          colors={(node) => node.nodeColor || '#cccccc'}
          nodeOpacity={1}
          nodeHoverOpacity={1}
          nodeThickness={18}
          nodeSpacing={expandedCategory ? 12 : 24}
          nodeBorderWidth={0}
          nodeBorderColor={{ from: 'color', modifiers: [['darker', 0.8]] }}
          linkOpacity={0.6}
          linkHoverOpacity={0.9}
          linkBlendMode="multiply"
          enableLinkGradient={true}
          label={(node) => (node as { label?: string; id: string }).label || node.id}
          labelPosition="outside"
          labelOrientation="horizontal"
          labelPadding={16}
          labelTextColor={{ from: 'color', modifiers: [['darker', 1]] }}
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
