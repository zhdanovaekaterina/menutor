import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { MealType, MealTypeCreate, MealTypeUsageResponse } from '@/api/types'
import {
  createMealType,
  deleteMealType,
  fetchMealTypes,
  fetchMealTypeUsage,
  updateMealType,
} from '@/api/client'
import { useToastStore } from './toast'

export const useMealTypeStore = defineStore('mealTypes', () => {
  const items = ref<MealType[]>([])
  const loading = ref(false)

  const sorted = computed(() =>
    [...items.value].sort((a, b) => {
      if (a.time !== b.time) return a.time.localeCompare(b.time)
      if (a.sort_order !== b.sort_order) return a.sort_order - b.sort_order
      return a.id - b.id
    }),
  )

  const customCount = computed(() =>
    items.value.filter((t) => !t.is_system).length,
  )

  async function load() {
    loading.value = true
    try {
      items.value = await fetchMealTypes()
    } catch {
      useToastStore().show('Ошибка загрузки типов приемов пищи', 'error')
    } finally {
      loading.value = false
    }
  }

  async function create(data: MealTypeCreate): Promise<MealType | null> {
    try {
      const mt = await createMealType(data)
      items.value.push(mt)
      useToastStore().show('Тип приема пищи создан', 'success')
      return mt
    } catch (e: any) {
      const msg = e.response?.data?.detail ?? 'Ошибка создания'
      useToastStore().show(msg, 'error')
      return null
    }
  }

  async function update(id: number, data: MealTypeCreate): Promise<MealType | null> {
    try {
      const mt = await updateMealType(id, data)
      const idx = items.value.findIndex((t) => t.id === id)
      if (idx !== -1) items.value[idx] = mt
      useToastStore().show('Тип приема пищи обновлён', 'success')
      return mt
    } catch (e: any) {
      const msg = e.response?.data?.detail ?? 'Ошибка обновления'
      useToastStore().show(msg, 'error')
      return null
    }
  }

  async function remove(id: number): Promise<boolean> {
    try {
      await deleteMealType(id)
      items.value = items.value.filter((t) => t.id !== id)
      useToastStore().show('Тип приема пищи удалён', 'success')
      return true
    } catch (e: any) {
      const msg = e.response?.data?.detail ?? 'Ошибка удаления'
      useToastStore().show(msg, 'error')
      return false
    }
  }

  async function checkUsage(id: number): Promise<MealTypeUsageResponse | null> {
    try {
      return await fetchMealTypeUsage(id)
    } catch {
      useToastStore().show('Ошибка проверки использования', 'error')
      return null
    }
  }

  return { items, sorted, customCount, loading, load, create, update, remove, checkUsage }
})
