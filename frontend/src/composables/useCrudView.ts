import { computed, ref } from 'vue'
import type { Ref } from 'vue'
import { useSelection } from './useSelection'
import { useToastStore } from '@/stores/toast'

interface CrudStore<T extends { id: number }, C> {
  items: T[]
  load: () => Promise<void>
  create: (data: C) => Promise<T>
  update: (id: number, data: C) => Promise<T>
  remove: (id: number) => Promise<void>
  removeMany: (ids: number[]) => Promise<void>
}

export function useCrudView<T extends { id: number }, C>(store: CrudStore<T, C>) {
  const toast = useToastStore()
  const selection = useSelection()

  const selectedId = ref<number | null>(null) as Ref<number | null>
  const confirmDeleteOpen = ref(false)
  const formOpen = ref(false)
  const exportOpen = ref(false)
  const importOpen = ref(false)
  const confirmBatchDeleteOpen = ref(false)
  const confirmDeleteAllOpen = ref(false)

  const selectedItem = computed(() =>
    store.items.find((item) => item.id === selectedId.value) ?? null,
  )

  function onSelect(id: number) {
    selectedId.value = id
    formOpen.value = true
  }

  function openNew() {
    selectedId.value = null
    formOpen.value = true
  }

  async function onSave(data: C, id: number | null) {
    try {
      if (id) {
        await store.update(id, data)
      } else {
        const created = await store.create(data)
        selectedId.value = created.id
      }
      formOpen.value = false
    } catch (e: any) {
      toast.show(e?.response?.data?.detail ?? 'Ошибка сохранения', 'error')
    }
  }

  function onRemove(id: number) {
    selectedId.value = id
    confirmDeleteOpen.value = true
  }

  async function onConfirmDelete() {
    confirmDeleteOpen.value = false
    if (!selectedId.value) return
    try {
      await store.remove(selectedId.value)
      selectedId.value = null
      formOpen.value = false
    } catch (e: any) {
      toast.show(e?.response?.data?.detail ?? 'Ошибка удаления', 'error')
    }
  }

  function onClear() {
    selectedId.value = null
    formOpen.value = false
  }

  function toggleSelectMode() {
    if (selection.active.value) selection.exit()
    else { selection.enter(); formOpen.value = false }
  }

  async function onConfirmBatchDelete() {
    confirmBatchDeleteOpen.value = false
    const ids = [...selection.selected.value]
    try {
      await store.removeMany(ids)
      selection.clear()
    } catch (e: any) {
      toast.show(e?.response?.data?.detail ?? 'Ошибка удаления', 'error')
    }
  }

  async function onConfirmDeleteAll() {
    confirmDeleteAllOpen.value = false
    const ids = store.items.map((item) => item.id)
    try {
      await store.removeMany(ids)
      selection.exit()
    } catch (e: any) {
      toast.show(e?.response?.data?.detail ?? 'Ошибка удаления', 'error')
    }
  }

  return {
    selection,
    selectedId,
    selectedItem,
    confirmDeleteOpen,
    formOpen,
    exportOpen,
    importOpen,
    confirmBatchDeleteOpen,
    confirmDeleteAllOpen,
    onSelect,
    openNew,
    onSave,
    onRemove,
    onConfirmDelete,
    onClear,
    toggleSelectMode,
    onConfirmBatchDelete,
    onConfirmDeleteAll,
  }
}
