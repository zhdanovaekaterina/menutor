import {
  createFamilyMember,
  deleteFamilyMember,
  fetchFamilyMembers,
  updateFamilyMember,
} from '@/api/client'
import type { FamilyMember, FamilyMemberCreate } from '@/api/types'
import { createCrudStore } from './crud-factory'

export const useFamilyStore = createCrudStore<FamilyMember, FamilyMemberCreate>('family', {
  fetchAll: fetchFamilyMembers,
  createItem: createFamilyMember,
  updateItem: updateFamilyMember,
  deleteItem: deleteFamilyMember,
  messages: {
    loadError: 'Ошибка загрузки семьи',
    created: 'Член семьи добавлен',
    updated: 'Данные обновлены',
    deleted: 'Член семьи удалён',
  },
})
