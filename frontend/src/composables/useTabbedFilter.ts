import { computed, ref } from 'vue'
import type { Ref } from 'vue'
import { useCategoryFilter } from './useCategoryFilter'

interface Filterable {
  category_id: number
  name: string
}

export function useTabbedFilter<R extends Filterable, P extends Filterable>(
  recipesRef: Ref<R[]> | (() => R[]),
  productsRef: Ref<P[]> | (() => P[]),
  options?: { defaultTab?: 'recipes' | 'products' },
) {
  const tab = ref<'recipes' | 'products'>(options?.defaultTab ?? 'recipes')
  const search = ref('')
  const recipeCF = useCategoryFilter<R>()
  const productCF = useCategoryFilter<P>()

  function switchTab(next: 'recipes' | 'products') {
    tab.value = next
    search.value = ''
    recipeCF.reset()
    productCF.reset()
  }

  const getRecipes = typeof recipesRef === 'function' ? recipesRef : () => recipesRef.value
  const getProducts = typeof productsRef === 'function' ? productsRef : () => productsRef.value

  const filteredRecipes = computed(() =>
    recipeCF.applyFilter(getRecipes(), search.value).sort((a, b) => a.name.localeCompare(b.name)),
  )
  const filteredProducts = computed(() =>
    productCF.applyFilter(getProducts(), search.value).sort((a, b) => a.name.localeCompare(b.name)),
  )

  return {
    tab,
    search,
    recipeCF,
    productCF,
    switchTab,
    filteredRecipes,
    filteredProducts,
  }
}
