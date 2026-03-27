<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  title?: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
}>()

const emit = defineEmits<{ confirm: []; cancel: [] }>()

const confirmBtn = ref<HTMLButtonElement | null>(null)

watch(
  () => props.open,
  async (v) => {
    if (v) {
      await nextTick()
      confirmBtn.value?.focus()
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  },
)
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50" @keydown.escape="emit('cancel')" @mousedown.self="emit('cancel')" @touchstart.self.passive="emit('cancel')">
      <div class="bg-white rounded-t-2xl sm:rounded-xl shadow-xl max-w-md w-full sm:mx-4 p-6 pb-8 sm:pb-6">
        <h3 class="text-lg font-semibold mb-2">{{ title ?? 'Подтверждение' }}</h3>
        <p class="text-sm text-gray-600 mb-2">{{ message }}</p>
        <slot />
        <div class="mt-4 flex flex-col-reverse sm:flex-row justify-end gap-2">
          <button
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
            @click="emit('cancel')"
          >
            {{ cancelLabel ?? 'Отмена' }}
          </button>
          <button
            ref="confirmBtn"
            :class="
              danger
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-blue-600 hover:bg-blue-700'
            "
            class="px-4 py-2 rounded-lg text-white text-sm transition-colors"
            @click="emit('confirm')"
          >
            {{ confirmLabel ?? 'Да' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
