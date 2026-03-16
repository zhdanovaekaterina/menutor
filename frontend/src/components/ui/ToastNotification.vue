<script setup lang="ts">
import { useToastStore } from '@/stores/toast'

const store = useToastStore()
const icons: Record<string, string> = { success: '\u2713', error: '\u26A0', info: '\u2139' }
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[9999] flex flex-col gap-2">
      <TransitionGroup name="toast">
        <div
          v-for="t in store.toasts"
          :key="t.id"
          :class="{
            'bg-green-50 border-green-200 text-green-700': t.type === 'success',
            'bg-red-50 border-red-200 text-red-700': t.type === 'error',
            'bg-blue-50 border-blue-200 text-blue-700': t.type === 'info',
          }"
          class="border px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 text-sm min-w-64"
        >
          <span>{{ icons[t.type] }}</span>
          <span class="flex-1">{{ t.message }}</span>
          <button class="opacity-60 hover:opacity-100" @click="store.remove(t.id)">&times;</button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(40px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
</style>
