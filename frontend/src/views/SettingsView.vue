<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const links = [
  { to: '/settings/family', label: 'Члены семьи', mobileLabel: 'Семья' },
  { to: '/settings/preferences', label: 'Предпочтения', mobileLabel: 'Предпочтения' },
  { to: '/settings/product-categories', label: 'Категории продуктов', mobileLabel: 'Кат. продуктов' },
  { to: '/settings/recipe-categories', label: 'Категории рецептов', mobileLabel: 'Кат. рецептов' },
  { to: '/settings/meal-types', label: 'Приемы пищи', mobileLabel: 'Приемы пищи' },
  { to: '/settings/password', label: 'Настройки аккаунта', mobileLabel: 'Аккаунт' },
  { to: '/settings/recipes', label: 'Рецепты', mobileLabel: 'Рецепты' },
  { to: '/settings/shopping-list', label: 'Список покупок', mobileLabel: 'Список покупок' },
  { to: '/settings/about', label: 'О программе', mobileLabel: 'О прогр.' },
]

const route = useRoute()
const mobileNavOpen = ref(false)

const currentLink = computed(() => links.find((l) => route.path.startsWith(l.to)))
</script>

<template>
  <div class="h-full flex flex-col p-3 sm:p-4 lg:p-6 gap-3 sm:gap-4">
    <h1 class="text-lg sm:text-xl font-bold">Настройки</h1>

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

      <!-- Mobile: burger dropdown -->
      <div class="lg:hidden shrink-0 relative">
        <button
          class="flex items-center gap-2 w-full px-4 py-2.5 border rounded-lg bg-white text-sm font-medium hover:bg-gray-50 transition-colors"
          @click="mobileNavOpen = !mobileNavOpen"
        >
          <svg class="w-5 h-5 text-gray-500 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
          </svg>
          <span class="flex-1 text-left">{{ currentLink?.label ?? 'Раздел' }}</span>
          <svg
            class="w-4 h-4 text-gray-400 transition-transform"
            :class="mobileNavOpen ? 'rotate-180' : ''"
            xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
          </svg>
        </button>

        <div
          v-if="mobileNavOpen"
          class="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-20 overflow-hidden"
        >
          <RouterLink
            v-for="link in links"
            :key="link.to"
            :to="link.to"
            class="block px-4 py-3 text-sm hover:bg-gray-50 transition-colors"
            active-class="!bg-blue-50 !text-blue-700 font-medium"
            @click="mobileNavOpen = false"
          >
            {{ link.label }}
          </RouterLink>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0 overflow-y-auto">
        <RouterView />
      </div>
    </div>
  </div>
</template>
