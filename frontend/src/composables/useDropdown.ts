import { ref } from 'vue'
import type { Ref } from 'vue'
import { useClickOutside } from './useClickOutside'

/**
 * Provides open/toggle/close state for a dropdown.
 * Pass the ref to the dropdown's root element so that clicks inside
 * the element (including the trigger button) are not treated as outside.
 *
 * Usage:
 *   const containerRef = ref<HTMLElement | null>(null)
 *   const { open, toggle, close } = useDropdown(containerRef)
 */
export function useDropdown(containerRef?: Ref<HTMLElement | null>) {
  const open = ref(false)

  function toggle() {
    open.value = !open.value
  }

  function close() {
    open.value = false
  }

  if (containerRef) {
    useClickOutside(containerRef, close)
  }

  return { open, toggle, close }
}
