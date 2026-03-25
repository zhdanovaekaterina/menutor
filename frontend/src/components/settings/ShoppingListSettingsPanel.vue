<script setup lang="ts">
import { useShoppingListSettingsStore } from '@/stores/shoppingListSettings'

const settings = useShoppingListSettingsStore()
</script>

<template>
  <div class="max-w-md">
    <h2 class="text-lg font-semibold mb-4">Настройки списка покупок</h2>

    <!-- Hide purchased toggle -->
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

    <!-- Grouping option -->
    <div class="py-3">
      <p class="text-sm font-medium mb-2">Группировка товаров</p>
      <div class="flex flex-col gap-2">
        <label class="flex items-center gap-3 cursor-pointer">
          <input
            type="radio"
            name="groupBy"
            value="category"
            :checked="settings.groupBy === 'category'"
            class="w-4 h-4 text-blue-600"
            @change="settings.setGroupBy('category')"
          />
          <div>
            <span class="text-sm">По категории</span>
            <p class="text-xs text-gray-500">Товары сгруппированы по категории продукта</p>
          </div>
        </label>
        <label class="flex items-center gap-3 cursor-pointer">
          <input
            type="radio"
            name="groupBy"
            value="supplier"
            :checked="settings.groupBy === 'supplier'"
            class="w-4 h-4 text-blue-600"
            @change="settings.setGroupBy('supplier')"
          />
          <div>
            <span class="text-sm">По поставщику</span>
            <p class="text-xs text-gray-500">Товары сгруппированы по поставщику продукта</p>
          </div>
        </label>
      </div>
    </div>
  </div>
</template>
