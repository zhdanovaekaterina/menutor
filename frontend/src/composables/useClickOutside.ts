import { onUnmounted, watch } from 'vue'
import type { Ref } from 'vue'

/**
 * Calls `callback` when a mousedown or touchstart event occurs outside `el`.
 * Uses `el.contains(event.target)` so clicks inside child components are
 * correctly treated as "inside" and do not trigger the callback.
 *
 * The listener is attached when `el` has a value and removed on unmount (or
 * when `el` becomes null again).
 */
export function useClickOutside(
  el: Ref<HTMLElement | null>,
  callback: () => void,
): void {
  let cleanup: (() => void) | null = null

  function onPointerDown(event: MouseEvent | TouchEvent): void {
    const target = event.target as Node | null
    if (!target || !el.value) return
    if (!el.value.contains(target)) {
      callback()
    }
  }

  function attach(): void {
    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('touchstart', onPointerDown, { passive: true })
    cleanup = () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('touchstart', onPointerDown)
    }
  }

  function detach(): void {
    if (cleanup) {
      cleanup()
      cleanup = null
    }
  }

  watch(
    el,
    (newEl) => {
      detach()
      if (newEl) attach()
    },
    { immediate: true },
  )

  onUnmounted(detach)
}
