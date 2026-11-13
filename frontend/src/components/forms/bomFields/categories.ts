/**
 * BOM row categories: picker labels and badge colours (#195, TASK-FE-P9-006)
 * Shared by the desktop row (BOMTableRow) and the mobile card (BOMCardList).
 */
import { EMISSION_CATEGORY_COLORS } from '@/constants/colors';
import type { BOMItemCategory } from '@/types/store.types';

export interface CategoryStyle {
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
}

export const CATEGORY_CONFIG: Record<BOMItemCategory, CategoryStyle> = {
  material: {
    label: 'Materials',
    color: EMISSION_CATEGORY_COLORS.materials,
    bgColor: 'rgba(16, 185, 129, 0.18)',
    borderColor: 'rgba(16, 185, 129, 0.22)',
  },
  energy: {
    label: 'Energy',
    color: EMISSION_CATEGORY_COLORS.energy,
    bgColor: 'rgba(245, 158, 11, 0.18)',
    borderColor: 'rgba(245, 158, 11, 0.22)',
  },
  transport: {
    label: 'Transport',
    color: EMISSION_CATEGORY_COLORS.transport,
    bgColor: 'rgba(59, 130, 246, 0.18)',
    borderColor: 'rgba(59, 130, 246, 0.22)',
  },
  combustion: {
    label: 'Combustion',
    color: '#E91E63',
    bgColor: 'rgba(233, 30, 99, 0.18)',
    borderColor: 'rgba(233, 30, 99, 0.22)',
  },
  other: {
    label: 'Other',
    color: EMISSION_CATEGORY_COLORS.other,
    bgColor: 'rgba(148, 163, 184, 0.15)',
    borderColor: 'rgba(148, 163, 184, 0.18)',
  },
};

export const BOM_CATEGORIES = Object.keys(CATEGORY_CONFIG) as BOMItemCategory[];

export function categoryStyle(category: string | undefined): CategoryStyle {
  return CATEGORY_CONFIG[category as BOMItemCategory] ?? CATEGORY_CONFIG.other;
}
