import {
  batchDeleteProducts,
  createProduct,
  deleteProduct,
  fetchProductCategories,
  fetchProducts,
  updateProduct,
} from '@/api/client'
import type { Product, ProductCreate } from '@/api/types'
import { createCrudStore } from './crud-factory'

export const useProductStore = createCrudStore<Product, ProductCreate>('products', {
  fetchAll: fetchProducts,
  fetchCategories: fetchProductCategories,
  createItem: createProduct,
  updateItem: updateProduct,
  deleteItem: deleteProduct,
  batchDeleteItems: batchDeleteProducts,
  messages: {
    loadError: 'Ошибка загрузки продуктов',
    created: 'Продукт создан',
    updated: 'Продукт обновлён',
    deleted: 'Продукт удалён',
    batchDeleted: 'Продукты удалены',
  },
})
