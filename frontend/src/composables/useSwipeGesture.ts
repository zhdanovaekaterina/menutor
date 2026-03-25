import { ref } from 'vue'
import type { Ref } from 'vue'

interface SwipeGestureOptions {
  /** Minimum swipe distance in px (default: 50) */
  threshold?: number
  /** Maximum angle deviation from axis in degrees (default: 30) */
  maxAngle?: number
  /** Ignore touches starting within this many px from left edge (default: 20) */
  edgeGuard?: number
  /** 'horizontal' = only left/right; 'both' = all four directions */
  axis?: 'horizontal' | 'both'
  onSwipe: (direction: 'left' | 'right' | 'up' | 'down') => void
  onBounce?: (direction: 'left' | 'right' | 'up' | 'down') => void
}

interface SwipeGestureReturn {
  swipeHandlers: {
    onTouchstart: (e: TouchEvent) => void
    onTouchmove: (e: TouchEvent) => void
    onTouchend: (e: TouchEvent) => void
  }
  isSwiping: Ref<boolean>
}

export function useSwipeGesture(options: SwipeGestureOptions): SwipeGestureReturn {
  const threshold = options.threshold ?? 50
  const maxAngle = options.maxAngle ?? 30
  const edgeGuard = options.edgeGuard ?? 20
  const axis = options.axis ?? 'horizontal'

  const isSwiping = ref(false)

  let startX = 0
  let startY = 0
  let lastSwipeTime = 0
  const DEBOUNCE_MS = 300

  function onTouchstart(e: TouchEvent) {
    const touch = e.touches[0]
    if (touch.clientX < edgeGuard) return
    startX = touch.clientX
    startY = touch.clientY
    isSwiping.value = false
  }

  function onTouchmove(e: TouchEvent) {
    const touch = e.touches[0]
    const dx = touch.clientX - startX
    const dy = touch.clientY - startY
    if (Math.abs(dx) > 10 || Math.abs(dy) > 10) {
      isSwiping.value = true
    }
  }

  function onTouchend(e: TouchEvent) {
    const touch = e.changedTouches[0]
    const dx = touch.clientX - startX
    const dy = touch.clientY - startY
    const dist = Math.sqrt(dx * dx + dy * dy)

    isSwiping.value = false

    if (dist < threshold) return

    const angle = Math.atan2(Math.abs(dy), Math.abs(dx)) * (180 / Math.PI)

    const now = Date.now()
    if (now - lastSwipeTime < DEBOUNCE_MS) return

    if (axis === 'horizontal') {
      if (angle > maxAngle) return
      lastSwipeTime = now
      options.onSwipe(dx > 0 ? 'right' : 'left')
    } else {
      // 'both'
      if (angle < maxAngle) {
        // horizontal
        lastSwipeTime = now
        options.onSwipe(dx > 0 ? 'right' : 'left')
      } else if (angle > 90 - maxAngle) {
        // vertical
        lastSwipeTime = now
        options.onSwipe(dy > 0 ? 'down' : 'up')
      }
      // ambiguous zone: ignore
    }
  }

  return {
    swipeHandlers: { onTouchstart, onTouchmove, onTouchend },
    isSwiping,
  }
}
