<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { Preference } from '@/api/types'
import { fetchRecipeMatchingPreferences } from '@/api/client'

const props = defineProps<{
  recipeId: number
}>()

const preferences = ref<Preference[]>([])

onMounted(async () => {
  try {
    const result = await fetchRecipeMatchingPreferences(props.recipeId)
    preferences.value = result.preferences
  } catch {
    // silently ignore errors — badges are non-critical UI
  }
})

function badgeClass(p: Preference): string {
  if (p.type === 'ALLERGY' || p.mode === 'BLOCKED') {
    return 'bg-red-100 text-red-700 border-red-200'
  }
  return 'bg-green-100 text-green-700 border-green-200'
}

function badgeLabel(p: Preference): string {
  return p.name
}
</script>

<template>
  <div v-if="preferences.length" class="flex flex-wrap gap-1">
    <span
      v-for="p in preferences"
      :key="p.id"
      class="inline-flex items-center text-xs px-2 py-0.5 rounded-full border"
      :class="badgeClass(p)"
      :title="p.type === 'ALLERGY' ? 'Аллергия' : p.mode === 'BLOCKED' ? 'Блокировать' : 'Разрешать'"
    >
      {{ badgeLabel(p) }}
    </span>
  </div>
</template>
