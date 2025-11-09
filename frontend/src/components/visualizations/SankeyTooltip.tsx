/**
 * SankeyTooltip Component
 *
 * Custom tooltip for Sankey diagram nodes and links.
 * Displays emission values, percentages, and category information.
 *
 * TASK-FE-008: Nivo Sankey Implementation
 */

import React from 'react';
import type { SankeyNode } from '../../utils/sankeyTransform';

interface SankeyTooltipProps {
  node?: {
    id: string;
    label: string;
    value: number;
    color: string;
    data?: SankeyNode;
  };
  link?: {
    source: {
      id: string;
      label: string;
    };
    target: {
      id: string;
      label: string;
    };
    value: number;
    color: string;
  };
}

/**
 * Custom tooltip component for Sankey diagram
 *
 * Shows:
 * - Component/category name
 * - CO2e value with unit
 * - Percentage of total (if available)
 * - Category label
 */
export default function SankeyTooltip({ node, link }: SankeyTooltipProps) {
  if (node) {
    const co2e = node.data?.metadata?.co2e || node.value;
    const category = node.data?.metadata?.category || 'Unknown';

    return (
      <div
        style={{
          background: 'white',
          padding: '12px',
          borderRadius: '4px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          fontSize: '12px',
          fontFamily: 'Inter, system-ui, sans-serif',
        }}
      >
        <div
          style={{
            fontWeight: 600,
            marginBottom: '4px',
            color: '#333',
          }}
        >
          {node.label}
        </div>
        <div style={{ color: '#666', marginBottom: '2px' }}>
          Emissions: <strong>{co2e.toFixed(2)} kg CO₂e</strong>
        </div>
        <div style={{ color: '#666', textTransform: 'capitalize' }}>
          Category: {category}
        </div>
      </div>
    );
  }

  if (link) {
    return (
      <div
        style={{
          background: 'white',
          padding: '12px',
          borderRadius: '4px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          fontSize: '12px',
          fontFamily: 'Inter, system-ui, sans-serif',
        }}
      >
        <div style={{ color: '#666', marginBottom: '2px' }}>
          <strong>{link.source.label}</strong> → <strong>{link.target.label}</strong>
        </div>
        <div style={{ color: '#666' }}>
          Flow: <strong>{link.value.toFixed(2)} kg CO₂e</strong>
        </div>
      </div>
    );
  }

  return null;
}
