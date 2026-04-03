<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { MealType, MealTypeCreate } from '@/api/types'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SlidePanel from '@/components/ui/SlidePanel.vue'
import { useMealTypeStore } from '@/stores/mealTypes'
import { useToastStore } from '@/stores/toast'

const store = useMealTypeStore()
const toast = useToastStore()

const selectedId = ref<number | null>(null)
const name = ref('')
const time = ref('')
const formOpen = ref(false)
const confirmOpen = ref(false)
const usageMenuNames = ref<string[]>([])
const usageConfirmOpen = ref(false)

onMounted(() => {
  store.load()
})

function selectItem(mt: MealType) {
  selectedId.value = mt.id
  name.value = mt.name
  time.value = mt.time
  formOpen.value = true
}

function openNew() {
  clearForm()
  formOpen.value = true
}

function clearForm() {
  selectedId.value = null
  name.value = ''
  time.value = ''
  formOpen.value = false
}

async function onSave() {
  if (!name.value.trim()) { toast.show('Введите название', 'error'); return }
  if (!time.value) { toast.show('Укажите время', 'error'); return }
  const data: MealTypeCreate = {
    name: name.value.trim(),
    time: time.value,
  }
  try {
    if (selectedId.value) await store.update(selectedId.value, data)
    else await store.create(data)
    clearForm()
  } catch { /* toast handled by store */ }
}

async function onDelete() {
  if (!selectedId.value) return
  const usage = await store.checkUsage(selectedId.value)
  if (!usage) return
  if (usage.count > 0) {
    usageMenuNames.value = usage.menus.map((m) => m.name)
    usageConfirmOpen.value = true
  } else {
    confirmOpen.value = true
  }
}

async function onConfirmDelete() {
  confirmOpen.value = false
  if (!selectedId.value) return
  await store.remove(selectedId.value)
  clearForm()
}

async function onConfirmDeleteUsed() {
  usageConfirmOpen.value = false
  if (!selectedId.value) return
  await store.remove(selectedId.value)
  clearForm()
}
</script>

<template>
  <div class="h-full flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <h3 class="font-semibold text-sm">Приемы пищи</h3>
      <button
        class="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="store.customCount >= 10"
        :title="store.customCount >= 10 ? 'Достигнут лимит (10)' : undefined"
        @click="openNew"
      >
        + Добавить
      </button>
    </div>

    <!-- Table (desktop) -->
    <div class="hidden sm:block flex-1 overflow-y-auto border rounded-lg">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 sticky top-0">
          <tr>
            <th class="text-left px-4 py-2">Название</th>
            <th class="text-center px-4 py-2 w-24">Время</th>
            <th class="text-left px-4 py-2 w-36">Тип</th>
            <th class="text-right px-4 py-2 w-28">Действия</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr
            v-for="mt in store.sorted"
            :key="mt.id"
            :class="mt.id === selectedId ? 'bg-blue-50' : 'hover:bg-gray-50'"
          >
            <td class="px-4 py-2">{{ mt.name }}</td>
            <td class="px-4 py-2 text-center text-gray-600">{{ mt.time }}</td>
            <td class="px-4 py-2">
              <span v-if="mt.is_system"
                class="inline-flex items-center text-xs text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                Системный
              </span>
              <span v-else
                class="inline-flex items-center text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full">
                Пользовательский
              </span>
            </td>
            <td class="px-4 py-2 text-right">
              <div class="flex items-center justify-end gap-1">
                <button
                  class="px-2.5 py-1 rounded-lg border border-gray-300 text-xs hover:bg-gray-50"
                  @click="selectItem(mt)"
                >
                  Изменить
                </button>
                <button
                  v-if="!mt.is_system"
                  class="px-2.5 py-1 rounded-lg border border-red-300 text-red-600 text-xs hover:bg-red-50"
                  @click="selectedId = mt.id; onDelete()"
                >
                  Удалить
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile: card list -->
    <div class="flex-1 overflow-y-auto space-y-2 sm:hidden">
      <div
        v-for="mt in store.sorted"
        :key="mt.id"
        :class="mt.id === selectedId ? 'ring-2 ring-blue-300' : ''"
        class="border rounded-lg p-3 hover:bg-gray-50 active:bg-gray-100 transition-colors"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="font-medium text-sm">{{ mt.name }}</span>
            <span class="text-xs text-gray-400">{{ mt.time }}</span>
          </div>
          <span v-if="mt.is_system"
            class="text-xs text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
            Системный
          </span>
          <span v-else
            class="text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full">
            Пользов.
          </span>
        </div>
        <div class="flex gap-2 mt-2">
          <button
            class="px-3 py-1 rounded-lg border border-gray-300 text-xs hover:bg-gray-50"
            @click="selectItem(mt)"
          >
            Изменить
          </button>
          <button
            v-if="!mt.is_system"
            class="px-3 py-1 rounded-lg border border-red-300 text-red-600 text-xs hover:bg-red-50"
            @click="selectedId = mt.id; onDelete()"
          >
            Удалить
          </button>
        </div>
      </div>
      <div v-if="!store.sorted.length" class="text-center text-sm text-gray-400 py-8">
        Нет приемов пищи
      </div>
    </div>

    <!-- Footer counter -->
    <div class="text-xs text-gray-400 text-right">
      Пользовательских: {{ store.customCount }} / 10
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
          <input
            v-model="name"
            maxlength="50"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Время *</label>
          <input
            v-model="time"
            type="time"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          />
        </div>

        <div class="flex gap-2 pt-4 border-t">
          <button
            class="flex-1 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700"
            @click="onSave"
          >
            Сохранить
          </button>
          <button
            v-if="selectedId && !store.items.find(t => t.id === selectedId)?.is_system"
            class="flex-1 px-4 py-2 rounded-lg bg-red-600 text-white text-sm hover:bg-red-700"
            @click="onDelete"
          >
            Удалить
          </button>
        </div>
      </div>
    </SlidePanel>

    <!-- Simple confirm (not used in menus) -->
    <ConfirmDialog
      :open="confirmOpen"
      message="Удалить этот тип приема пищи?"
      danger
      @confirm="onConfirmDelete"
      @cancel="confirmOpen = false"
    />

    <!-- Confirm delete used in menus -->
    <Teleport to="body">
      <div
        v-if="usageConfirmOpen"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @mousedown.self="usageConfirmOpen = false"
        @touchstart.self.passive="usageConfirmOpen = false"
      >
        <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
          <h3 class="text-lg font-semibold mb-2">Тип используется в меню</h3>
          <p class="text-sm text-gray-600 mb-3">
            Этот тип приема пищи используется в следующих меню:
          </p>
          <ul class="mb-4 text-sm text-gray-800 list-disc list-inside space-y-0.5">
            <li v-for="menuName in usageMenuNames" :key="menuName">{{ menuName }}</li>
          </ul>
          <p class="text-sm text-red-600 mb-6">
            Удаление приведёт к потере связанных слотов. Продолжить?
          </p>
          <div class="flex justify-end gap-2">
            <button
              class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
              @click="usageConfirmOpen = false"
            >
              Отмена
            </button>
            <button
              class="px-4 py-2 rounded-lg bg-red-600 text-white text-sm hover:bg-red-700"
              @click="onConfirmDeleteUsed"
            >
              Удалить
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
