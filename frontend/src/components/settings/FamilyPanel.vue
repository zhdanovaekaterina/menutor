<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { FamilyMember, FamilyMemberCreate } from '@/api/types'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SlidePanel from '@/components/ui/SlidePanel.vue'
import { useFamilyStore } from '@/stores/family'
import { useToastStore } from '@/stores/toast'

const store = useFamilyStore()
const toast = useToastStore()

const selectedId = ref<number | null>(null)
const name = ref('')
const portionMultiplier = ref(1.0)
const dietaryRestrictions = ref('')
const comment = ref('')
const confirmOpen = ref(false)
const formOpen = ref(false)

onMounted(() => store.load())

function selectMember(m: FamilyMember) {
  selectedId.value = m.id
  name.value = m.name
  portionMultiplier.value = m.portion_multiplier
  dietaryRestrictions.value = m.dietary_restrictions
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
  dietaryRestrictions.value = ''
  comment.value = ''
  formOpen.value = false
}

async function onSave() {
  if (!name.value.trim()) { toast.show('Введите имя', 'error'); return }
  const data: FamilyMemberCreate = {
    name: name.value.trim(),
    portion_multiplier: portionMultiplier.value,
    dietary_restrictions: dietaryRestrictions.value,
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
    <div class="flex-1 overflow-y-auto border rounded-lg">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 sticky top-0">
          <tr>
            <th class="text-left px-4 py-2">Имя</th>
            <th class="text-center px-4 py-2 w-28">Коэф.</th>
            <th class="text-left px-4 py-2">Ограничения</th>
            <th class="text-left px-4 py-2">Комментарий</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr
            v-for="m in store.members"
            :key="m.id"
            :class="m.id === selectedId ? 'bg-blue-50' : 'hover:bg-gray-50'"
            class="cursor-pointer"
            @click="selectMember(m)"
          >
            <td class="px-4 py-2">{{ m.name }}</td>
            <td class="px-4 py-2 text-center">{{ m.portion_multiplier }}</td>
            <td class="px-4 py-2 text-gray-600">{{ m.dietary_restrictions || '—' }}</td>
            <td class="px-4 py-2 text-gray-600">{{ m.comment || '—' }}</td>
          </tr>
        </tbody>
      </table>
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
          <label class="block text-sm font-medium text-gray-700 mb-1">Ограничения</label>
          <input v-model="dietaryRestrictions"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
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
