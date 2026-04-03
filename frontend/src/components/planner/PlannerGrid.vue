<script setup lang="ts">
import type { FamilyMember, MenuSlot } from '@/api/types'
import GridCell from './GridCell.vue'
import MobileGridNavigator from './MobileGridNavigator.vue'

const props = defineProps<{
  slots: MenuSlot[]
  recipeNames: Record<number, string>
  productNames: Record<number, string>
  pickerDay?: number | null
  pickerMealTypeId?: number | null
  menuId?: number | null
  activeMemberIds?: Set<number>
  allActive?: boolean
  familyMembers?: FamilyMember[]
  mealTypes?: { id: number; name: string }[]
}>()

const emit = defineEmits<{
  addItem: [day: number, mealTypeId: number, data: { type: 'recipe' | 'product'; id: number }]
  removeItem: [day: number, mealTypeId: number, data: { recipe_id?: number | null; product_id?: number | null }]
  editItem: [slot: MenuSlot]
  moveItem: [slot: MenuSlot, toDay: number, toMealTypeId: number, toIndex: number]
  reorderItems: [day: number, mealTypeId: number, orderedSlots: MenuSlot[]]
  openPicker: [day: number, mealTypeId: number]
  dayScrolled: []
}>()

const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
</script>

<template>
  <!-- Mobile: three-mode navigation (hidden on lg+) -->
  <MobileGridNavigator
    class="lg:hidden h-full"
    :slots="slots"
    :recipe-names="recipeNames"
    :product-names="productNames"
    :picker-day="pickerDay"
    :picker-meal-type-id="pickerMealTypeId ?? null"
    :menu-id="menuId"
    :active-member-ids="activeMemberIds"
    :all-active="allActive"
    :family-members="familyMembers"
    :meal-types="props.mealTypes ?? []"
    @add-item="(d, m, data) => emit('addItem', d, m, data)"
    @remove-item="(d, m, data) => emit('removeItem', d, m, data)"
    @edit-item="(slot) => emit('editItem', slot)"
    @move-item="(slot, d, m, idx) => emit('moveItem', slot, d, m, idx)"
    @reorder-items="(d, m, ordered) => emit('reorderItems', d, m, ordered)"
    @open-picker="(d, m) => emit('openPicker', d, m)"
    @day-scrolled="emit('dayScrolled')"
  />

  <!-- Desktop: original CSS grid layout (hidden below lg) -->
  <div
    class="hidden lg:grid h-full min-w-[700px] grid-cols-[60px_repeat(7,1fr)] gap-px bg-gray-200 rounded-lg overflow-hidden text-sm"
    :style="{ gridTemplateRows: `auto repeat(${(props.mealTypes ?? []).length}, 1fr)` }"
  >
    <!-- Header row -->
    <div class="bg-gray-100" />
    <div
      v-for="d in days"
      :key="'hd-' + d"
      class="bg-gray-100 font-semibold text-center py-2"
    >
      {{ d }}
    </div>

    <!-- Meal rows -->
    <template v-for="mt in (props.mealTypes ?? [])" :key="'row-' + mt.id">
      <div class="bg-gray-100 font-semibold px-3 py-2 flex items-start">{{ mt.name }}</div>
      <GridCell
        v-for="day in 7"
        :key="'gc-' + day + '-' + mt.id"
        :day="day - 1"
        :meal-type-id="mt.id"
        :slots="slots"
        :recipe-names="recipeNames"
        :product-names="productNames"
        :picker-active="pickerDay === day - 1 && pickerMealTypeId === mt.id"
        :active-member-ids="activeMemberIds"
        :all-active="allActive"
        :family-members="familyMembers"
        @add-item="(data) => emit('addItem', day - 1, mt.id, data)"
        @remove-item="(data) => emit('removeItem', day - 1, mt.id, data)"
        @edit-item="(slot) => emit('editItem', slot)"
        @move-item="(slot, toDay, toMealTypeId, toIdx) => emit('moveItem', slot, toDay, toMealTypeId, toIdx)"
        @reorder-items="(d, m, ordered) => emit('reorderItems', d, m, ordered)"
      />
    </template>
  </div>
</template>
