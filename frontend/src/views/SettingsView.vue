<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'

const links = [
  { to: '/settings/family', label: 'Члены семьи' },
  { to: '/settings/product-categories', label: 'Категории продуктов' },
  { to: '/settings/recipe-categories', label: 'Категории рецептов' },
  { to: '/settings/about', label: 'О программе' },
]
</script>

<template>
  <div class="h-full flex flex-col p-4 gap-4">
    <h1 class="text-xl font-bold">Настройки</h1>

    <div class="flex-1 flex gap-4 min-h-0">
      <!-- Nav -->
      <nav class="w-48 shrink-0 flex flex-col border-r pr-4">
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

      <!-- Content -->
      <div class="flex-1 min-w-0 overflow-y-auto">
        <RouterView />
      </div>
    </div>
  </div>
</template>
