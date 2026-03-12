import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  createProduct,
  deleteProduct,
  fetchProductCategories,
  fetchProducts,
  updateProduct,
} from '@/api/client'
import type { ActiveCategory, Product, ProductCreate } from '@/api/types'
import { useToastStore } from './toast'

export const useProductStore = defineStore('products', () => {
  const products = ref<Product[]>([])
  const categories = ref<ActiveCategory[]>([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      ;[products.value, categories.value] = await Promise.all([
        fetchProducts(),
        fetchProductCategories(),
      ])
    } catch {
      useToastStore().show('Ошибка загрузки продуктов', 'error')
    } finally {
      loading.value = false
    }
  }

  async function create(data: ProductCreate) {
    const product = await createProduct(data)
    products.value.push(product)
    useToastStore().show('Продукт создан', 'success')
    return product
  }

  async function update(id: number, data: ProductCreate) {
    const product = await updateProduct(id, data)
    const idx = products.value.findIndex((p) => p.id === id)
    if (idx !== -1) products.value[idx] = product
    useToastStore().show('Продукт обновлён', 'success')
    return product
  }

  async function remove(id: number) {
    await deleteProduct(id)
    products.value = products.value.filter((p) => p.id !== id)
    useToastStore().show('Продукт удалён', 'success')
  }

  return { products, categories, loading, load, create, update, remove }
})
