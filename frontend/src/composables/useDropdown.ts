import { onMounted, onUnmounted, ref } from 'vue'

export function useDropdown() {
  const open = ref(false)

  function toggle() {
    open.value = !open.value
  }

  function close() {
    open.value = false
  }

  onMounted(() => document.addEventListener('click', close))
  onUnmounted(() => document.removeEventListener('click', close))

  return { open, toggle, close }
}
