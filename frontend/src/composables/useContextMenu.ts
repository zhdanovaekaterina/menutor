import { ref } from 'vue'

export interface ContextMenuItem {
  label: string
  action: () => void
}

interface ContextMenuState {
  visible: boolean
  x: number
  y: number
  items: ContextMenuItem[]
}

// Module-level singleton — one menu open across all components at a time
const state = ref<ContextMenuState>({
  visible: false,
  x: 0,
  y: 0,
  items: [],
})

export function useContextMenu() {
  function open(x: number, y: number, items: ContextMenuItem[]) {
    state.value = { visible: true, x, y, items }
  }

  function close() {
    state.value = { ...state.value, visible: false }
  }

  return { state, open, close }
}
