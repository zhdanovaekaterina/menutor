<script setup lang="ts">
import { watch, ref, computed } from 'vue'
import type { Category } from '@/api/types'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SlidePanel from '@/components/ui/SlidePanel.vue'
import ColorPicker from '@/components/ui/ColorPicker.vue'
import { useCategoryStore } from '@/stores/categories'
import { useToastStore } from '@/stores/toast'
import { useAuthStore } from '@/stores/auth'
import { useRecentColors } from '@/composables/useRecentColors'

const props = defineProps<{ type: 'product' | 'recipe' }>()

const store = useCategoryStore()
const toast = useToastStore()
const authStore = useAuthStore()

const categories = computed(() => store.list(props.type).value)

const userId = computed(() => authStore.user?.id ?? null)
const { recentColors, addColor: addRecentColor } = useRecentColors(userId)

const selectedId = ref<number | null>(null)
const name = ref('')
const color = ref<string | null>(null)
const confirmOpen = ref(false)
const confirmDeleteOpen = ref(false)
const formOpen = ref(false)

// Two-step "used category" dialog state
type DialogStep = 'options' | 'select-target' | null
const dialogStep = ref<DialogStep>(null)
const targetCategoryId = ref<number | null>(null)
const moveLoading = ref(false)

watch(() => props.type, () => store.load(props.type), { immediate: true })

const selected = computed(() => categories.value.find((c) => c.id === selectedId.value))
const isInactive = computed(() => selected.value?.active === false)

// Active categories of the same type excluding the one being deleted
const moveTargetOptions = computed(() =>
  store.list(props.type).value.filter((c) => c.active && c.id !== selectedId.value),
)
const canMoveAndDelete = computed(() => moveTargetOptions.value.length > 0)

function selectCategory(c: Category) {
  selectedId.value = c.id
  name.value = c.name
  color.value = c.color ?? null
  formOpen.value = true
}

function openNew() {
  clearForm()
  formOpen.value = true
}

function clearForm() {
  selectedId.value = null
  name.value = ''
  color.value = null
  formOpen.value = false
}

function closeUsedDialog() {
  dialogStep.value = null
  targetCategoryId.value = null
  moveLoading.value = false
}

async function onSave() {
  if (!name.value.trim()) { toast.show('Введите название', 'error'); return }
  try {
    if (selectedId.value) await store.edit(props.type, selectedId.value, name.value.trim(), color.value)
    else await store.create(props.type, name.value.trim(), color.value)
    if (color.value) addRecentColor(color.value)
    clearForm()
  } catch { /* handled */ }
}

async function onDelete() {
  if (!selectedId.value) return
  const used = await store.isUsed(props.type, selectedId.value)
  if (used) {
    dialogStep.value = 'options'
    targetCategoryId.value = moveTargetOptions.value[0]?.id ?? null
  } else {
    confirmDeleteOpen.value = true
  }
}

async function onConfirmSoft() {
  confirmOpen.value = false
  if (!selectedId.value) return
  await store.remove(props.type, selectedId.value, false)
  clearForm()
}

async function onConfirmDelete() {
  confirmDeleteOpen.value = false
  if (!selectedId.value) return
  await store.remove(props.type, selectedId.value, true)
  clearForm()
}

async function onConfirmHard() {
  closeUsedDialog()
  if (!selectedId.value) return
  await store.remove(props.type, selectedId.value, true)
  clearForm()
}

async function onHideUsed() {
  closeUsedDialog()
  if (!selectedId.value) return
  await store.remove(props.type, selectedId.value, false)
  clearForm()
}

function onSelectMoveTarget() {
  dialogStep.value = 'select-target'
}

async function onConfirmMoveAndDelete() {
  if (!selectedId.value || !targetCategoryId.value) return
  moveLoading.value = true
  try {
    await store.moveAndDelete(props.type, selectedId.value, targetCategoryId.value)
    toast.show('Категория перемещена и удалена', 'success')
    closeUsedDialog()
    clearForm()
  } catch (err: unknown) {
    const detail =
      (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      ?? 'Ошибка при перемещении категории'
    toast.show(detail, 'error')
    moveLoading.value = false
  }
}

async function onHideActive() {
  if (!selectedId.value) return
  confirmOpen.value = true
}

async function onActivate() {
  if (!selectedId.value) return
  await store.activate(props.type, selectedId.value)
  clearForm()
}

const title = computed(() =>
  props.type === 'product' ? 'Категории продуктов' : 'Категории рецептов',
)
</script>

<template>
  <div class="h-full flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <h3 class="font-semibold text-sm">{{ title }}</h3>
      <button
        class="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700"
        @click="openNew"
      >
        + Добавить
      </button>
    </div>

    <!-- Table -->
    <div class="hidden sm:block flex-1 overflow-y-auto border rounded-lg">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 sticky top-0">
          <tr>
            <th class="text-left px-4 py-2">Название</th>
            <th class="text-left px-4 py-2 w-32">Статус</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr
            v-for="c in categories"
            :key="c.id"
            :class="c.id === selectedId ? 'bg-blue-50' : 'hover:bg-gray-50'"
            class="cursor-pointer"
            @click="selectCategory(c)"
          >
            <td class="px-4 py-2">
              <div class="flex items-center gap-2">
                <span
                  v-if="c.color"
                  class="inline-block w-3 h-3 rounded-full shrink-0 border border-black/10"
                  :style="{ backgroundColor: c.color }"
                />
                <span
                  v-else
                  class="inline-block w-3 h-3 rounded-full shrink-0 border border-dashed border-gray-300"
                />
                {{ c.name }}
              </div>
            </td>
            <td class="px-4 py-2">
              <span v-if="c.active"
                class="inline-flex items-center gap-1 text-xs text-green-700 bg-green-100 px-2 py-0.5 rounded-full">
                Активна
              </span>
              <span v-else
                class="inline-flex items-center gap-1 text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                Скрыта
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile: card list -->
    <div class="flex-1 overflow-y-auto space-y-2 sm:hidden">
      <div
        v-for="c in categories"
        :key="c.id"
        :class="c.id === selectedId ? 'ring-2 ring-blue-300' : ''"
        class="border rounded-lg p-3 cursor-pointer flex items-center justify-between hover:bg-gray-50 active:bg-gray-100"
        @click="selectCategory(c)"
      >
        <div class="flex items-center gap-2">
          <span
            v-if="c.color"
            class="inline-block w-3 h-3 rounded-full shrink-0 border border-black/10"
            :style="{ backgroundColor: c.color }"
          />
          <span
            v-else
            class="inline-block w-3 h-3 rounded-full shrink-0 border border-dashed border-gray-300"
          />
          <span class="text-sm">{{ c.name }}</span>
        </div>
        <span v-if="c.active" class="text-xs text-green-700 bg-green-100 px-2 py-0.5 rounded-full">Активна</span>
        <span v-else class="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">Скрыта</span>
      </div>
      <div v-if="!categories.length" class="text-center text-sm text-gray-400 py-8">
        Нет категорий
      </div>
    </div>

    <!-- Slide Panel Form -->
    <SlidePanel
      :open="formOpen"
      :title="selectedId ? 'Редактировать' : 'Добавить'"
      width="w-72"
      @close="clearForm"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
          <input v-model="name"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
        </div>

        <ColorPicker
          v-model="color"
          :recent-colors="recentColors"
          @use-color="addRecentColor"
        />

        <div class="flex flex-col gap-2 pt-4 border-t">
          <button class="w-full px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700" @click="onSave">
            Сохранить
          </button>
          <button v-if="selectedId && !isInactive"
            class="w-full px-4 py-2 rounded-lg border border-orange-300 text-orange-600 text-sm hover:bg-orange-50"
            @click="onHideActive">
            Скрыть
          </button>
          <button v-if="isInactive"
            class="w-full px-4 py-2 rounded-lg border border-green-300 text-green-600 text-sm hover:bg-green-50"
            @click="onActivate">
            Активировать
          </button>
          <button v-if="selectedId"
            class="w-full px-4 py-2 rounded-lg border border-red-300 text-red-600 text-sm hover:bg-red-50"
            @click="onDelete">
            Удалить
          </button>
        </div>
      </div>
    </SlidePanel>

    <ConfirmDialog
      :open="confirmOpen"
      message="Скрыть категорию? Существующие записи сохранятся, но добавить новые с этой категорией будет нельзя."
      @confirm="onConfirmSoft"
      @cancel="confirmOpen = false"
    />

    <ConfirmDialog
      :open="confirmDeleteOpen"
      message="Удалить категорию? Это действие необратимо."
      @confirm="onConfirmDelete"
      @cancel="confirmDeleteOpen = false"
    />

    <!-- Used category dialog: step 1 — choose action -->
    <Teleport to="body">
      <div v-if="dialogStep === 'options'" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @mousedown.self="closeUsedDialog" @touchstart.self.passive="closeUsedDialog">
        <div class="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 p-6">
          <h3 class="text-lg font-semibold mb-2">Категория используется</h3>
          <p class="text-sm text-gray-600 mb-6">Эта категория привязана к записям. Что сделать?</p>
          <div class="flex justify-end gap-2">
            <button
              class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
              @click="closeUsedDialog"
            >Отмена</button>
            <button
              class="px-4 py-2 rounded-lg border border-orange-300 text-orange-600 text-sm hover:bg-orange-50"
              @click="onHideUsed"
            >Скрыть</button>
            <button
              class="px-4 py-2 rounded-lg border border-blue-300 text-blue-700 text-sm hover:bg-blue-50 disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="!canMoveAndDelete"
              :title="canMoveAndDelete ? undefined : 'Нет других категорий для перемещения'"
              @click="onSelectMoveTarget"
            >Переместить и удалить</button>
            <button
              class="px-4 py-2 rounded-lg bg-red-600 text-white text-sm hover:bg-red-700"
              @click="onConfirmHard"
            >Удалить полностью</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Used category dialog: step 2 — select target category -->
    <Teleport to="body">
      <div v-if="dialogStep === 'select-target'" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @mousedown.self="closeUsedDialog" @touchstart.self.passive="closeUsedDialog">
        <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
          <h3 class="text-lg font-semibold mb-2">Переместить записи в другую категорию</h3>
          <p class="text-sm text-gray-600 mb-4">
            Выберите категорию, в которую будут перемещены все связанные записи. После этого текущая категория будет удалена.
          </p>
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-1">Целевая категория</label>
            <select
              v-model="targetCategoryId"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              :disabled="moveLoading"
            >
              <option v-for="c in moveTargetOptions" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="flex justify-end gap-2">
            <button
              class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 disabled:opacity-40"
              :disabled="moveLoading"
              @click="dialogStep = 'options'"
            >Назад</button>
            <button
              class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
              :disabled="moveLoading || !targetCategoryId"
              @click="onConfirmMoveAndDelete"
            >
              <svg v-if="moveLoading" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              {{ moveLoading ? 'Перемещение...' : 'Переместить и удалить' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
