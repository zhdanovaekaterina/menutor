import { describe, expect, it, vi } from 'vitest'
import { useCrudView } from '../useCrudView'

// Mock pinia stores
vi.mock('@/stores/toast', () => ({
  useToastStore: () => ({ show: vi.fn() }),
}))

function makeMockStore() {
  const items = [
    { id: 1, name: 'A' },
    { id: 2, name: 'B' },
  ]
  return {
    items,
    load: vi.fn(),
    create: vi.fn().mockResolvedValue({ id: 3, name: 'C' }),
    update: vi.fn().mockResolvedValue({ id: 1, name: 'A2' }),
    remove: vi.fn(),
    removeMany: vi.fn(),
  }
}

describe('useCrudView', () => {
  it('onSelect sets selectedId and opens form', () => {
    const store = makeMockStore()
    const { onSelect, selectedId, formOpen } = useCrudView(store)
    onSelect(1)
    expect(selectedId.value).toBe(1)
    expect(formOpen.value).toBe(true)
  })

  it('openNew clears selectedId and opens form', () => {
    const store = makeMockStore()
    const { openNew, selectedId, formOpen } = useCrudView(store)
    selectedId.value = 5
    openNew()
    expect(selectedId.value).toBeNull()
    expect(formOpen.value).toBe(true)
  })

  it('onClear resets state', () => {
    const store = makeMockStore()
    const { onClear, selectedId, formOpen } = useCrudView(store)
    selectedId.value = 1
    formOpen.value = true
    onClear()
    expect(selectedId.value).toBeNull()
    expect(formOpen.value).toBe(false)
  })

  it('onSave calls update when id is provided', async () => {
    const store = makeMockStore()
    const { onSave, formOpen } = useCrudView(store)
    formOpen.value = true
    await onSave({ name: 'Updated' } as any, 1)
    expect(store.update).toHaveBeenCalledWith(1, { name: 'Updated' })
    expect(formOpen.value).toBe(false)
  })

  it('onSave calls create when id is null', async () => {
    const store = makeMockStore()
    const { onSave, selectedId, formOpen } = useCrudView(store)
    formOpen.value = true
    await onSave({ name: 'New' } as any, null)
    expect(store.create).toHaveBeenCalledWith({ name: 'New' })
    expect(selectedId.value).toBe(3)
    expect(formOpen.value).toBe(false)
  })

  it('toggleSelectMode enters and exits selection mode', () => {
    const store = makeMockStore()
    const { toggleSelectMode, selection, formOpen } = useCrudView(store)
    formOpen.value = true
    toggleSelectMode()
    expect(selection.active.value).toBe(true)
    expect(formOpen.value).toBe(false)
    toggleSelectMode()
    expect(selection.active.value).toBe(false)
  })
})
