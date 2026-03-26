export interface PresetColor {
  hex: string
  name: string
}

/** 16 preset colors, 2 rows of 8, per WCAG AA contrast requirements */
export const PRESET_COLORS: PresetColor[] = [
  // Row 1
  { hex: '#DC2626', name: 'Красный' },
  { hex: '#EA580C', name: 'Оранжевый' },
  { hex: '#D97706', name: 'Янтарный' },
  { hex: '#CA8A04', name: 'Золотой' },
  { hex: '#65A30D', name: 'Лаймовый' },
  { hex: '#16A34A', name: 'Зеленый' },
  { hex: '#059669', name: 'Изумрудный' },
  { hex: '#0D9488', name: 'Бирюзовый' },
  // Row 2
  { hex: '#0891B2', name: 'Голубой' },
  { hex: '#2563EB', name: 'Синий' },
  { hex: '#4F46E5', name: 'Индиго' },
  { hex: '#7C3AED', name: 'Фиолетовый' },
  { hex: '#9333EA', name: 'Пурпурный' },
  { hex: '#DB2777', name: 'Розовый' },
  { hex: '#57534E', name: 'Каменный' },
  { hex: '#475569', name: 'Сланцевый' },
]

/** Default fallback colors when category has no color assigned */
export const FALLBACK_RECIPE_COLOR = '#3B82F6'  // blue-500 (primary)
export const FALLBACK_PRODUCT_COLOR = '#10B981'  // emerald-500 (accent)
