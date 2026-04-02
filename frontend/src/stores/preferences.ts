import type { Preference, PreferenceCreate } from '@/api/types'
import {
  createPreference,
  deletePreference,
  fetchPreferences,
  updatePreference,
} from '@/api/client'
import { createCrudStore } from './crud-factory'

export const usePreferencesStore = createCrudStore<Preference, PreferenceCreate>(
  'preferences',
  {
    fetchAll: fetchPreferences,
    createItem: createPreference,
    updateItem: updatePreference,
    deleteItem: deletePreference,
    messages: {
      loadError: 'Ошибка загрузки предпочтений',
      created: 'Предпочтение добавлено',
      updated: 'Предпочтение обновлено',
      deleted: 'Предпочтение удалено',
    },
  },
)
