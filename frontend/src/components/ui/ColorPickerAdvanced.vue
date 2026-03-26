<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { hexToRgb, rgbToHex, rgbToHsv, hsvToRgb } from '@/utils/color'

const props = defineProps<{ modelValue: string | null }>()
const emit = defineEmits<{ 'update:modelValue': [value: string | null] }>()

const hue = ref(210)
const saturation = ref(100)
const value = ref(100)

const hexInput = ref('')
const hexError = ref('')

const gradientRef = ref<HTMLElement>()
const hueRef = ref<HTMLElement>()

const currentRgb = computed(() => hsvToRgb(hue.value, saturation.value, value.value))
const red = computed(() => currentRgb.value[0])
const green = computed(() => currentRgb.value[1])
const blue = computed(() => currentRgb.value[2])

const currentHexFromHSV = computed(() => rgbToHex(red.value, green.value, blue.value))

// Sync external modelValue -> internal HSV
watch(() => props.modelValue, (val) => {
  if (!val) return
  const [r, g, b] = hexToRgb(val)
  const [h, s, v] = rgbToHsv(r, g, b)
  hue.value = h
  saturation.value = s
  value.value = v
  hexInput.value = val.toUpperCase()
}, { immediate: true })

function emitColor() {
  const hex = currentHexFromHSV.value
  hexInput.value = hex
  hexError.value = ''
  emit('update:modelValue', hex)
}

function onGradientPointerDown(e: PointerEvent) {
  const el = e.currentTarget as HTMLElement
  el.setPointerCapture(e.pointerId)
  updateGradient(e)
  const onMove = (ev: PointerEvent) => updateGradient(ev)
  const onUp = () => {
    el.removeEventListener('pointermove', onMove)
    el.removeEventListener('pointerup', onUp)
  }
  el.addEventListener('pointermove', onMove)
  el.addEventListener('pointerup', onUp)
}

function updateGradient(e: PointerEvent) {
  const rect = gradientRef.value!.getBoundingClientRect()
  saturation.value = Math.round(Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100)))
  value.value = Math.round(Math.max(0, Math.min(100, (1 - (e.clientY - rect.top) / rect.height) * 100)))
  emitColor()
}

function onHuePointerDown(e: PointerEvent) {
  const el = e.currentTarget as HTMLElement
  el.setPointerCapture(e.pointerId)
  updateHue(e)
  const onMove = (ev: PointerEvent) => updateHue(ev)
  const onUp = () => {
    el.removeEventListener('pointermove', onMove)
    el.removeEventListener('pointerup', onUp)
  }
  el.addEventListener('pointermove', onMove)
  el.addEventListener('pointerup', onUp)
}

function updateHue(e: PointerEvent) {
  const rect = hueRef.value!.getBoundingClientRect()
  hue.value = Math.round(Math.max(0, Math.min(360, ((e.clientX - rect.left) / rect.width) * 360)))
  emitColor()
}

function onHexInput(e: Event) {
  const val = (e.target as HTMLInputElement).value
  hexInput.value = val
  if (/^#[0-9a-fA-F]{6}$/.test(val)) {
    hexError.value = ''
    const [r, g, b] = hexToRgb(val)
    const [h, s, v] = rgbToHsv(r, g, b)
    hue.value = h
    saturation.value = s
    value.value = v
    emit('update:modelValue', val.toUpperCase())
  } else {
    hexError.value = 'Формат: #RRGGBB'
  }
}

function onRgbInput(channel: 'r' | 'g' | 'b', e: Event) {
  const raw = parseInt((e.target as HTMLInputElement).value, 10)
  const clamped = Math.round(Math.max(0, Math.min(255, isNaN(raw) ? 0 : raw)))
  const r = channel === 'r' ? clamped : red.value
  const g = channel === 'g' ? clamped : green.value
  const b = channel === 'b' ? clamped : blue.value
  const [h, s, v] = rgbToHsv(r, g, b)
  hue.value = h
  saturation.value = s
  value.value = v
  emitColor()
}

const gradientStyle = computed(() => ({
  background: `linear-gradient(to bottom, transparent, #000),
               linear-gradient(to right, #fff, hsl(${hue.value}, 100%, 50%))`,
}))

const cursorLeft = computed(() => `${saturation.value}%`)
const cursorTop = computed(() => `${100 - value.value}%`)
const hueLeft = computed(() => `${(hue.value / 360) * 100}%`)
</script>

<template>
  <div class="space-y-3 pt-2">
    <!-- Gradient area -->
    <div class="relative">
      <div
        ref="gradientRef"
        class="w-full h-28 rounded-lg cursor-crosshair select-none"
        :style="gradientStyle"
        @pointerdown="onGradientPointerDown"
      >
        <div
          class="absolute w-3.5 h-3.5 rounded-full border-2 border-white shadow -translate-x-1/2 -translate-y-1/2 pointer-events-none"
          :style="{ left: cursorLeft, top: cursorTop, backgroundColor: currentHexFromHSV }"
        />
      </div>
    </div>

    <!-- Hue bar -->
    <div class="relative">
      <div
        ref="hueRef"
        class="w-full h-4 rounded-lg cursor-pointer select-none"
        style="background: linear-gradient(to right, #FF0000, #FFFF00, #00FF00, #00FFFF, #0000FF, #FF00FF, #FF0000)"
        @pointerdown="onHuePointerDown"
      >
        <div
          class="absolute w-4 h-4 rounded-full border-2 border-white shadow -translate-x-1/2 -translate-y-0 top-0 pointer-events-none"
          :style="{ left: hueLeft, backgroundColor: `hsl(${hue}, 100%, 50%)` }"
        />
      </div>
    </div>

    <!-- Hex input -->
    <div>
      <label class="text-xs text-gray-500">Hex</label>
      <input
        class="w-full border rounded px-2 py-1 text-sm font-mono mt-0.5"
        :class="hexError ? 'border-red-400' : 'border-gray-300'"
        :value="hexInput"
        maxlength="7"
        @input="onHexInput"
      />
      <p v-if="hexError" class="text-xs text-red-500 mt-0.5">{{ hexError }}</p>
    </div>

    <!-- RGB inputs -->
    <div class="grid grid-cols-3 gap-2">
      <div>
        <label class="text-xs text-gray-500">R</label>
        <input
          type="number" min="0" max="255"
          class="w-full border border-gray-300 rounded px-2 py-1 text-sm mt-0.5"
          :value="red"
          @input="onRgbInput('r', $event)"
        />
      </div>
      <div>
        <label class="text-xs text-gray-500">G</label>
        <input
          type="number" min="0" max="255"
          class="w-full border border-gray-300 rounded px-2 py-1 text-sm mt-0.5"
          :value="green"
          @input="onRgbInput('g', $event)"
        />
      </div>
      <div>
        <label class="text-xs text-gray-500">B</label>
        <input
          type="number" min="0" max="255"
          class="w-full border border-gray-300 rounded px-2 py-1 text-sm mt-0.5"
          :value="blue"
          @input="onRgbInput('b', $event)"
        />
      </div>
    </div>
  </div>
</template>
