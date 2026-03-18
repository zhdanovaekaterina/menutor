/**
 * Unit groups and base-unit multipliers — mirrors backend quantity.py.
 *
 * _TO_BASE: how many base units one unit of this kind equals
 *   (g and ml are base units for weight and volume respectively).
 */

const UNIT_GROUP: Record<string, string> = {
  g: 'weight',
  kg: 'weight',
  ml: 'volume',
  l: 'volume',
  tsp: 'volume',
  tbsp: 'volume',
  pcs: 'count_pcs',
  box: 'count_box',
  pack: 'count_pack',
  serv: 'servings',
}

const TO_BASE: Record<string, number> = {
  g: 1,
  kg: 1000,
  ml: 1,
  l: 1000,
  tsp: 5,
  tbsp: 15,
  pcs: 1,
  box: 1,
  pack: 1,
  serv: 1,
}

/**
 * Returns the fixed conversion factor when both units belong to the same
 * group, or `null` when the units are from different groups (user must
 * enter the factor manually).
 *
 * conversion_factor semantics: recipe_amount / factor = purchase_amount
 *   → factor = TO_BASE[purchaseUnit] / TO_BASE[recipeUnit]
 */
export function autoConversionFactor(recipeUnit: string, purchaseUnit: string): number | null {
  const rg = UNIT_GROUP[recipeUnit]
  const pg = UNIT_GROUP[purchaseUnit]
  if (!rg || !pg || rg !== pg) return null
  return TO_BASE[purchaseUnit]! / TO_BASE[recipeUnit]!
}
