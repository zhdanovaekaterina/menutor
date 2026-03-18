<script setup lang="ts">
import { watch, ref, computed } from 'vue'
import type { Category } from '@/api/types'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SlidePanel from '@/components/ui/SlidePanel.vue'
import { useCategoryStore } from '@/stores/categories'
import { useToastStore } from '@/stores/toast'

const props = defineProps<{ type: 'product' | 'recipe' }>()

const store = useCategoryStore()
const toast = useToastStore()

const categories = computed(() => store.list(props.type).value)

const selectedId = ref<number | null>(null)
const name = ref('')
const confirmOpen = ref(false)
const confirmDeleteOpen = ref(false)
const confirmHardOpen = ref(false)
const formOpen = ref(false)

watch(() => props.type, () => store.load(props.type), { immediate: true })

const selected = computed(() => categories.value.find((c) => c.id === selectedId.value))
const isInactive = computed(() => selected.value?.active === false)

function selectCategory(c: Category) {
  selectedId.value = c.id
  name.value = c.name
  formOpen.value = true
}

function openNew() {
  clearForm()
  formOpen.value = true
}

function clearForm() {
  selectedId.value = null
  name.value = ''
  formOpen.value = false
}

async function onSave() {
  if (!name.value.trim()) { toast.show('Введите название', 'error'); return }
  try {
    if (selectedId.value) await store.edit(props.type, selectedId.value, name.value.trim())
    else await store.create(props.type, name.value.trim())
    clearForm()
  } catch { /* handled */ }
}

async function onDelete() {
  if (!selectedId.value) return
  const used = await store.isUsed(props.type, selectedId.value)
  if (used) {
    confirmHardOpen.value = true
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
  confirmHardOpen.value = false
  if (!selectedId.value) return
  await store.remove(props.type, selectedId.value, true)
  clearForm()
}

async function onHideUsed() {
  confirmHardOpen.value = false
  if (!selectedId.value) return
  await store.remove(props.type, selectedId.value, false)
  clearForm()
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
            <td class="px-4 py-2">{{ c.name }}</td>
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
        <span class="text-sm">{{ c.name }}</span>
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

    <!-- Used category dialog: hide or hard delete -->
    <Teleport to="body">
      <div v-if="confirmHardOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
          <h3 class="text-lg font-semibold mb-2">Категория используется</h3>
          <p class="text-sm text-gray-600 mb-6">Эта категория привязана к записям. Что сделать?</p>
          <div class="flex justify-end gap-2">
            <button class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
              @click="confirmHardOpen = false">Отмена</button>
            <button class="px-4 py-2 rounded-lg border border-orange-300 text-orange-600 text-sm hover:bg-orange-50"
              @click="onHideUsed">Скрыть</button>
            <button class="px-4 py-2 rounded-lg bg-red-600 text-white text-sm hover:bg-red-700"
              @click="onConfirmHard">Удалить полностью</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
