import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Ref } from 'vue'
import type { ActiveCategory } from '@/api/types'
import { useToastStore } from './toast'

interface CrudStoreOptions<T, C> {
  fetchAll: () => Promise<T[]>
  fetchCategories?: () => Promise<ActiveCategory[]>
  createItem: (data: C) => Promise<T>
  updateItem: (id: number, data: C) => Promise<T>
  deleteItem: (id: number) => Promise<unknown>
  messages: {
    loadError: string
    created: string
    updated: string
    deleted: string
  }
}

export function createCrudStore<T extends { id: number }, C>(
  name: string,
  options: CrudStoreOptions<T, C>,
) {
  return defineStore(name, () => {
    const items = ref<T[]>([]) as Ref<T[]>
    const categories = ref<ActiveCategory[]>([])
    const loading = ref(false)

    async function load() {
      loading.value = true
      try {
        if (options.fetchCategories) {
          ;[items.value, categories.value] = await Promise.all([
            options.fetchAll(),
            options.fetchCategories(),
          ])
        } else {
          items.value = await options.fetchAll()
        }
      } catch {
        useToastStore().show(options.messages.loadError, 'error')
      } finally {
        loading.value = false
      }
    }

    async function create(data: C) {
      const item = await options.createItem(data)
      items.value.push(item)
      useToastStore().show(options.messages.created, 'success')
      return item
    }

    async function update(id: number, data: C) {
      const item = await options.updateItem(id, data)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx] = item
      useToastStore().show(options.messages.updated, 'success')
      return item
    }

    async function remove(id: number) {
      await options.deleteItem(id)
      items.value = items.value.filter((i) => i.id !== id)
      useToastStore().show(options.messages.deleted, 'success')
    }

    return { items, categories, loading, load, create, update, remove }
  })
}
