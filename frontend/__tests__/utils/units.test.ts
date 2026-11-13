/**
 * Unit kinds for the BOM editor (#195, TASK-FE-P9-006)
 *
 * The unit picklist offers only units of the selected emission factor's kind, and the row's
 * CO2e preview converts the quantity to the factor's unit, as the backend does
 * (backend/domain/units.py). A unit outside the table matches only itself.
 */
import { describe, it, expect } from 'vitest';
import {
  BOM_UNITS,
  unitKind,
  areUnitsCompatible,
  convertQuantity,
  unitsForFactor,
  unitForFactorChange,
} from '../../src/utils/units';

describe('unitKind', () => {
  it.each([
    ['kg', 'mass'], ['g', 'mass'], ['t', 'mass'],
    ['L', 'volume'], ['mL', 'volume'],
    ['kWh', 'energy'], ['MJ', 'energy'],
    ['tkm', 'freight'], ['unit', 'count'],
    ['m', 'length'], ['cm', 'length'],
  ])('%s is %s', (unit, kind) => {
    expect(unitKind(unit)).toBe(kind);
  });

  it('ignores case and surrounding space', () => {
    expect(unitKind(' KG ')).toBe('mass');
    expect(unitKind('kwh')).toBe('energy');
  });

  it('returns null for an unknown unit', () => {
    expect(unitKind('vehicle-mile')).toBeNull();
  });
});

describe('areUnitsCompatible', () => {
  it('accepts units of one kind and rejects others', () => {
    expect(areUnitsCompatible('g', 'kg')).toBe(true);
    expect(areUnitsCompatible('MJ', 'kWh')).toBe(true);
    expect(areUnitsCompatible('kg', 'kWh')).toBe(false);
  });

  it('matches an unknown unit only to itself', () => {
    expect(areUnitsCompatible('vehicle-mile', 'Vehicle-Mile')).toBe(true);
    expect(areUnitsCompatible('vehicle-mile', 'km')).toBe(false);
  });
});

describe('convertQuantity', () => {
  it.each([
    [500, 'g', 'kg', 0.5],
    [2, 't', 'kg', 2000],
    [750, 'mL', 'L', 0.75],
    [36, 'MJ', 'kWh', 10],
    [90, 'cm', 'm', 0.9],
    [3, 'kWh', 'kWh', 3],
  ])('%s %s is %s %s', (quantity, from, to, expected) => {
    expect(convertQuantity(quantity, from, to)).toBeCloseTo(expected, 10);
  });

  it('returns null for incompatible units', () => {
    expect(convertQuantity(1, 'kg', 'kWh')).toBeNull();
  });
});

describe('unitsForFactor', () => {
  it('offers every BOM unit when no factor is selected', () => {
    expect(unitsForFactor(undefined)).toEqual([...BOM_UNITS]);
  });

  it('offers only units of the factor unit kind', () => {
    expect(unitsForFactor('kg')).toEqual(['kg', 'g', 't']);
    expect(unitsForFactor('kWh')).toEqual(['kWh', 'MJ']);
    expect(unitsForFactor('tkm')).toEqual(['tkm']);
    expect(unitsForFactor('unit')).toEqual(['unit']);
  });

  it('offers the factor unit itself when it is not in the table', () => {
    expect(unitsForFactor('vehicle-mile')).toEqual(['vehicle-mile']);
  });

  it('includes the unit table in a fixed order', () => {
    expect([...BOM_UNITS]).toEqual(['kg', 'g', 't', 'L', 'mL', 'kWh', 'MJ', 'tkm', 'unit', 'm', 'cm']);
  });
});

describe('unitForFactorChange', () => {
  it('keeps the row unit when it converts to the new factor unit', () => {
    expect(unitForFactorChange('g', 'kg')).toBe('g');
    expect(unitForFactorChange('MJ', 'kWh')).toBe('MJ');
  });

  it("switches to the factor's unit when the row unit is of another kind", () => {
    expect(unitForFactorChange('kg', 'kWh')).toBe('kWh');
    expect(unitForFactorChange('kg', 'vehicle-mile')).toBe('vehicle-mile');
  });
});
