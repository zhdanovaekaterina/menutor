<script setup lang="ts">
import { useShoppingListSettingsStore } from '@/stores/shoppingListSettings'

const settings = useShoppingListSettingsStore()
</script>

<template>
  <div class="max-w-md">
    <h2 class="text-lg font-semibold mb-4">Настройки списка покупок</h2>

    <div class="flex items-center justify-between py-3 border-b">
      <div>
        <p class="text-sm font-medium">Скрывать купленные товары</p>
        <p class="text-xs text-gray-500 mt-0.5">Отмеченные товары не будут отображаться в списке</p>
      </div>
      <button
        :class="settings.hidePurchased ? 'bg-blue-600' : 'bg-gray-200'"
        class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors duration-200"
        role="switch"
        :aria-checked="settings.hidePurchased"
        @click="settings.toggleHidePurchased()"
      >
        <span
          :class="settings.hidePurchased ? 'translate-x-5' : 'translate-x-0.5'"
          class="inline-block h-5 w-5 mt-0.5 rounded-full bg-white shadow transition-transform duration-200"
        />
      </button>
    </div>
  </div>
</template>
