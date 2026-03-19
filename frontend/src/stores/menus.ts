import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  addSlot,
  clearMenu,
  createMenu,
  deleteMenu,
  fetchMenu,
  fetchMenus,
  moveSlotApi,
  removeSlot,
} from '@/api/client'
import type { Menu, MenuSlot, RemoveItemRequest } from '@/api/types'
import { useToastStore } from './toast'

export const useMenuStore = defineStore('menus', () => {
  const menus = ref<Menu[]>([])
  const selectedId = ref<number | null>(null)
  const loading = ref(false)

  const current = computed(() =>
    menus.value.find((m) => m.id === selectedId.value) ?? null,
  )

  function _updateMenu(menu: Menu) {
    const idx = menus.value.findIndex((m) => m.id === menu.id)
    if (idx !== -1) menus.value[idx] = menu
  }

  async function load() {
    loading.value = true
    try {
      menus.value = await fetchMenus()
    } catch {
      useToastStore().show('Ошибка загрузки меню', 'error')
    } finally {
      loading.value = false
    }
  }

  async function select(id: number) {
    loading.value = true
    try {
      const menu = await fetchMenu(id)
      _updateMenu(menu)
      selectedId.value = id
    } catch {
      useToastStore().show('Ошибка загрузки меню', 'error')
    } finally {
      loading.value = false
    }
  }

  async function create(name: string) {
    const menu = await createMenu(name)
    menus.value.push(menu)
    selectedId.value = menu.id
    useToastStore().show('Меню создано', 'success')
    return menu
  }

  async function remove(id: number) {
    await deleteMenu(id)
    menus.value = menus.value.filter((m) => m.id !== id)
    if (selectedId.value === id) selectedId.value = null
    useToastStore().show('Меню удалено', 'success')
  }

  async function addSlotToMenu(slot: MenuSlot) {
    if (!current.value) return
    const updated = await addSlot(current.value.id, slot)
    _updateMenu(updated)
  }

  async function removeSlotFromMenu(data: RemoveItemRequest) {
    if (!current.value) return
    const updated = await removeSlot(current.value.id, data)
    _updateMenu(updated)
  }

  async function moveSlot(slot: MenuSlot, toDay: number, toMealType: string, toPosition: number) {
    if (!current.value) return
    const updated = await moveSlotApi(current.value.id, {
      day: slot.day,
      meal_type: slot.meal_type,
      recipe_id: slot.recipe_id,
      product_id: slot.product_id,
      to_day: toDay,
      to_meal_type: toMealType,
      to_position: toPosition,
    })
    _updateMenu(updated)
  }

  async function reorderSlots(day: number, mealType: string, orderedSlots: MenuSlot[]) {
    if (!current.value) return
    let updated: Menu | null = null
    for (let i = 0; i < orderedSlots.length; i++) {
      const s: MenuSlot = { ...orderedSlots[i], day, meal_type: mealType, position: i }
      updated = await addSlot(current.value.id, s)
    }
    if (updated) _updateMenu(updated)
  }

  async function mergeItemsIntoSlot(day: number, mealType: string, items: MenuSlot[]) {
    if (!current.value) return
    for (const src of items) {
      // Remap the copied slot to target day/meal_type, preserving quantity fields
      const slot: MenuSlot = {
        ...src,
        day,
        meal_type: mealType,
      }
      // addSlot on the backend is an upsert keyed on (day, meal_type, recipe_id, product_id),
      // so calling it for an existing item overwrites quantity/servings_override,
      // and for a new item it appends it.
      await addSlotToMenu(slot)
    }
  }

  async function clear() {
    if (!current.value) return
    const updated = await clearMenu(current.value.id)
    _updateMenu(updated)
    useToastStore().show('Меню очищено', 'success')
  }

  function _autoMenuName(): string {
    const now = new Date()
    const hh = String(now.getHours()).padStart(2, '0')
    const mm = String(now.getMinutes()).padStart(2, '0')
    const dd = String(now.getDate()).padStart(2, '0')
    const mo = String(now.getMonth() + 1).padStart(2, '0')
    const yyyy = now.getFullYear()
    return `${hh}:${mm}_${dd}.${mo}.${yyyy}`
  }

  async function ensureMenuSelected(): Promise<void> {
    if (current.value) return
    await create(_autoMenuName())
  }

  return { menus, current, selectedId, loading, load, select, create, remove, addSlotToMenu, removeSlotFromMenu, moveSlot, reorderSlots, mergeItemsIntoSlot, clear, ensureMenuSelected }
})
