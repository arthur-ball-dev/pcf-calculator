/**
 * SankeyDiagram Component
 *
 * Interactive Sankey diagram for visualizing carbon flow from materials
 * through manufacturing to final product using Nivo ResponsiveSankey.
 *
 * Features:
 * - Color coding by emission category
 * - Interactive tooltips with CO2e values
 * - Responsive sizing
 * - Empty/loading/error states
 * - WCAG 2.1 AA accessible
 *
 * TASK-FE-008: Nivo Sankey Implementation
 */

import { useMemo } from 'react';
import { ResponsiveSankey } from '@nivo/sankey';
import { transformToSankeyData } from '../../utils/sankeyTransform';
import SankeyTooltip from './SankeyTooltip';
import type { Calculation } from '../../types/store.types';

interface SankeyDiagramProps {
  calculation: Calculation | null;
  width?: number;
  height?: number;
}

/**
 * SankeyDiagram Component
 *
 * Visualizes carbon emissions flow using Sankey diagram.
 *
 * @param calculation - Calculation result with breakdown data
 * @param width - Optional fixed width (default: responsive)
 * @param height - Optional fixed height (default: responsive, min 400px)
 */
export default function SankeyDiagram({ calculation, width, height }: SankeyDiagramProps) {
  // Transform calculation data to Sankey format
  const sankeyData = useMemo(() => {
    return transformToSankeyData(calculation);
  }, [calculation]);

  // Calculate responsive dimensions
  const dimensions = useMemo(() => {
    const calculatedHeight = height || Math.max(400, Math.min(600, (width || 800) * 0.5));
    return {
      width: width || 800,
      height: calculatedHeight,
    };
  }, [width, height]);

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

  // Render Sankey diagram
  return (
    <div
      data-testid="sankey-container"
      role="img"
      aria-label={`Carbon flow diagram showing emissions breakdown with ${sankeyData.nodes.length} categories`}
      style={{
        width: dimensions.width,
        height: dimensions.height,
      }}
    >
      <ResponsiveSankey
        data={sankeyData}
        margin={{ top: 20, right: 120, bottom: 20, left: 120 }}
        align="justify"
        colors={(node) => node.nodeColor || '#cccccc'}
        nodeOpacity={1}
        nodeHoverOpacity={1}
        nodeThickness={18}
        nodeSpacing={24}
        nodeBorderWidth={0}
        nodeBorderColor={{ from: 'color', modifiers: [['darker', 0.8]] }}
        linkOpacity={0.6}
        linkHoverOpacity={0.9}
        linkBlendMode="multiply"
        enableLinkGradient={true}
        labelPosition="outside"
        labelOrientation="horizontal"
        labelPadding={16}
        labelTextColor={{ from: 'color', modifiers: [['darker', 1]] }}
        nodeTooltip={SankeyTooltip}
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
  );
}
