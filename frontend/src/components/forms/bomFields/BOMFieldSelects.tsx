/**
 * Category, unit and emission factor pickers for a BOM row (#195, TASK-FE-P9-006)
 * Shared by the desktop row (BOMTableRow) and the mobile card (BOMCardList).
 */
import { useMemo } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { EmissionFactor } from '@/hooks/useEmissionFactors';
import type { BOMItemCategory } from '@/types/store.types';
import { unitsForFactor } from '@/utils/units';
import { BOM_CATEGORIES, categoryStyle } from './categories';

/** Most factors rendered in one dropdown; 300+ SelectItems made the editor slow */
export const MAX_DROPDOWN_ITEMS = 50;

interface CategorySelectProps {
  value: BOMItemCategory;
  onChange: (value: BOMItemCategory) => void;
  className?: string;
}

/** Category picker that shows the coloured category badge as its value */
export function CategorySelect({ value, onChange, className }: CategorySelectProps) {
  const style = categoryStyle(value);
  return (
    <Select value={value} onValueChange={(v) => onChange(v as BOMItemCategory)}>
      <SelectTrigger
        aria-label="Category"
        className={className ?? 'h-[30px] w-[130px] px-2.5 text-[13px] font-semibold border'}
        style={{ background: style.bgColor, color: style.color, borderColor: style.borderColor }}
      >
        <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
          <span className="w-[7px] h-[7px] rounded-full flex-shrink-0" style={{ background: style.color }} />
          <SelectValue>{style.label}</SelectValue>
        </span>
      </SelectTrigger>
      <SelectContent>
        {BOM_CATEGORIES.map((category) => (
          <SelectItem key={category} value={category}>
            {categoryStyle(category).label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

interface UnitSelectProps {
  value: string;
  onChange: (value: string) => void;
  /** Unit of the row's emission factor; limits the options to its kind */
  factorUnit?: string;
  className?: string;
}

/** Unit picker offering only units the calculation can convert to the factor's unit */
export function UnitSelect({ value, onChange, factorUnit, className }: UnitSelectProps) {
  const units = useMemo(() => unitsForFactor(factorUnit), [factorUnit]);
  return (
    <Select onValueChange={onChange} value={value}>
      <SelectTrigger
        className={className ?? 'w-[70px] h-[30px] text-[13px] text-[var(--text-dim)] bg-transparent border-white/[0.08]'}
        aria-label="Unit"
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {units.map((unit) => (
          <SelectItem key={unit} value={unit}>
            {unit}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

interface EmissionFactorSelectProps {
  value: string | null | undefined;
  onChange: (factor: EmissionFactor | null) => void;
  factors: EmissionFactor[];
  disabled?: boolean;
  className?: string;
}

/** Emission factor picker (first MAX_DROPDOWN_ITEMS factors, plus the selected one) */
export function EmissionFactorSelect({ value, onChange, factors, disabled, className }: EmissionFactorSelectProps) {
  const options = useMemo(() => {
    if (factors.length <= MAX_DROPDOWN_ITEMS) return factors;
    const limited = factors.slice(0, MAX_DROPDOWN_ITEMS);
    if (value && !limited.some((f) => f.id === value)) {
      const selected = factors.find((f) => f.id === value);
      if (selected) limited.unshift(selected);
    }
    return limited;
  }, [factors, value]);

  return (
    <Select
      onValueChange={(id) => onChange(factors.find((f) => f.id === id) ?? null)}
      value={value ?? ''}
      disabled={disabled || options.length === 0}
    >
      <SelectTrigger
        className={className ?? 'w-full bg-white/[0.04] border-white/[0.08] text-[var(--text-primary)] truncate'}
        aria-label="Emission factor"
      >
        <SelectValue placeholder="Select factor" />
      </SelectTrigger>
      <SelectContent>
        {options.map((factor) => (
          <SelectItem key={factor.id} value={factor.id}>
            {factor.activity_name} ({factor.co2e_factor} kg CO&#8322;e/{factor.unit})
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

/** Shown on a row that has no emission factor yet; Calculate stays disabled until it has one */
export function MissingFactorHint() {
  return (
    <p className="mt-1 text-[12px] text-amber-400" role="status">
      Choose an emission factor to calculate
    </p>
  );
}
