<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { FamilyMember, FamilyMemberCreate } from '@/api/types'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SlidePanel from '@/components/ui/SlidePanel.vue'
import { useFamilyStore } from '@/stores/family'
import { usePreferencesStore } from '@/stores/preferences'
import { useToastStore } from '@/stores/toast'

const store = useFamilyStore()
const preferencesStore = usePreferencesStore()
const toast = useToastStore()

const selectedId = ref<number | null>(null)
const name = ref('')
const portionMultiplier = ref(1.0)
const selectedPreferenceIds = ref<number[]>([])
const comment = ref('')
const confirmOpen = ref(false)
const formOpen = ref(false)

onMounted(() => {
  store.load()
  preferencesStore.load()
})

function togglePreference(id: number) {
  const idx = selectedPreferenceIds.value.indexOf(id)
  if (idx === -1) selectedPreferenceIds.value.push(id)
  else selectedPreferenceIds.value.splice(idx, 1)
}

function selectMember(m: FamilyMember) {
  selectedId.value = m.id
  name.value = m.name
  portionMultiplier.value = m.portion_multiplier
  selectedPreferenceIds.value = [...m.preference_ids]
  comment.value = m.comment
  formOpen.value = true
}

function openNew() {
  clearForm()
  formOpen.value = true
}

function clearForm() {
  selectedId.value = null
  name.value = ''
  portionMultiplier.value = 1.0
  selectedPreferenceIds.value = []
  comment.value = ''
  formOpen.value = false
}

async function onSave() {
  if (!name.value.trim()) { toast.show('Введите имя', 'error'); return }
  const data: FamilyMemberCreate = {
    name: name.value.trim(),
    portion_multiplier: portionMultiplier.value,
    preference_ids: selectedPreferenceIds.value,
    comment: comment.value,
  }
  try {
    if (selectedId.value) await store.update(selectedId.value, data)
    else await store.create(data)
    clearForm()
  } catch { /* toast handled by store */ }
}

async function onConfirmDelete() {
  confirmOpen.value = false
  if (!selectedId.value) return
  try {
    await store.remove(selectedId.value)
    clearForm()
  } catch { /* toast handled by store */ }
}
</script>

<template>
  <div class="h-full flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <h3 class="font-semibold text-sm">Члены семьи</h3>
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
            <th class="text-left px-4 py-2">Имя</th>
            <th class="text-center px-4 py-2 w-28">Коэф.</th>
            <th class="text-left px-4 py-2">Предпочтения</th>
            <th class="text-left px-4 py-2">Комментарий</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr
            v-for="m in store.items"
            :key="m.id"
            :class="m.id === selectedId ? 'bg-blue-50' : 'hover:bg-gray-50'"
            class="cursor-pointer"
            @click="selectMember(m)"
          >
            <td class="px-4 py-2">{{ m.name }}</td>
            <td class="px-4 py-2 text-center">{{ m.portion_multiplier }}</td>
            <td class="px-4 py-2 text-gray-600">
              <span v-if="m.preference_ids.length" class="flex flex-wrap gap-1">
                <span
                  v-for="pid in m.preference_ids"
                  :key="pid"
                  class="inline-flex text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700"
                >
                  {{ preferencesStore.items.find((p) => p.id === pid)?.name ?? pid }}
                </span>
              </span>
              <span v-else>—</span>
            </td>
            <td class="px-4 py-2 text-gray-600">{{ m.comment || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile: card list -->
    <div class="flex-1 overflow-y-auto space-y-2 sm:hidden">
      <div
        v-for="m in store.items"
        :key="m.id"
        :class="m.id === selectedId ? 'ring-2 ring-blue-300' : ''"
        class="border rounded-lg p-3 cursor-pointer hover:bg-gray-50 active:bg-gray-100 transition-colors"
        @click="selectMember(m)"
      >
        <div class="flex items-center justify-between">
          <span class="font-medium text-sm">{{ m.name }}</span>
          <span class="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">&times;{{ m.portion_multiplier }}</span>
        </div>
        <div v-if="m.preference_ids.length" class="flex flex-wrap gap-1 mt-1">
          <span
            v-for="pid in m.preference_ids"
            :key="pid"
            class="inline-flex text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700"
          >
            {{ preferencesStore.items.find((p) => p.id === pid)?.name ?? pid }}
          </span>
        </div>
        <p v-if="m.comment" class="text-xs text-gray-400 mt-0.5">{{ m.comment }}</p>
      </div>
      <div v-if="!store.items.length" class="text-center text-sm text-gray-400 py-8">
        Нет членов семьи
      </div>
    </div>

    <!-- Slide Panel Form -->
    <SlidePanel
      :open="formOpen"
      :title="selectedId ? 'Редактировать' : 'Добавить'"
      width="w-80"
      @close="clearForm"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Имя *</label>
          <input v-model="name"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Коэф. порции</label>
          <input v-model.number="portionMultiplier" type="number" min="0.1" max="5" step="0.1"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Пищевые предпочтения</label>
          <div
            v-if="preferencesStore.items.length"
            class="border border-gray-300 rounded-lg divide-y max-h-40 overflow-y-auto"
          >
            <label
              v-for="pref in preferencesStore.items"
              :key="pref.id"
              class="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer text-sm"
            >
              <input
                type="checkbox"
                :checked="selectedPreferenceIds.includes(pref.id)"
                class="rounded"
                @change="togglePreference(pref.id)"
              />
              {{ pref.name }}
            </label>
          </div>
          <p v-else class="text-sm text-gray-400">Нет предпочтений. Добавьте их в разделе «Предпочтения».</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Комментарий</label>
          <input v-model="comment"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
        </div>

        <div class="flex gap-2 pt-4 border-t">
          <button class="flex-1 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700" @click="onSave">
            Сохранить
          </button>
          <button v-if="selectedId"
            class="flex-1 px-4 py-2 rounded-lg bg-red-600 text-white text-sm hover:bg-red-700"
            @click="confirmOpen = true">
            Удалить
          </button>
        </div>
      </div>
    </SlidePanel>

    <ConfirmDialog
      :open="confirmOpen"
      message="Удалить выбранного члена семьи?"
      danger
      @confirm="onConfirmDelete"
      @cancel="confirmOpen = false"
    />
  </div>
</template>
