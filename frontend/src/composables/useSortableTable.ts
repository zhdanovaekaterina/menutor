import { ref } from 'vue'

export function useSortableTable<K extends string>(initialKey: K) {
  const sortKey = ref<K>(initialKey) as import('vue').Ref<K>
  const sortAsc = ref(true)

  function toggleSort(key: K) {
    if (sortKey.value === key) sortAsc.value = !sortAsc.value
    else { sortKey.value = key; sortAsc.value = true }
  }

  function sortIcon(key: K): string {
    if (sortKey.value !== key) return '\u2195'
    return sortAsc.value ? '\u2191' : '\u2193'
  }

  return { sortKey, sortAsc, toggleSort, sortIcon }
}
