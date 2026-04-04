<script setup lang="ts">
defineProps<{
  costPerPortion: number | null
  costIsPartial: boolean
  /** Show as inline badge (mobile) or plain text (desktop table cell) */
  badge?: boolean
}>()
</script>

<template>
  <!-- No cost: dash -->
  <span v-if="costPerPortion === null" class="text-gray-400">--</span>

  <!-- Badge mode (mobile) -->
  <span
    v-else-if="badge"
    class="inline-flex items-center text-xs px-1.5 py-0.5 rounded-full border"
    :class="costIsPartial
      ? 'bg-amber-50 text-amber-700 border-amber-200'
      : 'bg-emerald-50 text-emerald-700 border-emerald-200'"
  >
    ~{{ costPerPortion.toFixed(2) }} руб.
    <!-- Warning icon for partial -->
    <svg
      v-if="costIsPartial"
      class="w-3 h-3 ml-0.5 text-amber-500"
      xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
      stroke-width="2" stroke="currentColor"
    >
      <path stroke-linecap="round" stroke-linejoin="round"
        d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
    </svg>
  </span>

  <!-- Table cell mode (desktop) -->
  <template v-else>
    <span :class="costIsPartial ? 'text-amber-700' : 'text-emerald-700'" class="tabular-nums">
      ~{{ costPerPortion.toFixed(2) }}
    </span>
    <svg
      v-if="costIsPartial"
      class="inline-block w-3.5 h-3.5 text-amber-500 ml-1 align-text-bottom"
      title="Стоимость рассчитана не полностью: не у всех ингредиентов указана цена"
      xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
      stroke-width="2" stroke="currentColor"
    >
      <path stroke-linecap="round" stroke-linejoin="round"
        d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
    </svg>
  </template>
</template>
