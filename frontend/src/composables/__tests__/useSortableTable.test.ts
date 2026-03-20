import { describe, expect, it } from 'vitest'
import { useSortableTable } from '../useSortableTable'

describe('useSortableTable', () => {
  it('initializes with given key and ascending order', () => {
    const { sortKey, sortAsc } = useSortableTable('name')
    expect(sortKey.value).toBe('name')
    expect(sortAsc.value).toBe(true)
  })

  it('toggleSort on same key flips direction', () => {
    const { sortAsc, toggleSort } = useSortableTable('name')
    toggleSort('name')
    expect(sortAsc.value).toBe(false)
    toggleSort('name')
    expect(sortAsc.value).toBe(true)
  })

  it('toggleSort on different key changes key and resets to ascending', () => {
    const { sortKey, sortAsc, toggleSort } = useSortableTable<'name' | 'price'>('name')
    toggleSort('name') // now desc
    toggleSort('price')
    expect(sortKey.value).toBe('price')
    expect(sortAsc.value).toBe(true)
  })

  it('sortIcon returns correct symbols', () => {
    const { sortIcon, toggleSort } = useSortableTable<'a' | 'b'>('a')
    expect(sortIcon('a')).toBe('\u2191') // current key, ascending
    expect(sortIcon('b')).toBe('\u2195') // not current key
    toggleSort('a')
    expect(sortIcon('a')).toBe('\u2193') // current key, descending
  })
})
