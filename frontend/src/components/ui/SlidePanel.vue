<script setup lang="ts">
import IconBackArrow from '@/components/ui/icons/IconBackArrow.vue'

defineProps<{
  open: boolean
  title?: string
  width?: string
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <Transition name="fade">
      <div
        v-if="open"
        class="fixed inset-0 bg-black/30 z-40"
        @click="emit('close')"
      />
    </Transition>

    <!-- Panel -->
    <Transition name="slide">
      <div
        v-if="open"
        :class="width ?? 'w-full sm:w-96'"
        class="fixed top-0 right-0 h-full bg-white shadow-xl z-50 flex flex-col"
      >
        <div class="flex items-center justify-between px-4 py-3 border-b shrink-0">
          <div class="flex items-center gap-2">
            <!-- Mobile: back arrow (instead of X) -->
            <button
              class="sm:hidden p-1 rounded hover:bg-gray-100 text-gray-500 -ml-1"
              @click="emit('close')"
            >
              <IconBackArrow class="w-5 h-5" />
            </button>
            <h2 class="text-lg font-semibold">{{ title }}</h2>
          </div>
          <!-- Desktop: X button -->
          <button
            class="hidden sm:block p-1 rounded hover:bg-gray-100 text-gray-500 transition-colors"
            @click="emit('close')"
          >
            <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4">
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
