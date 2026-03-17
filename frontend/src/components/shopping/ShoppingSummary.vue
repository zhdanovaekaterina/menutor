<script setup lang="ts">
import type { Money } from '@/api/types'

defineProps<{
  totalCost: Money
  itemCount: number
  purchasedCount: number
  progressPercent: number
}>()

const emit = defineEmits<{ exportText: []; exportCsv: [] }>()
</script>

<template>
  <div class="flex flex-col gap-3">
    <!-- Summary card -->
    <div class="bg-gray-50 rounded-lg p-4">
      <p class="text-sm text-gray-500">Сумма корзины</p>
      <p class="text-2xl font-bold">{{ Number(totalCost.amount).toFixed(2) }} руб.</p>
      <p class="text-sm text-gray-500 mt-1">Позиций: {{ itemCount }}</p>
      <div class="mt-3">
        <div class="flex justify-between text-xs text-gray-500 mb-1">
          <span>Прогресс покупок</span>
          <span>{{ purchasedCount }} из {{ itemCount }}</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div class="bg-green-500 h-2 rounded-full transition-all" :style="{ width: progressPercent + '%' }" />
        </div>
      </div>
    </div>

    <!-- Export section -->
    <div class="border rounded-lg p-3">
      <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Экспорт</h4>
      <div class="flex gap-2">
        <button
          class="flex-1 px-3 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
          @click="emit('exportText')"
        >
          Текст
        </button>
        <button
          class="flex-1 px-3 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
          @click="emit('exportCsv')"
        >
          CSV
        </button>
      </div>
    </div>
  </div>
</template>
