import { ref, shallowRef, computed } from 'vue'

export function useSelection<Id extends number = number>() {
  const active = ref(false)
  const selected = shallowRef(new Set<Id>())

  const count = computed(() => selected.value.size)

  function toggle(id: Id) {
    const next = new Set(selected.value)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    selected.value = next
  }

  function has(id: Id) {
    return selected.value.has(id)
  }

  function clear() {
    selected.value = new Set()
  }

  function enter() {
    active.value = true
  }

  function exit() {
    active.value = false
    clear()
  }

  function toggleAll(ids: Id[]) {
    if (ids.length === selected.value.size && ids.every((id) => selected.value.has(id))) {
      clear()
    } else {
      selected.value = new Set(ids)
    }
  }

  function allSelected(ids: Id[]) {
    return ids.length > 0 && ids.every((id) => selected.value.has(id))
  }

  return { active, selected, count, toggle, has, clear, enter, exit, toggleAll, allSelected }
}
