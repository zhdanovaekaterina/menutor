<script setup lang="ts">
const model = defineModel<string>({ default: '' })
</script>

<template>
  <div class="relative">
    <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">&#x1F50D;</span>
    <input
      v-model="model"
      type="text"
      placeholder="Поиск..."
      class="w-full border border-gray-300 rounded-lg pl-9 pr-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
    />
  </div>
</template>
