import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  createFamilyMember,
  deleteFamilyMember,
  fetchFamilyMembers,
  updateFamilyMember,
} from '@/api/client'
import type { FamilyMember, FamilyMemberCreate } from '@/api/types'
import { useToastStore } from './toast'

export const useFamilyStore = defineStore('family', () => {
  const members = ref<FamilyMember[]>([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      members.value = await fetchFamilyMembers()
    } catch {
      useToastStore().show('Ошибка загрузки семьи', 'error')
    } finally {
      loading.value = false
    }
  }

  async function create(data: FamilyMemberCreate) {
    const member = await createFamilyMember(data)
    members.value.push(member)
    useToastStore().show('Член семьи добавлен', 'success')
    return member
  }

  async function update(id: number, data: FamilyMemberCreate) {
    const member = await updateFamilyMember(id, data)
    const idx = members.value.findIndex((m) => m.id === id)
    if (idx !== -1) members.value[idx] = member
    useToastStore().show('Данные обновлены', 'success')
    return member
  }

  async function remove(id: number) {
    await deleteFamilyMember(id)
    members.value = members.value.filter((m) => m.id !== id)
    useToastStore().show('Член семьи удалён', 'success')
  }

  return { members, loading, load, create, update, remove }
})
