<script setup lang="ts">
import { computed, ref } from 'vue'

export interface FormatOption {
  label: string
  value: string
}

const props = defineProps<{
  formats: FormatOption[]
  modelValue: string
  loading?: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  export: []
}>()

const open = ref(false)

const currentLabel = computed(() => {
  return props.formats.find((f) => f.value === props.modelValue)?.label ?? props.modelValue
})

function toggleOpen() {
  open.value = !open.value
}

function close() {
  open.value = false
}

function selectFormat(value: string) {
  emit('update:modelValue', value)
  close()
}
</script>

<template>
  <div class="relative inline-flex w-full">
    <!-- Left: trigger export with current format -->
    <button
      type="button"
      :disabled="loading || disabled"
      class="flex-1 flex items-center justify-center gap-1.5 rounded-l-lg border border-r-0 border-gray-300 px-3 py-2 text-sm hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      @click="emit('export')"
    >
      <svg
        v-if="loading && !disabled"
        class="w-3.5 h-3.5 animate-spin text-gray-400 shrink-0"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      <span>Скачать {{ currentLabel }}</span>
    </button>

    <!-- Divider is the border-r-0 / border-l-0 gap between buttons -->

    <!-- Right: open format picker -->
    <button
      type="button"
      :disabled="loading || disabled"
      class="shrink-0 rounded-r-lg border border-gray-300 px-2 py-2 text-sm hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      aria-label="Выбрать формат"
      @click="toggleOpen"
      @keydown.escape="close"
    >
      <svg
        class="w-4 h-4 text-gray-500 transition-transform"
        :class="{ 'rotate-180': !open }"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="2"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
      </svg>
    </button>

    <!-- Dropdown menu -->
    <div
      v-if="open"
      class="absolute left-0 bottom-full z-50 mb-1 w-full min-w-[8rem] rounded-lg border border-gray-200 bg-white shadow-lg"
      role="menu"
    >
      <button
        v-for="fmt in formats"
        :key="fmt.value"
        type="button"
        class="flex w-full items-center justify-between px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg"
        :class="{ 'font-medium text-blue-600': fmt.value === modelValue }"
        role="menuitem"
        @click="selectFormat(fmt.value)"
      >
        <span>{{ fmt.label }}</span>
        <svg
          v-if="fmt.value === modelValue"
          class="w-4 h-4 text-blue-600 shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2.5"
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
        </svg>
      </button>
    </div>

    <!-- Backdrop to close on outside click -->
    <div v-if="open" class="fixed inset-0 z-40" @click="close" />
  </div>
</template>
