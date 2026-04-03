import { computed, type Ref } from 'vue'
import type { FamilyMember, Preference, Product, Recipe } from '@/api/types'

function resolveRecipeCategoryIds(
  recipe: Recipe,
  allRecipesById: Map<number, Recipe>,
  visited: Set<number>,
): [Set<number>, boolean] {
  if (visited.has(recipe.id)) return [new Set(), false]
  visited.add(recipe.id)
  const ids = new Set<number>()
  let hasUncategorized = false
  if (recipe.category_id === 0) {
    hasUncategorized = true
  } else {
    ids.add(recipe.category_id)
  }
  for (const ing of recipe.ingredients) {
    if (ing.sub_recipe_id != null) {
      const sub = allRecipesById.get(ing.sub_recipe_id)
      if (sub) {
        const [subIds, subUncategorized] = resolveRecipeCategoryIds(sub, allRecipesById, visited)
        subIds.forEach(id => ids.add(id))
        hasUncategorized = hasUncategorized || subUncategorized
      }
    }
  }
  visited.delete(recipe.id)
  return [ids, hasUncategorized]
}

function resolveProductIds(
  recipe: Recipe,
  allRecipesById: Map<number, Recipe>,
  visited: Set<number>,
): Set<number> {
  if (visited.has(recipe.id)) return new Set()
  visited.add(recipe.id)
  const ids = new Set<number>()
  for (const ing of recipe.ingredients) {
    if (ing.product_id != null) {
      ids.add(ing.product_id)
    } else if (ing.sub_recipe_id != null) {
      const sub = allRecipesById.get(ing.sub_recipe_id)
      if (sub) {
        resolveProductIds(sub, allRecipesById, visited).forEach(id => ids.add(id))
      }
    }
  }
  visited.delete(recipe.id)
  return ids
}

function recipeViolatesPref(
  recipe: Recipe,
  allRecipesById: Map<number, Recipe>,
  productCategoryMap: Map<number, number>,
  pref: Preference,
): boolean {
  const productIds = resolveProductIds(recipe, allRecipesById, new Set())
  const categoryIds = new Set<number>()
  let hasUncategorized = false
  for (const pid of productIds) {
    const catId = productCategoryMap.get(pid)
    if (catId === undefined || catId === 0) {
      hasUncategorized = true
    } else {
      categoryIds.add(catId)
    }
  }

  const blockedProductSet = new Set(pref.product_ids)
  const prefCategorySet = new Set(pref.category_ids)
  const prefRecipeCategorySet = new Set(pref.recipe_category_ids)

  if (pref.type === 'ALLERGY') {
    for (const pid of productIds) {
      if (blockedProductSet.has(pid)) return true
    }
    for (const cid of categoryIds) {
      if (prefCategorySet.has(cid)) return true
    }
    if (prefRecipeCategorySet.size > 0) {
      const [recipeCatIds] = resolveRecipeCategoryIds(recipe, allRecipesById, new Set())
      for (const cid of recipeCatIds) {
        if (prefRecipeCategorySet.has(cid)) return true
      }
    }
    return false
  }

  if (pref.mode === 'BLOCKED') {
    for (const cid of categoryIds) {
      if (prefCategorySet.has(cid)) return true
    }
    if (prefRecipeCategorySet.size > 0) {
      const [recipeCatIds] = resolveRecipeCategoryIds(recipe, allRecipesById, new Set())
      for (const cid of recipeCatIds) {
        if (prefRecipeCategorySet.has(cid)) return true
      }
    }
    return false
  }

  // ALLOWED mode
  const productCheckNeeded = prefCategorySet.size > 0
  const recipeCheckNeeded = prefRecipeCategorySet.size > 0

  if (!productCheckNeeded && !recipeCheckNeeded) return true

  if (productCheckNeeded) {
    if (productIds.size === 0) return true
    if (hasUncategorized) return true
    for (const cid of categoryIds) {
      if (!prefCategorySet.has(cid)) return true
    }
  }

  if (recipeCheckNeeded) {
    const [recipeCatIds, hasUncategorizedRecipe] = resolveRecipeCategoryIds(recipe, allRecipesById, new Set())
    if (hasUncategorizedRecipe) return true
    for (const cid of recipeCatIds) {
      if (!prefRecipeCategorySet.has(cid)) return true
    }
  }

  return false
}

function productViolatesPref(product: Product, pref: Preference): boolean {
  const blockedProductSet = new Set(pref.product_ids)
  const prefCategorySet = new Set(pref.category_ids)

  if (pref.type === 'ALLERGY') {
    return blockedProductSet.has(product.id) || prefCategorySet.has(product.category_id)
  }

  if (pref.mode === 'BLOCKED') {
    return prefCategorySet.has(product.category_id)
  }

  // ALLOWED mode
  return !prefCategorySet.has(product.category_id)
}

export function usePreferenceFilter(
  activeMemberIds: Ref<Set<number>>,
  members: Ref<FamilyMember[]>,
  preferences: Ref<Preference[]>,
  recipes: Ref<Recipe[]>,
  products: Ref<Product[]>,
) {
  const activePreferences = computed((): Preference[] => {
    const prefIds = new Set<number>()
    for (const memberId of activeMemberIds.value) {
      const member = members.value.find(m => m.id === memberId)
      if (member) {
        member.preference_ids.forEach(id => prefIds.add(id))
      }
    }
    return preferences.value.filter(p => prefIds.has(p.id))
  })

  const productCategoryMap = computed((): Map<number, number> => {
    const map = new Map<number, number>()
    for (const product of products.value) {
      map.set(product.id, product.category_id)
    }
    return map
  })

  const allRecipesById = computed((): Map<number, Recipe> => {
    const map = new Map<number, Recipe>()
    for (const recipe of recipes.value) {
      map.set(recipe.id, recipe)
    }
    return map
  })

  const blockedRecipeIds = computed((): Set<number> => {
    const prefs = activePreferences.value
    if (prefs.length === 0) return new Set()
    const blocked = new Set<number>()
    for (const recipe of recipes.value) {
      for (const pref of prefs) {
        if (recipeViolatesPref(recipe, allRecipesById.value, productCategoryMap.value, pref)) {
          blocked.add(recipe.id)
          break
        }
      }
    }
    return blocked
  })

  const blockedProductIds = computed((): Set<number> => {
    const prefs = activePreferences.value
    if (prefs.length === 0) return new Set()
    const blocked = new Set<number>()
    for (const product of products.value) {
      for (const pref of prefs) {
        if (productViolatesPref(product, pref)) {
          blocked.add(product.id)
          break
        }
      }
    }
    return blocked
  })

  return { blockedRecipeIds, blockedProductIds, activePreferences }
}
