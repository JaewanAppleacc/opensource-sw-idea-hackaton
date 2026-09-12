import { useCallback, useEffect, useRef, useState } from 'react'
import { usePrefersReducedMotion } from './usePrefersReducedMotion'

interface UseCarouselOptions {
  pageCount: number
  autoplay?: boolean
  intervalMs?: number
}

interface UseCarouselResult {
  page: number
  goTo: (page: number) => void
  next: () => void
  prev: () => void
  isPlaying: boolean
  togglePlaying: () => void
}

export function useCarousel({ pageCount, autoplay = false, intervalMs = 5000 }: UseCarouselOptions): UseCarouselResult {
  const prefersReducedMotion = usePrefersReducedMotion()
  const [page, setPage] = useState(0)
  const [isPlaying, setIsPlaying] = useState(autoplay && !prefersReducedMotion)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const goTo = useCallback(
    (target: number) => {
      if (pageCount <= 0) return
      setPage(((target % pageCount) + pageCount) % pageCount)
    },
    [pageCount],
  )

  const next = useCallback(() => goTo(page + 1), [goTo, page])
  const prev = useCallback(() => goTo(page - 1), [goTo, page])
  const togglePlaying = useCallback(() => setIsPlaying((prev) => !prev), [])

  useEffect(() => {
    if (!isPlaying || prefersReducedMotion || pageCount <= 1) return
    timerRef.current = setInterval(() => {
      setPage((prev) => (prev + 1) % pageCount)
    }, intervalMs)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [isPlaying, prefersReducedMotion, pageCount, intervalMs])

  useEffect(() => {
    if (prefersReducedMotion) setIsPlaying(false)
  }, [prefersReducedMotion])

  return { page, goTo, next, prev, isPlaying, togglePlaying }
}
