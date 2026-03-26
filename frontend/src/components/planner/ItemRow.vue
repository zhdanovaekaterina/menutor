<script setup lang="ts">
import { computed } from 'vue'
import { hexToRgba } from '@/utils/color'
import { FALLBACK_RECIPE_COLOR, FALLBACK_PRODUCT_COLOR } from '@/constants/colors'

const props = defineProps<{
  name: string
  detail: string
  piecesDetail?: { portions: string; pieces: number } | null
  variant: 'recipe' | 'product'
  categoryColor?: string | null
}>()

const emit = defineEmits<{ remove: []; click: [] }>()

const effectiveColor = computed(() =>
  props.categoryColor ?? (props.variant === 'recipe' ? FALLBACK_RECIPE_COLOR : FALLBACK_PRODUCT_COLOR)
)

const bgTint = computed(() => hexToRgba(effectiveColor.value, 0.08))
</script>

<template>
  <div
    class="flex items-center gap-1 px-2 py-2 lg:py-1 rounded text-sm lg:text-xs group cursor-pointer border-l-[3px]"
    :style="{ borderLeftColor: effectiveColor, backgroundColor: bgTint }"
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
