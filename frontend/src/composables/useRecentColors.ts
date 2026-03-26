import { ref, watch, readonly, type Ref } from 'vue'

const KEY_PREFIX = 'menutor_recent_colors_'
const MAX_RECENT = 10

export function useRecentColors(userId: Ref<number | null>) {
  const colors = ref<string[]>([])

  function load() {
    if (!userId.value) {
      colors.value = []
      return
    }
    try {
      const raw = localStorage.getItem(`${KEY_PREFIX}${userId.value}`)
      colors.value = raw ? JSON.parse(raw) : []
    } catch {
      colors.value = []
    }
  }

  function addColor(hex: string) {
    if (!userId.value) return
    const normalized = hex.toUpperCase()
    colors.value = [normalized, ...colors.value.filter((c) => c !== normalized)].slice(0, MAX_RECENT)
    localStorage.setItem(`${KEY_PREFIX}${userId.value}`, JSON.stringify(colors.value))
  }

  watch(userId, load, { immediate: true })

  return { recentColors: readonly(colors), addColor }
}
