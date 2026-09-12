import { useEffect } from 'react'
import type { RefObject } from 'react'

export function useOnClickOutside<T extends HTMLElement>(
  ref: RefObject<T | null>,
  handler: () => void,
  active: boolean,
) {
  useEffect(() => {
    if (!active) return

    function handlePointer(event: PointerEvent) {
      const el = ref.current
      if (!el || el.contains(event.target as Node)) return
      handler()
    }

    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') handler()
    }

    document.addEventListener('pointerdown', handlePointer)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('pointerdown', handlePointer)
      document.removeEventListener('keydown', handleKey)
    }
  }, [ref, handler, active])
}
