/**
 * ContextBar Component
 *
 * Glassmorphic bar showing the selected product with optional badge and action button.
 * Used across wizard steps to provide persistent product context and quick actions.
 *
 * Based on prototype: approach-5b-single-card context-bar CSS
 *
 * Visual design:
 * - Left: emerald-dim icon background + product name + code
 * - Right: optional badge (e.g., "8 components") + optional action button
 * - Responsive: stacks on mobile (flex-col below 768px)
 *
 * Props:
 * - productName: Display name of the selected product
 * - productCode: Product code (e.g., "SR-001")
 * - badge: Optional text badge (e.g., "8 components")
 * - actionLabel: Optional button text
 * - actionIcon: Optional React node for button icon
 * - onAction: Click handler for the action button
 * - disabled: Whether the action button is disabled
 * - className: Additional CSS classes
 */

import React from 'react';
import { cn } from '@/lib/utils';

interface ContextBarProps {
  productName: string;
  productCode: string;
  badge?: string;
  actionLabel?: string;
  actionIcon?: React.ReactNode;
  onAction?: () => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Layers icon SVG - same as logo but used in emerald-dim background
 */
const LayersIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
  >
    <path d="M12 2L2 7l10 5 10-5-10-5z" />
    <path d="M2 17l10 5 10-5" />
    <path d="M2 12l10 5 10-5" />
  </svg>
);

const ContextBar: React.FC<ContextBarProps> = ({
  productName,
  productCode,
  badge,
  actionLabel,
  actionIcon,
  onAction,
  disabled = false,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex items-center justify-between',
        'p-4 px-6 rounded-[14px] mb-6',
        'bg-[var(--card-bg)] border border-[var(--card-border)] backdrop-blur-[12px]',
        // Responsive: stack on mobile
        'max-[768px]:flex-col max-[768px]:items-start max-[768px]:gap-3',
        className
      )}
    >
      {/* Left: Product info */}
      <div className="flex items-center gap-3.5">
        {/* Icon container */}
        <div
          className={cn(
            'w-[38px] h-[38px] rounded-[10px] flex-shrink-0',
            'bg-[var(--accent-emerald-dim)] flex items-center justify-center',
            'text-[var(--accent-emerald)]'
          )}
        >
          <LayersIcon className="w-[18px] h-[18px]" />
        </div>

        {/* Product details */}
        <div>
          <div className="font-heading font-semibold text-base text-[var(--text-primary)]">
            {productName}
          </div>
          <div className="text-[0.8125rem] text-[var(--text-dim)] tabular-nums">
            {productCode}
          </div>
        </div>
      </div>

      {/* Right: Badge + Action */}
      {(badge || actionLabel) && (
        <div className="flex items-center gap-3">
          {/* Badge */}
          {badge && (
            <div
              className={cn(
                'px-3 py-1 rounded-lg',
                'bg-[var(--accent-emerald-dim)] text-[var(--accent-emerald)]',
                'text-[0.8125rem] font-semibold tabular-nums'
              )}
            >
              {badge}
            </div>
          )}

          {/* Action button */}
          {actionLabel && onAction && (
            <button
              type="button"
              onClick={onAction}
              disabled={disabled}
              className={cn(
                'inline-flex items-center gap-2',
                'px-5 py-2 rounded-[10px]',
                'bg-emerald-500 text-white',
                'text-[0.8125rem] font-semibold',
                'shadow-[0_1px_3px_rgba(16,185,129,0.3)]',
                'transition-all duration-200',
                'hover:bg-emerald-600 hover:shadow-[0_4px_16px_rgba(16,185,129,0.3)] hover:-translate-y-px',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                'disabled:opacity-50 disabled:pointer-events-none'
              )}
            >
              {actionIcon}
              {actionLabel}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ContextBar;
