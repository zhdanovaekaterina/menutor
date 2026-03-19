import { computed, ref } from 'vue'
import type { MenuSlot } from '@/api/types'

// Module-level singleton — one clipboard shared across all grid cells
const clipboardItems = ref<MenuSlot[] | null>(null)

export function usePlannerClipboard() {
  const hasClipboard = computed(
    () => clipboardItems.value !== null && clipboardItems.value.length > 0,
  )

  function copySlot(items: MenuSlot[]): void {
    // Deep-copy so later mutations to the source slot don't affect the buffer
    clipboardItems.value = items.map((s) => ({ ...s }))
  }

  function pasteSlot(): MenuSlot[] | null {
    return clipboardItems.value
  }

  return { hasClipboard, copySlot, pasteSlot }
}
