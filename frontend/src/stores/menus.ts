import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  addSlot,
  clearMenu,
  createMenu,
  deleteMenu,
  fetchMenu,
  fetchMenus,
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

  async function clear() {
    if (!current.value) return
    const updated = await clearMenu(current.value.id)
    _updateMenu(updated)
    useToastStore().show('Меню очищено', 'success')
  }

  return { menus, current, selectedId, loading, load, select, create, remove, addSlotToMenu, removeSlotFromMenu, clear }
})
