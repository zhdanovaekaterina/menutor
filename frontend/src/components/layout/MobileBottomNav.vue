<script setup lang="ts">
import { RouterLink } from 'vue-router'

const links = [
  { to: '/planner', icon: '\uD83D\uDCC5', label: '\u041C\u0435\u043D\u044E' },
  { to: '/shopping-list', icon: '\uD83D\uDED2', label: '\u041F\u043E\u043A\u0443\u043F\u043A\u0438' },
  { to: '/recipes', icon: '\uD83C\uDF73', label: '\u0420\u0435\u0446\u0435\u043F\u0442\u044B' },
  { to: '/products', icon: '\uD83D\uDCE6', label: '\u041F\u0440\u043E\u0434\u0443\u043A\u0442\u044B' },
  { to: '/settings', icon: '\u2699\uFE0F', label: '\u041D\u0430\u0441\u0442\u0440.' },
]
</script>

<template>
  <nav class="lg:hidden fixed bottom-0 inset-x-0 bg-white border-t flex z-40">
    <RouterLink
      v-for="link in links"
      :key="link.to"
      :to="link.to"
      class="flex-1 flex flex-col items-center gap-0.5 py-2 text-gray-500"
      active-class="!text-blue-600"
    >
      <span class="text-lg">{{ link.icon }}</span>
      <span class="text-[10px]">{{ link.label }}</span>
    </RouterLink>
  </nav>
</template>
