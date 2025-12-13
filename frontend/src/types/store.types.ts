/**
 * Store Type Definitions
 *
 * TypeScript interfaces for Zustand stores including:
 * - Wizard navigation state
 * - Calculator state (product selection, BOM, calculations)
 * - Shared types and enums
 *
 * UPDATED: TASK-FE-020 - Migrated UUID fields from number to string
 * - Product.id: number -> string (32-char hex UUID)
 * - selectedProductId: number | null -> string | null
 * - BOMItem.emissionFactorId: number | null -> string | null
 *
 * UPDATED: TEST-FIX - Added notes field to BOMItem
 * - notes: string | undefined - optional field from API BOMItemResponse
 */

// ============================================================================
// Wizard Store Types
// ============================================================================

export type WizardStep = 'select' | 'edit' | 'calculate' | 'results';

export interface WizardState {
  // State
  currentStep: WizardStep;
  completedSteps: WizardStep[];
  canProceed: boolean;
  canGoBack: boolean;

  // Actions
  setStep: (step: WizardStep) => void;
  markStepComplete: (step: WizardStep) => void;
  markStepIncomplete: (step: WizardStep) => void;
  goNext: () => void;
  goBack: () => void;
  reset: () => void;
}

// ============================================================================
// Calculator Store Types
// ============================================================================

export type BOMItemCategory = 'material' | 'energy' | 'transport' | 'other';

export type UnitType = 'unit' | 'kg' | 'g' | 'L' | 'mL' | 'm' | 'cm' | 'kWh' | 'MJ' | 'tkm';

export type CalculationStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

export type CalculationType = 'cradle_to_gate' | 'cradle_to_grave' | 'gate_to_gate';

export interface BOMItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  category: BOMItemCategory;
  emissionFactorId: string | null; // UPDATED: number | null -> string | null (UUID)
  notes?: string; // ADDED: Optional notes from API BOMItemResponse
}

export interface Product {
  id: string; // UPDATED: number -> string (32-char hex UUID)
  code: string;
  name: string;
  category: string | null; // UPDATED: Made nullable to match API ProductListItem/ProductDetail
  unit: string; // UPDATED: Changed from UnitType enum to string to match API
  is_finished_product: boolean;
  metadata?: Record<string, unknown>;
}

export interface Calculation {
  id: string;
  status: CalculationStatus;
  product_id?: string;
  created_at?: string;
  updated_at?: string;
  calculation_type?: CalculationType;

  // Present when completed
  total_co2e?: number;
  total_co2e_kg?: number;
  materials_co2e?: number;
  energy_co2e?: number;
  transport_co2e?: number;
  waste_co2e?: number;
  calculation_time_ms?: number;

  // Present when failed
  error_message?: string;
}

export interface CalculatorState {
  // Product selection
  selectedProductId: string | null; // UPDATED: number | null -> string | null (UUID)
  selectedProduct: Product | null;

  // BOM data
  bomItems: BOMItem[];
  hasUnsavedChanges: boolean;

  // Calculation data
  calculation: Calculation | null;

  // Loading states
  isLoadingProducts: boolean;
  isLoadingBOM: boolean;

  // Actions - Product
  setSelectedProduct: (productId: string | null) => void; // UPDATED: number | null -> string | null
  setSelectedProductDetails: (product: Product | null) => void;

  // Actions - BOM
  setBomItems: (items: BOMItem[]) => void;
  updateBomItem: (id: string, updates: Partial<BOMItem>) => void;
  addBomItem: (item: BOMItem) => void;
  removeBomItem: (id: string) => void;

  // Actions - Calculation
  setCalculation: (calculation: Calculation | null) => void;

  // Actions - Loading
  setLoadingProducts: (loading: boolean) => void;
  setLoadingBOM: (loading: boolean) => void;

  // Actions - Reset
  reset: () => void;
}

// ============================================================================
// Helper Types
// ============================================================================

export interface StepConfig {
  id: WizardStep;
  label: string;
  description: string;
  progressLabel?: string; // Optional shorter label for progress indicator
  component?: React.ComponentType;
  validate?: () => Promise<boolean>;
}

export interface EmissionBreakdown {
  category: string;
  co2e: number;
  percentage: number;
}

export interface CalculationResult extends Calculation {
  breakdown: EmissionBreakdown[];
  data_quality_score?: number;
}
