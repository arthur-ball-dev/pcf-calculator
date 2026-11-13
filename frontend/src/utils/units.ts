/**
 * Unit kinds for the BOM editor (#195, TASK-FE-P9-006)
 *
 * A BOM row's quantity is converted to its emission factor's unit, within a kind (mass, volume,
 * energy, freight, count, length). The unit picklist offers only units of the selected factor's
 * kind, so a row can't be given a unit the calculation can't convert. A unit outside the table
 * (for example a raw EPA string such as "vehicle-mile") matches only itself.
 *
 * Mirrors backend/domain/units.py, which applies the same table when calculating; keep the two
 * in step.
 */

type UnitKind = 'mass' | 'volume' | 'energy' | 'freight' | 'count' | 'length';

/** kind -> [unit, size in the kind's base unit], in picklist order */
const UNIT_TABLE: Record<UnitKind, ReadonlyArray<readonly [string, number]>> = {
  mass: [['kg', 1], ['g', 0.001], ['t', 1000]],
  volume: [['L', 1], ['mL', 0.001]],
  energy: [['kWh', 1], ['MJ', 1 / 3.6]],
  freight: [['tkm', 1]],
  count: [['unit', 1]],
  length: [['m', 1], ['cm', 0.01]],
};

/** Every unit the BOM editor offers, in picklist order */
export const BOM_UNITS: readonly string[] = Object.values(UNIT_TABLE).flatMap((units) =>
  units.map(([unit]) => unit),
);

/**
 * Units catalog emission factors use that the editor doesn't offer on its own (EPA "short
 * ton-mile", DEFRA "cubic metres" and "kWh (Gross CV)"): rows convert to them, and a factor in
 * one of them adds it to that row's picklist. "vehicle-mile" (distance driven) is deliberately
 * absent: freight in tkm doesn't convert to it.
 */
const CATALOG_UNITS: ReadonlyArray<readonly [string, UnitKind, number]> = [
  ['short ton-mile', 'freight', 0.90718474 * 1.609344],
  ['cubic metres', 'volume', 1000],
  ['cubic meters', 'volume', 1000],
  ['m3', 'volume', 1000],
  ['kWh (Gross CV)', 'energy', 1],
  ['kWh (Net CV)', 'energy', 1],
];

const ENTRIES = new Map<string, { kind: UnitKind; size: number; unit: string }>([
  ...(Object.entries(UNIT_TABLE) as Array<[UnitKind, ReadonlyArray<readonly [string, number]>]>).flatMap(
    ([kind, units]) => units.map(([unit, size]) => [unit.toLowerCase(), { kind, size, unit }] as const),
  ),
  ...CATALOG_UNITS.map(([unit, kind, size]) => [unit.toLowerCase(), { kind, size, unit }] as const),
]);

const key = (unit: string): string => unit.trim().toLowerCase();

/** The kind of a unit, or null if it is not in the table */
export function unitKind(unit: string): UnitKind | null {
  return ENTRIES.get(key(unit))?.kind ?? null;
}

/** Whether a quantity in `from` can be converted to `to` */
export function areUnitsCompatible(from: string, to: string): boolean {
  const a = ENTRIES.get(key(from));
  const b = ENTRIES.get(key(to));
  if (!a || !b) return key(from) === key(to);
  return a.kind === b.kind;
}

/** Convert a quantity between compatible units; null if they are not compatible */
export function convertQuantity(quantity: number, from: string, to: string): number | null {
  if (!areUnitsCompatible(from, to)) return null;
  const a = ENTRIES.get(key(from));
  const b = ENTRIES.get(key(to));
  if (!a || !b) return quantity;
  return (quantity * a.size) / b.size;
}

/** The units a row may use with a factor of this unit; every unit when there is no factor */
export function unitsForFactor(factorUnit: string | undefined | null): string[] {
  if (!factorUnit) return [...BOM_UNITS];
  const entry = ENTRIES.get(key(factorUnit));
  if (!entry) return [factorUnit];
  const editorUnits = UNIT_TABLE[entry.kind].map(([unit]) => unit);
  // A catalog-only factor unit is offered too, so the row can use the factor's own unit
  return editorUnits.some((unit) => key(unit) === key(factorUnit)) ? editorUnits : [...editorUnits, factorUnit];
}

/** The row's unit after choosing a factor: kept if convertible, else the factor's own unit */
export function unitForFactorChange(rowUnit: string, factorUnit: string): string {
  if (areUnitsCompatible(rowUnit, factorUnit)) return rowUnit;
  return ENTRIES.get(key(factorUnit))?.unit ?? factorUnit;
}
