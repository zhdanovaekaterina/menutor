<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { Preference, PreferenceCreate } from '@/api/types'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SlidePanel from '@/components/ui/SlidePanel.vue'
import PreferenceForm from './PreferenceForm.vue'
import { usePreferencesStore } from '@/stores/preferences'
import { useToastStore } from '@/stores/toast'

const store = usePreferencesStore()
const toast = useToastStore()

const selectedItem = ref<Preference | null>(null)
const formOpen = ref(false)
const confirmOpen = ref(false)

onMounted(() => store.load())

function typeLabel(type: Preference['type']): string {
  return type === 'CATEGORY_BASED' ? 'По категориям' : 'Аллергия'
}

function modeLabel(p: Preference): string {
  if (p.type === 'ALLERGY') return 'Блокировать'
  return p.mode === 'BLOCKED' ? 'Блокировать' : 'Разрешать'
}

function modeBadgeClass(p: Preference): string {
  const blocked = p.type === 'ALLERGY' || p.mode === 'BLOCKED'
  return blocked
    ? 'text-red-700 bg-red-100'
    : 'text-green-700 bg-green-100'
}

function openNew() {
  selectedItem.value = null
  formOpen.value = true
}

function openEdit(item: Preference) {
  selectedItem.value = item
  formOpen.value = true
}

function openDelete(item: Preference) {
  selectedItem.value = item
  confirmOpen.value = true
}

function closeForm() {
  formOpen.value = false
  selectedItem.value = null
}

async function onSave(data: PreferenceCreate) {
  if (!data.name.trim()) { toast.show('Введите название', 'error'); return }
  try {
    if (selectedItem.value) {
      await store.update(selectedItem.value.id, data)
    } else {
      await store.create(data)
    }
    closeForm()
  } catch { /* handled by store */ }
}

async function onConfirmDelete() {
  confirmOpen.value = false
  if (!selectedItem.value) return
  try {
    await store.remove(selectedItem.value.id)
    selectedItem.value = null
  } catch { /* handled by store */ }
}
</script>

<template>
  <div class="h-full flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <h3 class="font-semibold text-sm">Пищевые предпочтения</h3>
      <button
        class="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700"
        @click="openNew"
      >
        + Добавить
      </button>
    </div>

    <!-- Desktop table -->
    <div class="hidden sm:block flex-1 overflow-y-auto border rounded-lg">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 sticky top-0">
          <tr>
            <th class="text-left px-4 py-2">Название</th>
            <th class="text-left px-4 py-2 w-36">Тип</th>
            <th class="text-left px-4 py-2 w-36">Действие</th>
            <th class="px-4 py-2 w-24"></th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr
            v-for="item in store.items"
            :key="item.id"
            class="hover:bg-gray-50"
          >
            <td class="px-4 py-2 font-medium">{{ item.name }}</td>
            <td class="px-4 py-2 text-gray-600">{{ typeLabel(item.type) }}</td>
            <td class="px-4 py-2">
              <span
                class="inline-flex items-center text-xs px-2 py-0.5 rounded-full"
                :class="modeBadgeClass(item)"
              >
                {{ modeLabel(item) }}
              </span>
            </td>
            <td class="px-4 py-2">
              <div class="flex items-center justify-end gap-1">
                <button
                  class="p-1 rounded hover:bg-gray-100 text-gray-500 transition-colors"
                  title="Редактировать"
                  @click="openEdit(item)"
                >
                  <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125" />
                  </svg>
                </button>
                <button
                  class="p-1 rounded hover:bg-red-50 text-red-400 transition-colors"
                  title="Удалить"
                  @click="openDelete(item)"
                >
                  <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                  </svg>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!store.items.length">
            <td colspan="4" class="px-4 py-8 text-center text-sm text-gray-400">
              Нет предпочтений
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile card list -->
    <div class="flex-1 overflow-y-auto space-y-2 sm:hidden">
      <div
        v-for="item in store.items"
        :key="item.id"
        class="border rounded-lg p-3 hover:bg-gray-50 active:bg-gray-100 transition-colors"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0">
            <p class="font-medium text-sm truncate">{{ item.name }}</p>
            <p class="text-xs text-gray-500 mt-0.5">{{ typeLabel(item.type) }}</p>
            <span
              class="inline-flex items-center text-xs px-2 py-0.5 rounded-full mt-1"
              :class="modeBadgeClass(item)"
            >
              {{ modeLabel(item) }}
            </span>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <button
              class="p-1.5 rounded hover:bg-gray-100 text-gray-500"
              @click="openEdit(item)"
            >
              <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125" />
              </svg>
            </button>
            <button
              class="p-1.5 rounded hover:bg-red-50 text-red-400"
              @click="openDelete(item)"
            >
              <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
              </svg>
            </button>
          </div>
        </div>
      </div>
      <div v-if="!store.items.length" class="text-center text-sm text-gray-400 py-8">
        Нет предпочтений
      </div>
    </div>

    <!-- Slide Panel Form -->
    <SlidePanel
      :open="formOpen"
      :title="selectedItem ? 'Редактировать предпочтение' : 'Добавить предпочтение'"
      width="w-96"
      @close="closeForm"
    >
      <PreferenceForm
        :initial="selectedItem"
        @save="onSave"
        @cancel="closeForm"
      />
    </SlidePanel>

    <ConfirmDialog
      :open="confirmOpen"
      message="Удалить предпочтение? Оно будет отвязано от членов семьи."
      danger
      @confirm="onConfirmDelete"
      @cancel="confirmOpen = false"
    />
  </div>
</template>
