<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { Preference, PreferenceCreate } from '@/api/types'
import { useCategoryStore } from '@/stores/categories'
import { useProductStore } from '@/stores/products'

const props = defineProps<{
  initial?: Preference | null
}>()

const emit = defineEmits<{
  save: [data: PreferenceCreate]
  cancel: []
}>()

const categoryStore = useCategoryStore()
const productStore = useProductStore()

onMounted(async () => {
  await Promise.all([
    categoryStore.load('product'),
    productStore.allItems.length === 0 ? productStore.load() : Promise.resolve(),
  ])
})

const name = ref(props.initial?.name ?? '')
const type = ref<'CATEGORY_BASED' | 'ALLERGY'>(props.initial?.type ?? 'CATEGORY_BASED')
const mode = ref<'BLOCKED' | 'ALLOWED'>(props.initial?.mode ?? 'BLOCKED')
const selectedCategoryIds = ref<number[]>(props.initial?.category_ids ?? [])
const selectedProductIds = ref<number[]>(props.initial?.product_ids ?? [])

// ALLERGY always forces BLOCKED mode
watch(type, (newType) => {
  if (newType === 'ALLERGY') {
    mode.value = 'BLOCKED'
    selectedCategoryIds.value = []
  } else {
    selectedProductIds.value = []
  }
})

const activeProductCategories = computed(() =>
  categoryStore.productCategories.filter((c) => c.active),
)

function toggleCategory(id: number) {
  const idx = selectedCategoryIds.value.indexOf(id)
  if (idx === -1) selectedCategoryIds.value.push(id)
  else selectedCategoryIds.value.splice(idx, 1)
}

function toggleProduct(id: number) {
  const idx = selectedProductIds.value.indexOf(id)
  if (idx === -1) selectedProductIds.value.push(id)
  else selectedProductIds.value.splice(idx, 1)
}

function onSubmit() {
  emit('save', {
    name: name.value.trim(),
    type: type.value,
    mode: type.value === 'ALLERGY' ? 'BLOCKED' : mode.value,
    category_ids: type.value === 'CATEGORY_BASED' ? selectedCategoryIds.value : [],
    product_ids: type.value === 'ALLERGY' ? selectedProductIds.value : [],
  })
}
</script>

<template>
  <div class="space-y-4">
    <!-- Name -->
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
      <input
        v-model="name"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        placeholder="Например: Без глютена"
      />
    </div>

    <!-- Type -->
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Тип</label>
      <select
        v-model="type"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
      >
        <option value="CATEGORY_BASED">По категориям</option>
        <option value="ALLERGY">Аллергия</option>
      </select>
    </div>

    <!-- Mode (hidden for ALLERGY since it's always BLOCKED) -->
    <div v-if="type === 'CATEGORY_BASED'">
      <label class="block text-sm font-medium text-gray-700 mb-1">Действие</label>
      <select
        v-model="mode"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
      >
        <option value="BLOCKED">Блокировать</option>
        <option value="ALLOWED">Разрешать</option>
      </select>
    </div>

    <!-- Categories (for CATEGORY_BASED) -->
    <div v-if="type === 'CATEGORY_BASED'">
      <label class="block text-sm font-medium text-gray-700 mb-1">Категории продуктов</label>
      <div
        v-if="activeProductCategories.length"
        class="border border-gray-300 rounded-lg divide-y max-h-40 overflow-y-auto"
      >
        <label
          v-for="cat in activeProductCategories"
          :key="cat.id"
          class="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer text-sm"
        >
          <input
            type="checkbox"
            :checked="selectedCategoryIds.includes(cat.id)"
            class="rounded"
            @change="toggleCategory(cat.id)"
          />
          <span
            v-if="cat.color"
            class="inline-block w-2.5 h-2.5 rounded-full shrink-0 border border-black/10"
            :style="{ backgroundColor: cat.color }"
          />
          {{ cat.name }}
        </label>
      </div>
      <p v-else class="text-sm text-gray-400">Нет активных категорий</p>
    </div>

    <!-- Products (for ALLERGY) -->
    <div v-if="type === 'ALLERGY'">
      <label class="block text-sm font-medium text-gray-700 mb-1">Продукты-аллергены</label>
      <div
        v-if="productStore.allItems.length"
        class="border border-gray-300 rounded-lg divide-y max-h-48 overflow-y-auto"
      >
        <label
          v-for="p in productStore.allItems"
          :key="p.id"
          class="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer text-sm"
        >
          <input
            type="checkbox"
            :checked="selectedProductIds.includes(p.id)"
            class="rounded"
            @change="toggleProduct(p.id)"
          />
          {{ p.name }}
        </label>
      </div>
      <p v-else class="text-sm text-gray-400">Нет продуктов</p>
    </div>

    <!-- Actions -->
    <div class="flex gap-2 pt-4 border-t">
      <button
        class="flex-1 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700"
        @click="onSubmit"
      >
        Сохранить
      </button>
      <button
        class="flex-1 px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
        @click="emit('cancel')"
      >
        Отмена
      </button>
    </div>
  </div>
</template>
