<script setup lang="ts">
defineProps<{
  open: boolean
  title?: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
}>()

const emit = defineEmits<{ confirm: []; cancel: [] }>()
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        <h3 class="text-lg font-semibold mb-2">{{ title ?? 'Подтверждение' }}</h3>
        <p class="text-sm text-gray-600 mb-6">{{ message }}</p>
        <div class="flex justify-end gap-2">
          <button
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
            @click="emit('cancel')"
          >
            {{ cancelLabel ?? 'Отмена' }}
          </button>
          <button
            :class="
              danger
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-blue-600 hover:bg-blue-700'
            "
            class="px-4 py-2 rounded-lg text-white text-sm"
            @click="emit('confirm')"
          >
            {{ confirmLabel ?? 'Да' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
