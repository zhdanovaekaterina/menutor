<script setup lang="ts">
defineProps<{
  name: string
  detail: string
  variant: 'recipe' | 'product'
}>()

const emit = defineEmits<{ remove: []; click: [] }>()
</script>

<template>
  <div
    :class="variant === 'recipe'
      ? 'bg-blue-50 border-l-2 border-blue-400'
      : 'bg-orange-50 border-l-2 border-orange-400'"
    class="flex items-center gap-1 px-2 py-1 rounded text-xs group cursor-pointer"
    draggable="true"
    @click="emit('click')"
  >
    <span class="truncate flex-1">{{ name }}</span>
    <span class="text-gray-500 whitespace-nowrap">{{ detail }}</span>
    <button
      class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 ml-1 shrink-0"
      title="Удалить"
      @click.stop="emit('remove')"
    >
      &times;
    </button>
  </div>
</template>
