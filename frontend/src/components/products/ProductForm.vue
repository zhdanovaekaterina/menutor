<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ActiveCategory, Product, ProductCreate } from '@/api/types'

const UNIT_OPTIONS = [
  { code: 'g', label: 'г' },
  { code: 'kg', label: 'кг' },
  { code: 'ml', label: 'мл' },
  { code: 'l', label: 'л' },
  { code: 'pcs', label: 'шт' },
  { code: 'box', label: 'кор' },
  { code: 'pack', label: 'уп' },
]

const props = defineProps<{
  product: Product | null
  categories: ActiveCategory[]
}>()

const emit = defineEmits<{
  save: [data: ProductCreate, id: number | null]
  remove: [id: number]
  clear: []
}>()

const name = ref('')
const categoryId = ref<number | null>(null)
const brand = ref('')
const supplier = ref('')
const recipeUnit = ref('g')
const purchaseUnit = ref('kg')
const priceAmount = ref(0)
const conversionFactor = ref(1)
const hasWeight = ref(false)
const weightPerPiece = ref(0)

watch(
  () => props.product,
  (p) => {
    if (p) {
      name.value = p.name
      categoryId.value = p.category_id
      brand.value = p.brand
      supplier.value = p.supplier
      recipeUnit.value = p.recipe_unit
      purchaseUnit.value = p.purchase_unit
      priceAmount.value = Number(p.price_amount)
      conversionFactor.value = p.conversion_factor
      hasWeight.value = p.weight_per_piece_g != null
      weightPerPiece.value = p.weight_per_piece_g ?? 0
    }
  },
  { immediate: true },
)

function clearForm() {
  name.value = ''
  categoryId.value = null
  brand.value = ''
  supplier.value = ''
  recipeUnit.value = 'g'
  purchaseUnit.value = 'kg'
  priceAmount.value = 0
  conversionFactor.value = 1
  hasWeight.value = false
  weightPerPiece.value = 0
  emit('clear')
}

function onSave() {
  if (!name.value.trim() || categoryId.value == null) return
  const data: ProductCreate = {
    name: name.value.trim(),
    category_id: categoryId.value,
    recipe_unit: recipeUnit.value,
    purchase_unit: purchaseUnit.value,
    price_amount: String(priceAmount.value),
    brand: brand.value,
    supplier: supplier.value,
    weight_per_piece_g: hasWeight.value ? weightPerPiece.value : null,
    conversion_factor: conversionFactor.value,
  }
  emit('save', data, props.product?.id ?? null)
}
</script>

<template>
  <div class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
      <input v-model="name"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Категория *</label>
      <select v-model="categoryId"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none">
        <option :value="null" disabled>Выберите...</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Бренд</label>
        <input v-model="brand"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Поставщик</label>
        <input v-model="supplier"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Ед. в рецепте</label>
        <select v-model="recipeUnit"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none">
          <option v-for="u in UNIT_OPTIONS" :key="u.code" :value="u.code">{{ u.label }}</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Ед. покупки</label>
        <select v-model="purchaseUnit"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none">
          <option v-for="u in UNIT_OPTIONS" :key="u.code" :value="u.code">{{ u.label }}</option>
        </select>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Цена (руб.)</label>
        <input v-model.number="priceAmount" type="number" min="0" step="0.01"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Коэф. конвертации</label>
        <input v-model.number="conversionFactor" type="number" min="0.001" step="0.001"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
      </div>
    </div>

    <div class="flex items-center gap-3">
      <input type="checkbox" v-model="hasWeight" class="rounded border-gray-300" />
      <label class="text-sm">Вес одной штуки</label>
      <input v-model.number="weightPerPiece" type="number" :disabled="!hasWeight" min="0" step="0.1"
        class="w-24 border border-gray-300 rounded-lg px-2 py-1.5 text-sm disabled:opacity-40" />
      <span class="text-sm text-gray-500">г</span>
    </div>

    <div class="flex gap-2 pt-4 border-t">
      <button class="flex-1 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700" @click="onSave">
        Сохранить
      </button>
      <button v-if="product" class="flex-1 px-4 py-2 rounded-lg bg-red-600 text-white text-sm hover:bg-red-700"
        @click="emit('remove', product.id)">
        Удалить
      </button>
    </div>
    <button class="w-full px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50" @click="clearForm">
      Очистить
    </button>
  </div>
</template>
