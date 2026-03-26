<script setup lang="ts">
import { ref, computed } from 'vue'
import { PRESET_COLORS } from '@/constants/colors'
import { contrastRatio } from '@/utils/color'
import ColorPickerSwatch from './ColorPickerSwatch.vue'
import ColorPickerAdvanced from './ColorPickerAdvanced.vue'

const props = withDefaults(defineProps<{
  modelValue: string | null
  recentColors?: readonly string[]
  showClearButton?: boolean
}>(), {
  recentColors: () => [],
  showClearButton: true,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
  'use-color': [color: string]
}>()

const advancedOpen = ref(false)

function selectColor(hex: string) {
  emit('update:modelValue', hex)
  emit('use-color', hex)
}

const lowContrast = computed(() =>
  props.modelValue != null && contrastRatio(props.modelValue, '#FFFFFF') < 3
)
</script>

<template>
  <fieldset class="space-y-3">
    <legend class="text-sm font-medium text-gray-700">Цвет</legend>

    <!-- Preview -->
    <div class="flex items-center gap-3">
      <div
        class="w-10 h-10 rounded-lg border border-gray-200 shrink-0 flex items-center justify-center"
        :style="{ backgroundColor: modelValue ?? '#FFFFFF' }"
      >
        <svg v-if="!modelValue" class="w-5 h-5 text-gray-300" fill="none" viewBox="0 0 24 24"
             stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" d="M5 19L19 5" />
        </svg>
      </div>
      <span class="text-sm text-gray-600 font-mono">{{ modelValue ?? 'Не выбран' }}</span>
      <div class="flex-1" />
      <button
        v-if="modelValue && showClearButton"
        class="text-xs text-gray-400 hover:text-red-500 transition-colors"
        @click="emit('update:modelValue', null)"
      >
        Сбросить
      </button>
    </div>

    <!-- Low contrast warning -->
    <div
      v-if="lowContrast"
      class="flex items-center gap-1.5 text-xs text-amber-600 bg-amber-50
             border border-amber-200 rounded-lg px-2.5 py-1.5"
    >
      <svg class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24"
           stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round"
              d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      Этот цвет может быть плохо виден на белом фоне
    </div>

    <!-- Preset palette -->
    <div>
      <p class="text-xs font-medium text-gray-500 mb-1.5">Палитра</p>
      <div class="grid grid-cols-8 gap-2 sm:gap-1.5" role="radiogroup" aria-label="Предустановленные цвета">
        <ColorPickerSwatch
          v-for="color in PRESET_COLORS"
          :key="color.hex"
          :hex="color.hex"
          :selected="modelValue === color.hex"
          :label="color.name"
          @select="selectColor"
        />
      </div>
    </div>

    <!-- Recent colors -->
    <div v-if="recentColors.length > 0">
      <p class="text-xs font-medium text-gray-500 mb-1.5">Недавние</p>
      <div class="flex flex-wrap gap-2 sm:gap-1.5">
        <ColorPickerSwatch
          v-for="hex in recentColors"
          :key="hex"
          :hex="hex"
          :selected="modelValue === hex"
          :label="`Недавний цвет ${hex}`"
          @select="selectColor"
        />
      </div>
    </div>

    <!-- Toggle advanced -->
    <button
      class="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700
             transition-colors mt-2 py-1"
      @click="advancedOpen = !advancedOpen"
    >
      <svg
        class="w-3.5 h-3.5 transition-transform duration-200"
        :class="advancedOpen ? 'rotate-90' : ''"
        fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
      {{ advancedOpen ? 'Скрыть расширенный выбор' : 'Расширенный выбор' }}
    </button>

    <!-- Advanced color picker (collapsible) -->
    <div
      class="overflow-hidden transition-all duration-200 ease-out"
      :style="{ maxHeight: advancedOpen ? '400px' : '0', opacity: advancedOpen ? 1 : 0 }"
    >
      <ColorPickerAdvanced
        :model-value="modelValue"
        @update:model-value="(v) => { emit('update:modelValue', v); if (v) emit('use-color', v) }"
      />
    </div>
  </fieldset>
</template>
