<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="h-full flex flex-col p-4 gap-4">
    <h1 class="text-xl font-bold">Настройки</h1>

    <div class="flex-1 flex gap-4 min-h-0">
      <!-- Nav -->
      <div class="w-48 shrink-0 border-r pr-4">
        <nav class="flex flex-col py-2">
          <RouterLink to="/settings/family" class="flex items-center gap-2 px-3 py-2.5 text-sm rounded-lg hover:bg-gray-100 transition-colors" active-class="!bg-blue-50 !text-blue-700 font-medium">
            <svg class="w-4 h-4 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
            </svg>
            <span>Члены семьи</span>
          </RouterLink>
          <RouterLink to="/settings/product-categories" class="flex items-center gap-2 px-3 py-2.5 text-sm rounded-lg hover:bg-gray-100 transition-colors" active-class="!bg-blue-50 !text-blue-700 font-medium">
            <svg class="w-4 h-4 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 0 0 3 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 0 0 5.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 0 0 9.568 3Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6Z" />
            </svg>
            <span>Категории продуктов</span>
          </RouterLink>
          <RouterLink to="/settings/recipe-categories" class="flex items-center gap-2 px-3 py-2.5 text-sm rounded-lg hover:bg-gray-100 transition-colors" active-class="!bg-blue-50 !text-blue-700 font-medium">
            <svg class="w-4 h-4 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 0 0 3 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 0 0 5.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 0 0 9.568 3Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6Z" />
            </svg>
            <span>Категории рецептов</span>
          </RouterLink>
          <RouterLink to="/settings/password" class="flex items-center gap-2 px-3 py-2.5 text-sm rounded-lg hover:bg-gray-100 transition-colors" active-class="!bg-blue-50 !text-blue-700 font-medium">
            <svg class="w-4 h-4 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 0 1 21.75 8.25Z" />
            </svg>
            <span>Настройки аккаунта</span>
          </RouterLink>
          <RouterLink to="/settings/about" class="flex items-center gap-2 px-3 py-2.5 text-sm rounded-lg hover:bg-gray-100 transition-colors" active-class="!bg-blue-50 !text-blue-700 font-medium">
            <svg class="w-4 h-4 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
            </svg>
            <span>О программе</span>
          </RouterLink>
        </nav>
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0 overflow-y-auto">
        <RouterView />
      </div>
    </div>
  </div>
</template>
