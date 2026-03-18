import { describe, expect, it } from 'vitest'
import { useCategoryFilter } from '../useCategoryFilter'

interface TestItem {
  category_id: number
  name: string
}

const items: TestItem[] = [
  { category_id: 1, name: 'Apple' },
  { category_id: 2, name: 'Bread' },
  { category_id: 1, name: 'Avocado' },
  { category_id: 3, name: 'Milk' },
]

describe('useCategoryFilter', () => {
  it('returns all items when filter is null and no search query', () => {
    const { applyFilter } = useCategoryFilter<TestItem>()
    expect(applyFilter(items)).toHaveLength(4)
  })

  it('filters by category_id', () => {
    const { categoryFilter, applyFilter } = useCategoryFilter<TestItem>()
    categoryFilter.value = 1
    const result = applyFilter(items)
    expect(result).toHaveLength(2)
    expect(result.every((i) => i.category_id === 1)).toBe(true)
  })

  it('filters by search query (case-insensitive)', () => {
    const { applyFilter } = useCategoryFilter<TestItem>()
    const result = applyFilter(items, 'apple')
    expect(result).toHaveLength(1)
    expect(result[0]!.name).toBe('Apple')
  })

  it('combines category and search filters', () => {
    const { categoryFilter, applyFilter } = useCategoryFilter<TestItem>()
    categoryFilter.value = 1
    const result = applyFilter(items, 'av')
    expect(result).toHaveLength(1)
    expect(result[0]!.name).toBe('Avocado')
  })

  it('returns empty array when nothing matches', () => {
    const { categoryFilter, applyFilter } = useCategoryFilter<TestItem>()
    categoryFilter.value = 99
    expect(applyFilter(items)).toHaveLength(0)
  })

  it('reset() clears the category filter', () => {
    const { categoryFilter, reset } = useCategoryFilter<TestItem>()
    categoryFilter.value = 5
    reset()
    expect(categoryFilter.value).toBeNull()
  })
})
