import { defineStore } from 'pinia'
import { ref } from 'vue'
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
  const current = ref<Menu | null>(null)
  const loading = ref(false)

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
      current.value = await fetchMenu(id)
    } catch {
      useToastStore().show('Ошибка загрузки меню', 'error')
    } finally {
      loading.value = false
    }
  }

  async function create(name: string) {
    const menu = await createMenu(name)
    menus.value.push(menu)
    current.value = menu
    useToastStore().show('Меню создано', 'success')
    return menu
  }

  async function remove(id: number) {
    await deleteMenu(id)
    menus.value = menus.value.filter((m) => m.id !== id)
    if (current.value?.id === id) current.value = null
    useToastStore().show('Меню удалено', 'success')
  }

  async function addSlotToMenu(slot: MenuSlot) {
    if (!current.value) return
    current.value = await addSlot(current.value.id, slot)
  }

  async function removeSlotFromMenu(data: RemoveItemRequest) {
    if (!current.value) return
    current.value = await removeSlot(current.value.id, data)
  }

  async function clear() {
    if (!current.value) return
    current.value = await clearMenu(current.value.id)
    useToastStore().show('Меню очищено', 'success')
  }

  return { menus, current, loading, load, select, create, remove, addSlotToMenu, removeSlotFromMenu, clear }
})
