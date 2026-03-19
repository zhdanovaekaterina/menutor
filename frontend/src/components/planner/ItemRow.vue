<script setup lang="ts">
defineProps<{
  name: string
  detail: string
  piecesDetail?: { portions: string; pieces: number } | null
  variant: 'recipe' | 'product'
}>()

const emit = defineEmits<{ remove: []; click: [] }>()
</script>

<template>
  <div
    :class="variant === 'recipe'
      ? 'bg-blue-50 border-l-2 border-blue-400'
      : 'bg-orange-50 border-l-2 border-orange-400'"
    class="flex items-center gap-1 px-2 py-2 lg:py-1 rounded text-sm lg:text-xs group cursor-pointer"
    @click="emit('click')"
  >
    <span class="truncate flex-1">{{ name }}</span>
    <!-- Standard detail (non-pieces recipes and products) -->
    <span v-if="!piecesDetail" class="text-gray-500 whitespace-nowrap">{{ detail }}</span>
    <!-- Pieces-mode detail -->
    <span v-else class="whitespace-nowrap flex items-center gap-0.5">
      <span class="text-gray-400 text-[10px] hidden lg:inline">{{ piecesDetail.portions }} п. &middot;</span>
      <span class="text-blue-600 font-semibold">{{ piecesDetail.pieces }} шт</span>
    </span>
    <button
      class="hidden lg:inline opacity-40 hover:opacity-100 transition-opacity text-gray-400 hover:text-red-500 ml-1 shrink-0"
      title="Удалить"
      @click.stop="emit('remove')"
    >
      &times;
    </button>
  </div>
</template>
