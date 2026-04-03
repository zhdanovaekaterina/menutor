import type { MealIngredient, MealSummaryResponse } from '@/api/types'
import type { NestedRecipeSummary } from '@/components/summary/NestedRecipeCard.vue'
import { formatUnit } from '@/utils/units'

const DAY_LABELS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
const SEP_THICK = '='.repeat(72)
const SEP_THIN = '-'.repeat(72)

function fmtServings(n: number): string {
  return String(Math.round(n * 10) / 10)
}

function fmtQty(n: number): string {
  return String(Math.round(n * 100) / 100)
}

function renderIngredients(ingredients: MealIngredient[], indent: string): string[] {
  return ingredients.map((ing) => {
    const name =
      ing.sub_recipe_id != null
        ? `[↳ ${ing.sub_recipe_name ?? 'Вложенный рецепт'}]`
        : ing.product_name
    return `${indent}• ${name} — ${fmtQty(ing.quantity_amount)} ${formatUnit(ing.quantity_unit)}`
  })
}

export function buildSummaryText(
  summary: MealSummaryResponse,
  selectedSlotsByRecipe: Map<number, Set<number>>,
  recipeIngredients: Map<number, MealIngredient[]>,
  nestedRecipes: NestedRecipeSummary[],
  deselectedSubRecipes: Set<number>,
  mealTypeNames: Record<number, string> = {},
): string {
  const date = new Date().toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
  const lines: string[] = []

  lines.push(SEP_THICK)
  lines.push('ПЛАН ПРИГОТОВЛЕНИЯ')
  lines.push(`Меню: ${summary.menu_name}`)
  lines.push(`Дата: ${date}`)
  lines.push(SEP_THICK)

  // ── Recipes ────────────────────────────────────────────────────────────────
  const selectedRecipes = summary.recipes.filter((r) => {
    const sel = selectedSlotsByRecipe.get(r.recipe_id) ?? new Set()
    return sel.size > 0
  })

  if (selectedRecipes.length > 0) {
    lines.push('')
    lines.push(`РЕЦЕПТЫ (${selectedRecipes.length})`)
    lines.push(SEP_THIN)

    for (let i = 0; i < selectedRecipes.length; i++) {
      const recipe = selectedRecipes[i]!
      if (i > 0) {
        lines.push('')
        lines.push(SEP_THIN)
      }

      const selectedSlots = selectedSlotsByRecipe.get(recipe.recipe_id) ?? new Set()
      const selectedOccs = recipe.occurrences.filter((o) => selectedSlots.has(o.slot_index))
      const totalServings = selectedOccs.reduce((sum, o) => sum + o.servings, 0)

      lines.push('')
      lines.push(`[${i + 1}] ${recipe.recipe_name.toUpperCase()}`)

      if (recipe.pieces_info) {
        const totalPieces = Math.round(totalServings * recipe.pieces_info.pieces_per_portion)
        lines.push(`    Итого: ${totalPieces} шт. (${fmtServings(totalServings)} порц.)`)
      } else {
        lines.push(`    Итого: ${fmtServings(totalServings)} порц.`)
      }

      lines.push('')
      lines.push('    Приёмы пищи:')
      for (const occ of selectedOccs) {
        const day = DAY_LABELS[occ.day] ?? String(occ.day)
        const mealName = mealTypeNames[occ.meal_type_id] ?? `#${occ.meal_type_id}`
        if (recipe.pieces_info) {
          const pcs = Math.round(occ.servings * recipe.pieces_info.pieces_per_portion)
          lines.push(`    • ${day}, ${mealName} — ${pcs} шт. (${fmtServings(occ.servings)} порц.)`)
        } else {
          lines.push(`    • ${day}, ${mealName} — ${fmtServings(occ.servings)} порц.`)
        }
      }

      lines.push('')
      const scaledIngs = recipeIngredients.get(recipe.recipe_id) ?? []
      lines.push('    Ингредиенты:')
      if (scaledIngs.length > 0) {
        for (const line of renderIngredients(scaledIngs, '    ')) {
          lines.push(line)
        }
      } else {
        lines.push('    (нет)')
      }
    }
    lines.push('')
  }

  // ── Nested (sub) recipes ───────────────────────────────────────────────────
  const activeNested = nestedRecipes.filter((n) => !deselectedSubRecipes.has(n.sub_recipe_id))

  if (activeNested.length > 0) {
    lines.push('')
    lines.push(SEP_THICK)
    lines.push(`ВЛОЖЕННЫЕ РЕЦЕПТЫ (${activeNested.length})`)
    lines.push(SEP_THIN)

    for (let i = 0; i < activeNested.length; i++) {
      const nested = activeNested[i]!
      if (i > 0) {
        lines.push('')
        lines.push(SEP_THIN)
      }

      lines.push('')
      lines.push(`[${i + 1}] ${nested.sub_recipe_name.toUpperCase()}`)
      lines.push(
        `    Количество: ${fmtQty(nested.total_quantity_amount)} ${formatUnit(nested.quantity_unit)}`,
      )
      lines.push('')
      lines.push('    Ингредиенты:')
      if (nested.ingredients.length > 0) {
        for (const line of renderIngredients(nested.ingredients, '    ')) {
          lines.push(line)
        }
      } else {
        lines.push('    (нет)')
      }
    }
    lines.push('')
  }

  // ── Standalone products ────────────────────────────────────────────────────
  if (summary.products.length > 0) {
    lines.push('')
    lines.push(SEP_THICK)
    lines.push(`ОТДЕЛЬНЫЕ ПРОДУКТЫ (${summary.products.length})`)
    lines.push(SEP_THIN)

    for (let i = 0; i < summary.products.length; i++) {
      const product = summary.products[i]!
      if (i > 0) {
        lines.push('')
        lines.push(SEP_THIN)
      }

      lines.push('')
      lines.push(`[${i + 1}] ${product.product_name.toUpperCase()}`)
      lines.push(`    Итого: ${fmtQty(product.total_quantity)} ${formatUnit(product.unit)}`)
      lines.push('')
      lines.push('    Приёмы пищи:')
      for (const occ of product.occurrences) {
        const day = DAY_LABELS[occ.day] ?? String(occ.day)
        const mealName = mealTypeNames[occ.meal_type_id] ?? `#${occ.meal_type_id}`
        lines.push(`    • ${day}, ${mealName} — ${fmtQty(occ.quantity)} ${formatUnit(occ.unit)}`)
      }
    }
    lines.push('')
  }

  lines.push(SEP_THICK)
  return lines.join('\n')
}

export function getSummaryFilename(menuName: string): string {
  const safe = menuName.replace(/[^\wа-яёА-ЯЁ _-]/gu, '').replace(/\s+/g, '_') || 'menu'
  return `plan_${safe}.txt`
}
