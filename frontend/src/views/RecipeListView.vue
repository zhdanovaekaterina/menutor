<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { RecipeCreate } from '@/api/types'
import RecipeForm from '@/components/recipes/RecipeForm.vue'
import RecipeTable from '@/components/recipes/RecipeTable.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import { useProductStore } from '@/stores/products'
import { useRecipeStore } from '@/stores/recipes'
import { useToastStore } from '@/stores/toast'

const store = useRecipeStore()
const productStore = useProductStore()
const toast = useToastStore()

const selectedId = ref<number | null>(null)
const confirmDeleteOpen = ref(false)

onMounted(async () => {
  await Promise.all([store.load(), productStore.load()])
})

const selectedRecipe = computed(() =>
  store.recipes.find((r) => r.id === selectedId.value) ?? null,
)

function onSelect(id: number) {
  selectedId.value = id
}

async function onSave(data: RecipeCreate, id: number | null) {
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
  } catch (e: any) {
    toast.show(e?.response?.data?.detail ?? 'Ошибка удаления', 'error')
  }
}

function onClear() {
  selectedId.value = null
}
</script>

<template>
  <div class="h-full flex flex-col p-4 gap-4">
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-bold">Рецепты</h1>
      <button
        class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700"
        @click="selectedId = null"
      >
        + Новый рецепт
      </button>
    </div>

    <div class="flex-1 flex gap-4 min-h-0">
      <div class="flex-1 min-w-0">
        <RecipeTable
          :recipes="store.recipes"
          :categories="store.categories"
          :selected-id="selectedId"
          @select="onSelect"
        />
      </div>
      <div class="w-96 shrink-0 overflow-y-auto border-l pl-4">
        <RecipeForm
          :recipe="selectedRecipe"
          :categories="store.categories"
          :products="productStore.products"
          @save="onSave"
          @remove="onRemove"
          @clear="onClear"
        />
      </div>
    </div>

    <ConfirmDialog
      :open="confirmDeleteOpen"
      :message="`Удалить рецепт «${selectedRecipe?.name ?? ''}»?`"
      danger
      @confirm="onConfirmDelete"
      @cancel="confirmDeleteOpen = false"
    />
  </div>
</template>
