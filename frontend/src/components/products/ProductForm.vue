<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ActiveCategory, Product, ProductCreate } from '@/api/types'
import { useToastStore } from '@/stores/toast'
import { autoConversionFactor } from '@/utils/units'

const toast = useToastStore()

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
const purchaseUnit = ref('g')
const priceAmount = ref(0)
const conversionFactor = ref(1)

const autoFactor = computed(() => autoConversionFactor(recipeUnit.value, purchaseUnit.value))
const isFactorLocked = computed(() => autoFactor.value !== null)

watch([recipeUnit, purchaseUnit], () => {
  if (autoFactor.value !== null) {
    conversionFactor.value = autoFactor.value
  }
})

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
  purchaseUnit.value = 'g'
  priceAmount.value = 0
  conversionFactor.value = 1
  emit('clear')
}

function onSave() {
  if (!name.value.trim()) { toast.show('Введите название продукта', 'error'); return }
  if (categoryId.value == null) { toast.show('Выберите категорию', 'error'); return }
  const data: ProductCreate = {
    name: name.value.trim(),
    category_id: categoryId.value,
    recipe_unit: recipeUnit.value,
    purchase_unit: purchaseUnit.value,
    price_amount: String(priceAmount.value),
    brand: brand.value,
    supplier: supplier.value,
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
        <label class="block text-sm font-medium text-gray-700 mb-1">Коэф. конвертации</label>
        <input v-model.number="conversionFactor" type="number" min="0.001" step="0.001"
          :disabled="isFactorLocked"
          :class="isFactorLocked ? 'bg-gray-100 text-gray-500 cursor-not-allowed' : ''"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
        <p v-if="isFactorLocked" class="text-xs text-gray-400 mt-1">Рассчитан автоматически</p>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Цена (руб.)</label>
        <input v-model.number="priceAmount" type="number" min="0" step="0.01"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
      </div>
    </div>

    <div class="flex gap-2 pt-4 border-t">
      <button
        class="flex-1 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
        @click="onSave"
      >
        {{ product ? 'Сохранить' : 'Создать' }}
      </button>
      <button
        v-if="product"
        class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
        @click="clearForm"
      >
        Новый
      </button>
      <button
        v-if="product"
        class="px-4 py-2 rounded-lg border border-red-300 text-red-600 text-sm hover:bg-red-50 transition-colors"
        @click="emit('remove', product.id)"
      >
        Удалить
      </button>
    </div>
  </div>
</template>
