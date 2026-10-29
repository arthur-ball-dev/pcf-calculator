/**
 * SankeyTooltip Component
 *
 * Custom tooltip for Sankey diagram nodes and links.
 * Displays emission values, percentages, and category information.
 *
 * TASK-FE-008: Nivo Sankey Implementation
 */

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
 * Format a number to 2 decimal places, avoiding floating point errors
 */
function formatValue(value: number): string {
  return Number(value.toFixed(2)).toString();
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
/**
 * Tooltip styles shared between node and link tooltips
 */
const tooltipStyles = {
  container: {
    background: 'white',
    padding: '12px',
    borderRadius: '4px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
    fontSize: '12px',
    fontFamily: 'Inter, system-ui, sans-serif',
    maxWidth: '250px',
  },
  title: {
    fontWeight: 600,
    marginBottom: '4px',
    color: '#333',
  },
  text: {
    color: '#666',
    marginBottom: '2px',
  },
} as const;

/**
 * Custom tooltip for Sankey nodes
 */
export default function SankeyTooltip({ node, link }: SankeyTooltipProps) {
  if (node) {
    const co2e = node.data?.metadata?.co2e || node.value;
    const category = node.data?.metadata?.category || 'Unknown';

    return (
      <div style={tooltipStyles.container}>
        <div style={tooltipStyles.title}>
          {node.label}
        </div>
        <div style={tooltipStyles.text}>
          Emissions: <strong>{formatValue(co2e)} kg CO₂e</strong>
        </div>
        <div style={{ ...tooltipStyles.text, textTransform: 'capitalize', marginBottom: 0 }}>
          Category: {category}
        </div>
      </div>
    );
  }

  if (link) {
    return (
      <div style={tooltipStyles.container}>
        <div style={tooltipStyles.text}>
          <strong>{link.source.label}</strong> → <strong>{link.target.label}</strong>
        </div>
        <div style={{ ...tooltipStyles.text, marginBottom: 0 }}>
          Flow: <strong>{formatValue(link.value)} kg CO₂e</strong>
        </div>
      </div>
    );
  }

  return null;
}

/**
 * Link tooltip props from Nivo
 */
interface SankeyLinkTooltipProps {
  link: {
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
 * Custom tooltip for Sankey links
 * This is a separate component because Nivo's linkTooltip expects a different prop structure
 */
export function SankeyLinkTooltip({ link }: SankeyLinkTooltipProps) {
  return (
    <div style={tooltipStyles.container}>
      <div style={tooltipStyles.text}>
        <strong>{link.source.label}</strong> → <strong>{link.target.label}</strong>
      </div>
      <div style={{ ...tooltipStyles.text, marginBottom: 0 }}>
        Flow: <strong>{formatValue(link.value)} kg CO₂e</strong>
      </div>
    </div>
  );
}
