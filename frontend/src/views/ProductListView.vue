<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { ProductCreate } from '@/api/types'
import ProductForm from '@/components/products/ProductForm.vue'
import ProductTable from '@/components/products/ProductTable.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SlidePanel from '@/components/ui/SlidePanel.vue'
import { useProductStore } from '@/stores/products'
import { useToastStore } from '@/stores/toast'

const store = useProductStore()
const toast = useToastStore()

const selectedId = ref<number | null>(null)
const confirmDeleteOpen = ref(false)
const formOpen = ref(false)

onMounted(() => store.load())

const selectedProduct = computed(() =>
  store.products.find((p) => p.id === selectedId.value) ?? null,
)

function onSelect(id: number) {
  selectedId.value = id
  formOpen.value = true
}

function openNew() {
  selectedId.value = null
  formOpen.value = true
}

async function onSave(data: ProductCreate, id: number | null) {
  try {
    if (id) {
      await store.update(id, data)
    } else {
      const created = await store.create(data)
      selectedId.value = created.id
    }
  } catch (e: any) {
    toast.show(e?.response?.data?.detail ?? 'Ошибка сохранения', 'error')
  }
}

function onRemove(id: number) {
  selectedId.value = id
  confirmDeleteOpen.value = true
}

async function onConfirmDelete() {
  confirmDeleteOpen.value = false
  if (!selectedId.value) return
  try {
    await store.remove(selectedId.value)
    selectedId.value = null
    formOpen.value = false
  } catch (e: any) {
    toast.show(e?.response?.data?.detail ?? 'Ошибка удаления', 'error')
  }
}

function onClear() {
  selectedId.value = null
  formOpen.value = false
}
</script>

<template>
  <div class="h-full flex flex-col p-4 gap-4">
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-bold">Продукты</h1>
      <button
        class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700"
        @click="openNew"
      >
        + Новый продукт
      </button>
    </div>

    <div class="flex-1 min-h-0">
      <ProductTable
        :products="store.products"
        :categories="store.categories"
        :selected-id="selectedId"
        @select="onSelect"
      />
    </div>

    <SlidePanel
      :open="formOpen"
      :title="selectedProduct ? 'Редактировать продукт' : 'Новый продукт'"
      @close="onClear"
    >
      <ProductForm
        :product="selectedProduct"
        :categories="store.categories"
        @save="onSave"
        @remove="onRemove"
        @clear="onClear"
      />
    </SlidePanel>

    <ConfirmDialog
      :open="confirmDeleteOpen"
      :message="`Удалить продукт «${selectedProduct?.name ?? ''}»?`"
      danger
      @confirm="onConfirmDelete"
      @cancel="confirmDeleteOpen = false"
    />
  </div>
</template>
