<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'

const links = [
  { to: '/settings/family', label: 'Члены семьи', mobileLabel: 'Семья' },
  { to: '/settings/product-categories', label: 'Категории продуктов', mobileLabel: 'Кат. продуктов' },
  { to: '/settings/recipe-categories', label: 'Категории рецептов', mobileLabel: 'Кат. рецептов' },
  { to: '/settings/password', label: 'Настройки аккаунта', mobileLabel: 'Аккаунт' },
  { to: '/settings/about', label: 'О программе', mobileLabel: 'О прогр.' },
]
</script>

<template>
  <div class="h-full flex flex-col p-4 lg:p-6 gap-4">
    <h1 class="text-xl font-bold">Настройки</h1>

    <div class="flex-1 flex flex-col lg:flex-row gap-4 min-h-0">
      <!-- Desktop: vertical nav -->
      <nav class="hidden lg:flex w-48 shrink-0 flex-col border-r pr-4">
        <RouterLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="px-4 py-2.5 text-sm rounded-lg hover:bg-gray-100 transition-colors"
          active-class="!bg-blue-50 !text-blue-700 font-medium"
        >
          {{ link.label }}
        </RouterLink>
      </nav>

      <!-- Mobile: horizontal scrollable tabs -->
      <nav class="lg:hidden flex gap-1 overflow-x-auto -mx-4 px-4 pb-2 border-b shrink-0 scrollbar-none">
        <RouterLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="px-3 py-2 text-sm rounded-full whitespace-nowrap border border-transparent hover:bg-gray-100 transition-colors shrink-0"
          active-class="!bg-blue-50 !text-blue-700 !border-blue-200 font-medium"
        >
          {{ link.mobileLabel ?? link.label }}
        </RouterLink>
      </nav>

      <!-- Content -->
      <div class="flex-1 min-w-0 overflow-y-auto">
        <RouterView />
      </div>
    </div>
  </div>
</template>
