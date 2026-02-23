/**
 * AppLogo Component
 *
 * Emerald Night design system logo for the PCF Calculator header.
 * Displays an emerald square icon with layers SVG and "PCF Calculator" text.
 *
 * Based on prototype: approach-5b-single-card/01-select-product.html
 *
 * Visual:
 * - 34x34px emerald square with 9px border-radius
 * - White layers SVG icon (18x18px)
 * - "PCF" in primary text, "Calculator" in emerald accent
 * - Plus Jakarta Sans heading font at 1.125rem
 *
 * Accessibility:
 * - Uses h1 heading for screen readers and semantic structure
 * - Layers SVG marked aria-hidden
 */

import React from 'react';

const AppLogo: React.FC = () => {
  return (
    <h1 className="flex items-center gap-3 m-0">
      {/* Emerald square icon */}
      <div
        className="w-[34px] h-[34px] rounded-[9px] bg-emerald-500 flex items-center justify-center flex-shrink-0"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="white"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-[18px] h-[18px]"
          aria-hidden="true"
        >
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
      </div>

      {/* Logo text */}
      <span className="font-heading font-bold text-lg tracking-[-0.01em] text-[var(--text-primary)]">
        PCF <span className="text-emerald-500">Calculator</span>
      </span>
    </h1>
  );
};

export default AppLogo;
