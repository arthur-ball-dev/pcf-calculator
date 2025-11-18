/**
 * API Type Definitions
 *
 * TypeScript interfaces matching backend Pydantic models.
 * These types ensure type safety for API requests/responses.
 *
 * Reference: backend/schemas/__init__.py
 */

// ============================================================================
// Products API Types
// ============================================================================

export interface BOMItemResponse {
  id: string;
  child_product_id: string;
  child_product_name: string;
  quantity: number;
  unit: string | null;
  notes: string | null;
}

export interface ProductListItem {
  id: string;
  code: string;
  name: string;
  unit: string;
  category: string | null;
  is_finished_product: boolean;
  created_at: string;
}

export interface ProductDetail {
  id: string;
  code: string;
  name: string;
  description: string | null;
  unit: string;
  category: string | null;
  is_finished_product: boolean;
  bill_of_materials: BOMItemResponse[];
  created_at: string;
}

export interface ProductListResponse {
  items: ProductListItem[];
  total: number;
  limit: number;
  offset: number;
}

// ============================================================================
// Calculations API Types
// ============================================================================

export type CalculationType = 'cradle_to_gate' | 'cradle_to_grave' | 'gate_to_gate';

export interface CalculationRequest {
  product_id: string;
  calculation_type?: CalculationType;
}

export interface CalculationStartResponse {
  calculation_id: string;
  status: string;
}

export interface CalculationStatusResponse {
  calculation_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  product_id: string | null;
  created_at: string | null;

  // Present when completed
  total_co2e_kg?: number;
  materials_co2e?: number;
  energy_co2e?: number;
  transport_co2e?: number;
  calculation_time_ms?: number;

  // Present when failed
  error_message?: string;
}

// ============================================================================
// Emission Factors API Types
// ============================================================================

export interface EmissionFactorListItem {
  id: string;
  activity_name: string;
  category: string | null;
  co2e_factor: number;
  unit: string;
  data_source: string;
  geography: string;
  reference_year: number | null;
  data_quality_rating: number | null;
  created_at: string;
}

export interface EmissionFactorListResponse {
  items: EmissionFactorListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface EmissionFactorCreateRequest {
  activity_name: string;
  co2e_factor: number;
  unit: string;
  data_source: string;
  geography?: string;
  reference_year?: number;
  data_quality_rating?: number;
  uncertainty_min?: number;
  uncertainty_max?: number;
}

export interface EmissionFactorCreateResponse {
  id: string;
  activity_name: string;
  co2e_factor: number;
  unit: string;
  data_source: string;
  geography: string;
  reference_year: number | null;
  data_quality_rating: number | null;
  created_at: string;
}

// ============================================================================
// Common Types
// ============================================================================

export interface PaginationParams {
  limit?: number;
  offset?: number;
}

// ============================================================================
// Error Types
// ============================================================================

export type APIErrorCode =
  | 'NETWORK_ERROR'
  | 'TIMEOUT'
  | 'SERVER_ERROR'
  | 'NOT_FOUND'
  | 'VALIDATION_ERROR'
  | 'UNKNOWN_ERROR';

export interface APIErrorDetails {
  code: APIErrorCode;
  message: string;
  originalError?: unknown;
}
