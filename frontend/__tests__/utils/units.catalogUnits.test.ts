/**
 * Units used by catalog emission factors (TASK-FE-P9-007, #195 follow-up)
 *
 * Ship freight rows (tkm) use EPA's "short ton-mile" factor, process water rows (L) DEFRA's
 * "cubic metres", DEFRA fuels "kWh (Gross CV)". These convert within their kind, mirroring
 * backend/domain/units.py. The picklist for such a factor offers the editor's units of that
 * kind plus the factor's own unit. "vehicle-mile" has no conversion from tkm.
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

const TKM_PER_SHORT_TON_MILE = 0.90718474 * 1.609344;

describe('catalog factor units', () => {
  it.each([
    ['short ton-mile', 'freight'],
    ['cubic metres', 'volume'],
    ['m3', 'volume'],
    ['kWh (Gross CV)', 'energy'],
    ['kWh (Net CV)', 'energy'],
  ])('%s is %s', (unit, kind) => {
    expect(unitKind(unit)).toBe(kind);
  });

  it('converts tkm to short ton-miles and litres to cubic metres', () => {
    expect(convertQuantity(TKM_PER_SHORT_TON_MILE, 'tkm', 'short ton-mile')).toBeCloseTo(1, 10);
    expect(convertQuantity(250, 'L', 'cubic metres')).toBeCloseTo(0.25, 10);
    expect(convertQuantity(3.6, 'MJ', 'kWh (Gross CV)')).toBeCloseTo(1, 10);
  });

  it('keeps vehicle-mile apart from freight', () => {
    expect(areUnitsCompatible('tkm', 'vehicle-mile')).toBe(false);
  });

  it("offers the editor's units of the kind plus the factor's own unit", () => {
    expect(unitsForFactor('short ton-mile')).toEqual(['tkm', 'short ton-mile']);
    expect(unitsForFactor('cubic metres')).toEqual(['L', 'mL', 'cubic metres']);
    expect(unitsForFactor('kWh (Gross CV)')).toEqual(['kWh', 'MJ', 'kWh (Gross CV)']);
  });

  it('keeps a convertible row unit when such a factor is chosen', () => {
    expect(unitForFactorChange('tkm', 'short ton-mile')).toBe('tkm');
    expect(unitForFactorChange('L', 'cubic metres')).toBe('L');
  });

  it("doesn't add catalog-only units to the full picklist", () => {
    expect(BOM_UNITS).not.toContain('short ton-mile');
    expect(BOM_UNITS).not.toContain('cubic metres');
  });
});
