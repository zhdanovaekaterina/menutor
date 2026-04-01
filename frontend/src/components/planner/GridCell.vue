<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import Sortable from 'sortablejs'
import type { CellItem, FamilyMember, MenuSlot, MergedSlotView } from '@/api/types'
import { isMergedSlot } from '@/api/types'
import { useContextMenu } from '@/composables/useContextMenu'
import { usePlannerClipboard } from '@/composables/usePlannerClipboard'
import { useMenuStore } from '@/stores/menus'
import { useProductStore } from '@/stores/products'
import { useRecipeStore } from '@/stores/recipes'
import { useCategoryStore } from '@/stores/categories'
import { formatUnit } from '@/utils/units'
import { isSlotVisible, getMemberInitials } from '@/utils/slotVisibility'
import ItemRow from './ItemRow.vue'
import MergedSlotDialog from '@/components/ui/MergedSlotDialog.vue'
import IconPlus from '@/components/ui/icons/IconPlus.vue'

const props = defineProps<{
  day: number
  mealType: string
  slots: MenuSlot[]
  recipeNames: Record<number, string>
  productNames: Record<number, string>
  pickerActive?: boolean
  size?: 'medium' | 'full'
  activeMemberIds?: Set<number>
  allActive?: boolean
  familyMembers?: FamilyMember[]
}>()

const emit = defineEmits<{
  addItem: [data: { type: 'recipe' | 'product'; id: number }]
  removeItem: [data: { recipe_id?: number | null; product_id?: number | null; position?: number | null }]
  editItem: [slot: MenuSlot]
  moveItem: [slot: MenuSlot, toDay: number, toMealType: string, toIndex: number]
  reorderItems: [day: number, mealType: string, orderedSlots: MenuSlot[]]
  openPicker: []
}>()

// Merged slot dialog state
const mergedDialogSlot = ref<MergedSlotView | null>(null)
const showMergedDialog = ref(false)

function openMergedDialog(merged: MergedSlotView) {
  mergedDialogSlot.value = merged
  showMergedDialog.value = true
}

function onMergedEditSlot(slot: MenuSlot) {
  showMergedDialog.value = false
  emit('editItem', slot)
}

function onMergedRemoveSlot(slot: MenuSlot) {
  showMergedDialog.value = false
  emit('removeItem', { recipe_id: slot.recipe_id, product_id: slot.product_id, position: slot.position ?? null })
}

function mergeSameRecipeSlots(slots: MenuSlot[]): CellItem[] {
  const groups = new Map<number, MenuSlot[]>()
  const result: CellItem[] = []
  for (const slot of slots) {
    if (!slot.recipe_id || !slot.member_ids?.length) {
      result.push(slot)
      continue
    }
    const existing = groups.get(slot.recipe_id)
    if (existing) existing.push(slot)
    else groups.set(slot.recipe_id, [slot])
  }
  for (const [recipeId, group] of groups) {
    if (group.length === 1) {
      result.push(group[0]!)
    } else {
      result.push({
        _merged: true,
        recipe_id: recipeId,
        slots: group,
        totalServings: group.reduce((sum, s) => sum + (s.servings_override ?? 0), 0),
        allMemberIds: [...new Set(group.flatMap(s => s.member_ids ?? []))],
      } as MergedSlotView)
    }
  }
  return result
}

const dragOver = ref(false)
const listRef = ref<HTMLElement>()

const recipeStore = useRecipeStore()
const productStore = useProductStore()
const categoryStore = useCategoryStore()

function categoryColor(item: CellItem): string | null {
  const recipeId = isMergedSlot(item) ? item.recipe_id : item.recipe_id
  const productId = isMergedSlot(item) ? null : item.product_id
  if (recipeId != null) {
    const recipe = recipeStore.items.find((r) => r.id === recipeId)
    if (!recipe) return null
    return categoryStore.findById('recipe', recipe.category_id)?.color ?? null
  }
  if (productId != null) {
    const product = productStore.items.find((p) => p.id === productId)
    if (!product) return null
    return categoryStore.findById('product', product.category_id)?.color ?? null
  }
  return null
}

// Context menu
const { open: openContextMenu, close: closeContextMenu } = useContextMenu()
const { hasClipboard, copySlot, pasteSlot } = usePlannerClipboard()
const menuStore = useMenuStore()

function buildContextMenuItems() {
  return [
    {
      label: 'Копировать',
      action: () => {
        copySlot(cellSlots.value)
        closeContextMenu()
      },
    },
    {
      label: 'Вставить',
      disabled: !hasClipboard.value,
      action: async () => {
        const items = pasteSlot()
        if (!items || items.length === 0) return
        await menuStore.ensureMenuSelected()
        await menuStore.mergeItemsIntoSlot(props.day, props.mealType, items)
        closeContextMenu()
      },
    },
  ]
}

function onContextMenu(e: MouseEvent) {
  openContextMenu(e.clientX, e.clientY, buildContextMenuItems())
}

// Long-press for mobile context menu
let longPressTimer: ReturnType<typeof setTimeout> | null = null
let touchMoved = false

function onTouchStart(e: TouchEvent) {
  touchMoved = false
  const touch = e.touches[0]
  if (!touch) return
  longPressTimer = setTimeout(() => {
    if (!touchMoved) {
      openContextMenu(touch.clientX, touch.clientY, buildContextMenuItems())
    }
  }, 500)
}

function onTouchMove() {
  touchMoved = true
  if (longPressTimer !== null) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
}

function onTouchEnd() {
  if (longPressTimer !== null) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
}

let sortable: Sortable | null = null

const rawCellSlots = computed(() =>
  props.slots
    .filter((s) => s.day === props.day && s.meal_type === props.mealType)
    .sort((a, b) => (a.position ?? 0) - (b.position ?? 0)),
)

const cellSlots = computed((): CellItem[] => {
  const activeIds = props.activeMemberIds
  if (!activeIds || activeIds.size === 0) {
    // No filter active — show all but still merge grouped slots
    return mergeSameRecipeSlots(rawCellSlots.value)
  }
  const visible = rawCellSlots.value.filter(s => isSlotVisible(s, activeIds))
  return mergeSameRecipeSlots(visible)
})

function itemName(item: CellItem) {
  if (isMergedSlot(item)) return props.recipeNames[item.recipe_id] ?? `#${item.recipe_id}`
  if (item.recipe_id != null) return props.recipeNames[item.recipe_id] ?? `#${item.recipe_id}`
  if (item.product_id != null) return props.productNames[item.product_id] ?? `#${item.product_id}`
  return '?'
}

function formatNumber(n: number): string {
  return n % 1 === 0 ? String(n) : n.toFixed(1)
}

function itemDetail(item: CellItem) {
  if (isMergedSlot(item)) {
    return { text: `${formatNumber(item.totalServings)} п.`, piecesDetail: null }
  }
  if (item.recipe_id != null) {
    const s = item.servings_override ?? item.quantity
    const recipe = recipeStore.items.find(r => r.id === item.recipe_id)

    if (recipe?.total_pieces != null && recipe?.pieces_per_portion != null) {
      const portions = s != null ? formatNumber(s) : '?'
      const pcs = item.pieces_override
        ?? Math.max(1, Math.round((s ?? 1) * recipe.pieces_per_portion))
      return { text: '', piecesDetail: { portions, pieces: pcs } }
    }

    return { text: s != null ? `${formatNumber(s)} п.` : '', piecesDetail: null }
  }
  if (item.product_id != null && item.quantity != null) {
    return { text: `${item.quantity} ${formatUnit(item.unit ?? '')}`, piecesDetail: null }
  }
  return { text: '', piecesDetail: null }
}

function itemMemberInitials(item: CellItem): string[] {
  const members = props.familyMembers ?? []
  if (isMergedSlot(item)) return getMemberInitials(item.allMemberIds, members)
  return getMemberInitials(item.member_ids ?? [], members)
}

/* Native drop from SourcePanel (not SortableJS) */
function onDragOver(e: DragEvent) {
  if (e.dataTransfer?.types.includes('application/json')) {
    e.preventDefault()
    dragOver.value = true
  }
}

function onDrop(e: DragEvent) {
  dragOver.value = false
  const raw = e.dataTransfer?.getData('application/json')
  if (!raw) return
  e.preventDefault()
  try {
    const data = JSON.parse(raw)
    if (data.type && data.id) {
      emit('addItem', data as { type: 'recipe' | 'product'; id: number })
    }
  } catch { /* ignore */ }
}

function initSortable() {
  if (!listRef.value) return
  sortable = Sortable.create(listRef.value, {
    group: 'menu-slots',
    animation: 150,
    ghostClass: 'sortable-ghost',
    dragClass: 'sortable-drag',
    onEnd(evt) {
      const fromDay = Number(evt.from.dataset.day)
      const fromMeal = evt.from.dataset.mealType!
      const toDay = Number(evt.to.dataset.day)
      const toMeal = evt.to.dataset.mealType!
      const oldIdx = evt.oldIndex!
      const newIdx = evt.newIndex!

      /* Undo SortableJS DOM changes — let Vue re-render */
      if (evt.from !== evt.to) {
        evt.to.removeChild(evt.item)
        const ref = evt.from.children[oldIdx]
        if (ref) evt.from.insertBefore(evt.item, ref)
        else evt.from.appendChild(evt.item)
      } else if (oldIdx !== newIdx) {
        evt.from.removeChild(evt.item)
        const ref = evt.from.children[oldIdx]
        if (ref) evt.from.insertBefore(evt.item, ref)
        else evt.from.appendChild(evt.item)
      }

      /* Resolve source slot from the index within that cell */
      const sourceSlots = props.slots
        .filter((s) => s.day === fromDay && s.meal_type === fromMeal)
        .sort((a, b) => (a.position ?? 0) - (b.position ?? 0))
      const movedSlot = sourceSlots[oldIdx]
      if (!movedSlot) return

      if (fromDay !== toDay || fromMeal !== toMeal) {
        emit('moveItem', movedSlot, toDay, toMeal, newIdx)
      } else if (oldIdx !== newIdx) {
        const reordered = [...sourceSlots]
        reordered.splice(oldIdx, 1)
        reordered.splice(newIdx, 0, movedSlot)
        emit('reorderItems', fromDay, fromMeal, reordered)
      }
    },
  })
}

onMounted(initSortable)
onUnmounted(() => sortable?.destroy())

watch(
  () => rawCellSlots.value.length,
  () => {
    sortable?.destroy()
    initSortable()
  },
)
</script>

<template>
  <div
    :class="[
      dragOver ? 'ring-2 ring-blue-300 bg-blue-50/50' : '',
      pickerActive ? 'ring-2 ring-blue-400 ring-offset-1 bg-blue-50/60' : '',
      !dragOver && !pickerActive ? 'bg-white' : ''
    ]"
    class="relative h-full min-h-[100px] p-1 flex flex-col gap-1"
    @contextmenu.prevent="onContextMenu"
    @touchstart.passive="onTouchStart"
    @touchmove.passive="onTouchMove"
    @touchend.passive="onTouchEnd"
    @dragover="onDragOver"
    @dragleave="dragOver = false"
    @drop="onDrop"
  >
    <div ref="listRef" :data-day="day" :data-meal-type="mealType"
         class="flex flex-col gap-1 min-h-[8px] flex-1 overflow-y-auto"
         :class="props.size === 'full' ? '' : 'max-h-40'">
      <ItemRow
        v-for="(item, i) in cellSlots"
        :key="isMergedSlot(item)
          ? `merged-${item.recipe_id}`
          : `${item.recipe_id ?? ''}-${item.product_id ?? ''}-${item.position ?? i}`"
        :name="itemName(item)"
        :detail="itemDetail(item).text"
        :pieces-detail="itemDetail(item).piecesDetail"
        :variant="isMergedSlot(item) ? 'recipe' : (item.recipe_id != null ? 'recipe' : 'product')"
        :category-color="categoryColor(item)"
        :member-initials="itemMemberInitials(item)"
        :is-merged="isMergedSlot(item)"
        @remove="isMergedSlot(item)
          ? openMergedDialog(item)
          : emit('removeItem', { recipe_id: item.recipe_id, product_id: item.product_id, position: item.position ?? null })"
        @click="isMergedSlot(item)
          ? openMergedDialog(item)
          : emit('editItem', item)"
      />
    </div>
    <!-- Mobile add button -->
    <button
      class="lg:hidden absolute bottom-1.5 right-1.5 flex items-center justify-center rounded-full bg-blue-500 text-white shadow-md active:bg-blue-600 transition-colors"
      :class="props.size === 'full' ? 'w-12 h-12' : 'w-9 h-9'"
      aria-label="Добавить"
      @click.stop="emit('openPicker')"
    >
      <IconPlus :class="props.size === 'full' ? 'w-6 h-6' : 'w-5 h-5'" />
    </button>
  </div>

  <MergedSlotDialog
    v-if="showMergedDialog && mergedDialogSlot"
    :recipe-name="mergedDialogSlot ? (recipeNames[mergedDialogSlot.recipe_id] ?? '') : ''"
    :total-servings="mergedDialogSlot?.totalServings ?? 0"
    :slots="mergedDialogSlot?.slots ?? []"
    :family-members="familyMembers ?? []"
    @close="showMergedDialog = false"
    @edit-slot="onMergedEditSlot"
    @remove-slot="onMergedRemoveSlot"
  />
</template>

<style scoped>
.sortable-ghost {
  opacity: 0.4;
}
</style>
