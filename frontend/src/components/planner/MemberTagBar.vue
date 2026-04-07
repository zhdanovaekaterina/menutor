<script setup lang="ts">
import MemberTag from './MemberTag.vue'
import type { FamilyMember } from '@/api/types'

defineProps<{
  members: FamilyMember[]
  activeMemberIds: Set<number>
  allActive: boolean
  activePortionsLabel: string
}>()

defineEmits<{
  'toggle-member': [id: number]
  'toggle-all': []
}>()
</script>

<template>
  <div
    v-if="members.length > 0"
    role="toolbar"
    aria-label="Фильтр по членам семьи"
    class="flex items-center gap-2 overflow-x-auto scrollbar-none snap-x snap-mandatory px-0 py-1"
  >
    <MemberTag
      label="Все"
      :active="allActive"
      :special="true"
      :title="allActive ? 'Показать только общие' : 'Включить всех участников'"
      class="snap-start"
      @toggle="$emit('toggle-all')"
    />
    <div class="w-px h-5 bg-gray-300 shrink-0" />
    <MemberTag
      v-for="member in members"
      :key="member.id"
      :label="`${member.name} ×${member.portion_multiplier}`"
      :active="activeMemberIds.has(member.id)"
      :title="activeMemberIds.has(member.id) ? `Нажмите, чтобы исключить ${member.name}` : `Нажмите, чтобы включить ${member.name}`"
      class="snap-start"
      @toggle="$emit('toggle-member', member.id)"
    />
    <slot />
    <span class="ml-auto text-xs text-gray-500 whitespace-nowrap shrink-0">
      {{ activePortionsLabel }}
    </span>
    <!-- Screen reader live region -->
    <div class="sr-only" aria-live="polite" aria-atomic="true">{{ activePortionsLabel }}</div>
  </div>
</template>

<style scoped>
.scrollbar-none::-webkit-scrollbar { display: none; }
.scrollbar-none { -ms-overflow-style: none; scrollbar-width: none; }
</style>
