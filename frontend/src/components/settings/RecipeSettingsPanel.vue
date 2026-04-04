<script setup lang="ts">
import { useRecipeSettingsStore } from '@/stores/recipeSettings'

const settings = useRecipeSettingsStore()
</script>

<template>
  <div class="max-w-md">
    <h2 class="text-lg font-semibold mb-4">Настройки рецептов</h2>

    <!-- Show cost column toggle -->
    <div class="flex items-center justify-between py-3 border-b">
      <div>
        <p class="text-sm font-medium">Показывать стоимость порции</p>
        <p class="text-xs text-gray-500 mt-0.5">Отображать колонку «Стоимость» в списке рецептов</p>
      </div>
      <button
        :class="settings.showCostColumn ? 'bg-blue-600' : 'bg-gray-200'"
        class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors duration-200"
        role="switch"
        :aria-checked="settings.showCostColumn"
        @click="settings.toggleShowCostColumn()"
      >
        <span
          :class="settings.showCostColumn ? 'translate-x-5' : 'translate-x-0.5'"
          class="inline-block h-5 w-5 mt-0.5 rounded-full bg-white shadow transition-transform duration-200"
        />
      </button>
    </div>
  </div>
</template>
