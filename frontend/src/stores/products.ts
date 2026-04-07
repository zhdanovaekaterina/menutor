import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { ActiveCategory, Product, ProductCreate } from '@/api/types'
import {
  batchDeleteProducts,
  createProduct,
  deleteProduct,
  fetchProductCategories,
  fetchProducts,
  updateProduct,
} from '@/api/client'
import { PAGE_SIZE } from '@/utils/pagination'
import { useToastStore } from './toast'

export const useProductStore = defineStore('products', () => {
  const items = ref<Product[]>([])
  const allItems = ref<Product[]>([])
  const categories = ref<ActiveCategory[]>([])
  const loading = ref(false)
  const page = ref(1)
  const total = ref(0)
  const pageSize = ref(PAGE_SIZE)
  const search = ref('')
  const categoryId = ref<number | null>(null)

  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

  async function _loadPage() {
    const data = await fetchProducts({
      page: page.value,
      search: search.value || undefined,
      categoryId: categoryId.value ?? undefined,
    })
    items.value = data.items
    total.value = data.total
    pageSize.value = data.page_size || PAGE_SIZE
  }

  async function _loadAll() {
    const data = await fetchProducts()
    allItems.value = data.items
  }

  async function load() {
    loading.value = true
    try {
      const [, cats] = await Promise.all([
        Promise.all([_loadPage(), _loadAll()]),
        fetchProductCategories(),
      ])
      categories.value = cats
    } catch {
      useToastStore().show('Ошибка загрузки продуктов', 'error')
    } finally {
      loading.value = false
    }
  }

  async function setPage(p: number) {
    page.value = p
    loading.value = true
    try {
      await _loadPage()
    } catch {
      useToastStore().show('Ошибка загрузки продуктов', 'error')
    } finally {
      loading.value = false
    }
  }

  async function setFilters(newSearch: string, newCategoryId: number | null) {
    search.value = newSearch
    categoryId.value = newCategoryId
    page.value = 1
    loading.value = true
    try {
      await _loadPage()
    } catch {
      useToastStore().show('Ошибка загрузки продуктов', 'error')
    } finally {
      loading.value = false
    }
  }

  async function create(data: ProductCreate): Promise<Product> {
    const item = await createProduct(data)
    await Promise.all([_loadPage(), _loadAll()])
    useToastStore().show('Продукт создан', 'success')
    return item
  }

  async function update(id: number, data: ProductCreate): Promise<Product> {
    const item = await updateProduct(id, data)
    await Promise.all([_loadPage(), _loadAll()])
    useToastStore().show('Продукт обновлён', 'success')
    return item
  }

  async function remove(id: number) {
    await deleteProduct(id)
    await Promise.all([_loadPage(), _loadAll()])
    useToastStore().show('Продукт удалён', 'success')
  }

  async function removeMany(ids: number[]) {
    if (!ids.length) return
    await batchDeleteProducts(ids)
    await Promise.all([_loadPage(), _loadAll()])
    useToastStore().show('Продукты удалены', 'success')
  }

  async function patchPrice(id: number, priceAmount: number): Promise<void> {
    const product = allItems.value.find((p) => p.id === id)
    if (!product) return
    const updated = await updateProduct(id, {
      name: product.name,
      category_id: product.category_id,
      recipe_unit: product.recipe_unit,
      purchase_unit: product.purchase_unit,
      price_amount: priceAmount.toFixed(2),
      price_currency: product.price_currency,
      brand: product.brand,
      supplier: product.supplier,
      conversion_factor: product.conversion_factor,
    })
    // Update in-place without full reload
    const allIdx = allItems.value.findIndex((p) => p.id === id)
    if (allIdx !== -1) allItems.value[allIdx] = updated
    const pageIdx = items.value.findIndex((p) => p.id === id)
    if (pageIdx !== -1) items.value[pageIdx] = updated
  }

  async function removeAll() {
    const ids = allItems.value.map((i) => i.id)
    if (!ids.length) return
    await batchDeleteProducts(ids)
    await Promise.all([_loadPage(), _loadAll()])
    useToastStore().show('Продукты удалены', 'success')
  }

  return {
    items,
    allItems,
    categories,
    loading,
    page,
    total,
    pageSize,
    totalPages,
    search,
    categoryId,
    load,
    setPage,
    setFilters,
    create,
    update,
    patchPrice,
    remove,
    removeMany,
    removeAll,
  }
})
