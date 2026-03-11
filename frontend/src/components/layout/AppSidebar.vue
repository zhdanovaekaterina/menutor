<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'

const collapsed = ref(false)

const links = [
  { to: '/planner', icon: '\uD83D\uDCC5', label: '\u041F\u043B\u0430\u043D\u0438\u0440\u043E\u0432\u0449\u0438\u043A' },
  { to: '/shopping-list', icon: '\uD83D\uDED2', label: '\u0421\u043F\u0438\u0441\u043E\u043A \u043F\u043E\u043A\u0443\u043F\u043E\u043A' },
  { to: '/recipes', icon: '\uD83C\uDF73', label: '\u0420\u0435\u0446\u0435\u043F\u0442\u044B' },
  { to: '/products', icon: '\uD83D\uDCE6', label: '\u041F\u0440\u043E\u0434\u0443\u043A\u0442\u044B' },
  { to: '/settings', icon: '\u2699\uFE0F', label: '\u041D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438' },
]
</script>

<template>
  <aside
    :class="collapsed ? 'w-16' : 'w-52'"
    class="bg-slate-800 text-white flex flex-col transition-all duration-200 shrink-0 hidden lg:flex"
  >
    <div class="h-14 flex items-center justify-center font-bold text-lg border-b border-slate-700">
      <span v-if="!collapsed">Menutor</span>
      <span v-else>M</span>
    </div>

    <nav class="flex-1 flex flex-col gap-1 py-2 px-2">
      <RouterLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm hover:bg-slate-700 transition-colors"
        active-class="!bg-slate-600"
      >
        <span class="text-lg w-6 text-center shrink-0">{{ link.icon }}</span>
        <span v-if="!collapsed" class="truncate">{{ link.label }}</span>
      </RouterLink>
    </nav>

    <button
      class="p-3 border-t border-slate-700 text-xs text-slate-400 hover:text-white"
      @click="collapsed = !collapsed"
    >
      {{ collapsed ? '\u276F' : '\u276E Свернуть' }}
    </button>
  </aside>
</template>
