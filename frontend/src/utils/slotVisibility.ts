import type { MenuSlot } from '@/api/types'

export function isSlotVisible(slot: MenuSlot, activeIds: Set<number>): boolean {
  if (!slot.member_ids?.length) return true
  return slot.member_ids.some(id => activeIds.has(id))
}

export function getMemberInitials(
  memberIds: number[],
  familyMembers: { id: number; name: string }[]
): string[] {
  if (!memberIds.length) return []
  const initials = memberIds.map(id => {
    const member = familyMembers.find(m => m.id === id)
    return member ? member.name.charAt(0).toUpperCase() : '?'
  })
  // Handle duplicate initials: use 2 chars
  const seen = new Map<string, number>()
  return initials.map((ini, idx) => {
    const count = (seen.get(ini) ?? 0) + 1
    seen.set(ini, count)
    if (initials.filter(i => i === ini).length > 1) {
      const member = familyMembers.find(m => m.id === memberIds[idx])
      return member ? member.name.substring(0, 2) : ini
    }
    return ini
  })
}
