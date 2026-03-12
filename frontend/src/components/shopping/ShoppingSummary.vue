<script setup lang="ts">
import type { Money } from '@/api/types'

defineProps<{
  totalCost: Money
  itemCount: number
  purchasedCount: number
  progressPercent: number
}>()

const emit = defineEmits<{ remove: []; exportText: []; exportCsv: [] }>()
</script>

<template>
  <div class="flex flex-col gap-4">
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
          <div
            class="bg-green-500 h-2 rounded-full transition-all"
            :style="{ width: progressPercent + '%' }"
          />
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-2">
      <button
        class="w-full px-4 py-2 rounded-lg border border-red-300 text-red-600 text-sm hover:bg-red-50"
        @click="emit('remove')"
      >
        Удалить из списка
      </button>
      <button
        class="w-full px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
        @click="emit('exportText')"
      >
        Экспорт (текст)
      </button>
      <button
        class="w-full px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
        @click="emit('exportCsv')"
      >
        Экспорт (CSV)
      </button>
    </div>
  </div>
</template>
