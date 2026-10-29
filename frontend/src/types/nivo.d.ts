/**
 * Nivo Type Definitions
 *
 * Custom type definitions extending @nivo/sankey types for PCF Calculator.
 * Provides proper typing for Sankey diagram event handlers and custom nodes.
 *
 * TASK-FE-P7-026: Eliminate TypeScript any usages
 *
 * These types are based on the official @nivo/sankey types but customized
 * for our PCF Calculator's specific node structure with metadata.
 */

import type { MouseEvent } from 'react';

/**
 * Base node interface for Sankey data input
 * This is what we pass to the Sankey component
 */
export interface PCFSankeyInputNode {
  id: string;
  label: string;
  nodeColor?: string;
  metadata?: {
    co2e: number;
    unit: string;
    category: string;
  };
}

/**
 * Alias for PCFSankeyInputNode for simpler usage
 */
export type PCFSankeyNode = PCFSankeyInputNode;

/**
 * Base link interface for Sankey data input
 */
export interface PCFSankeyInputLink {
  source: string;
  target: string;
  value: number;
  color?: string;
}

/**
 * Computed Sankey node datum returned by Nivo after processing
 * Extends our input node with computed layout properties
 */
export interface PCFSankeyNodeDatum extends PCFSankeyInputNode {
  // Properties computed by d3-sankey
  depth: number;
  index: number;
  x0: number;
  x1: number;
  y0: number;
  y1: number;
  value: number;
  color: string;
  formattedValue: string;
  layer: number;
  // Computed by Nivo
  x: number;
  y: number;
  width: number;
  height: number;
  // Link references (simplified for our use case)
  sourceLinks: readonly PCFSankeyLinkDatum[];
  targetLinks: readonly PCFSankeyLinkDatum[];
}

/**
 * Computed Sankey link datum returned by Nivo after processing
 */
export interface PCFSankeyLinkDatum {
  value: number;
  index: number;
  source: PCFSankeyNodeDatum;
  target: PCFSankeyNodeDatum;
  pos0: number;
  pos1: number;
  thickness: number;
  color: string;
  formattedValue: string;
  startColor?: string;
  endColor?: string;
}

/**
 * Union type for click handler data - can be either a node or a link
 * This is what Nivo passes to the onClick handler
 */
export type PCFSankeyClickData = PCFSankeyNodeDatum | PCFSankeyLinkDatum;

/**
 * Type guard to check if click data is a link (has source object)
 */
export function isSankeyLink(data: PCFSankeyClickData): data is PCFSankeyLinkDatum {
  return (
    data !== null &&
    typeof data === 'object' &&
    'source' in data &&
    typeof data.source === 'object' &&
    data.source !== null &&
    'id' in data.source
  );
}

/**
 * Type guard to check if click data is a node (has id directly)
 */
export function isSankeyNode(data: PCFSankeyClickData): data is PCFSankeyNodeDatum {
  return (
    data !== null &&
    typeof data === 'object' &&
    'id' in data &&
    typeof data.id === 'string' &&
    !('source' in data && typeof (data as PCFSankeyLinkDatum).source === 'object')
  );
}

/**
 * Click handler type for Sankey diagrams
 * Matches Nivo's onClick signature
 */
export type PCFSankeyClickHandler = (
  data: PCFSankeyClickData,
  event: MouseEvent<Element>
) => void;

/**
 * Event data passed to node click handler
 * Contains the node and the mouse event
 */
export interface SankeyNodeClickEvent {
  node: PCFSankeyNodeDatum;
  event: MouseEvent<SVGGElement>;
}

/**
 * Event data passed to link click handler
 * Contains the link and the mouse event
 */
export interface SankeyLinkClickEvent {
  link: PCFSankeyLinkDatum;
  event: MouseEvent<SVGPathElement>;
}

/**
 * Handler type for Sankey node click events
 */
export type SankeyNodeClickHandler = (event: SankeyNodeClickEvent) => void;

/**
 * Handler type for Sankey link click events
 */
export type SankeyLinkClickHandler = (event: SankeyLinkClickEvent) => void;

/**
 * Custom layer props for Sankey diagrams
 * Used by custom labels layer
 */
export interface PCFSankeyLayerProps {
  nodes: readonly PCFSankeyNodeDatum[];
  links: readonly PCFSankeyLinkDatum[];
  margin: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
  width: number;
  height: number;
  outerWidth: number;
  outerHeight: number;
}
