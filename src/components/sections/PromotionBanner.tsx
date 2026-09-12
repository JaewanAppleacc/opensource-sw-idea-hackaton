import { ChevronLeft, ChevronRight, Pause, Play } from 'lucide-react'
import { Container } from '../ui/Container'
import { useCarousel } from '../../hooks/useCarousel'
import { promotionSlides } from '../../data/content'
import type { GuideTint } from '../../types'

const tintGradients: Record<GuideTint, string> = {
  lavender: 'from-tint-lavender via-white to-tint-sky',
  mint: 'from-tint-mint via-white to-tint-lavender',
  sky: 'from-tint-sky via-white to-tint-mint',
}

export function PromotionBanner() {
  const { page, goTo, next, prev, isPlaying, togglePlaying } = useCarousel({
    pageCount: promotionSlides.length,
    autoplay: true,
    intervalMs: 5000,
  })
  const slide = promotionSlides[page]!

  return (
    <section aria-label="프로모션 배너" className="mt-14">
      <Container>
        <div
          className={`relative overflow-hidden rounded-card border border-ink-border bg-gradient-to-r p-8 sm:p-12 ${tintGradients[slide.tint]}`}
        >
          <a href={slide.href} className="block max-w-xl">
            <p className="text-sm font-bold text-brand-blue">{slide.eyebrow}</p>
            <p className="mt-2 text-xl font-bold text-ink-900 sm:text-2xl">{slide.title}</p>
            <p className="mt-2 text-sm text-ink-500 sm:text-base">{slide.subtitle}</p>
          </a>

          <div className="mt-8 flex items-center gap-2 sm:absolute sm:bottom-6 sm:right-8 sm:mt-0">
            <button
              type="button"
              onClick={prev}
              aria-label="이전 프로모션"
              className="flex h-8 w-8 items-center justify-center rounded-full bg-white/70 text-ink-700 transition hover:bg-white active:scale-95"
            >
              <ChevronLeft size={16} aria-hidden="true" />
            </button>
            <button
              type="button"
              onClick={togglePlaying}
              aria-pressed={isPlaying}
              aria-label={isPlaying ? '프로모션 자동재생 정지' : '프로모션 자동재생 시작'}
              className="flex h-8 w-8 items-center justify-center rounded-full bg-white/70 text-ink-700 transition hover:bg-white active:scale-95"
            >
              {isPlaying ? <Pause size={14} aria-hidden="true" /> : <Play size={14} aria-hidden="true" />}
            </button>
            <span className="min-w-[3.5rem] rounded-full bg-white/70 px-3 py-1.5 text-center text-xs font-semibold text-ink-700" aria-live="polite">
              {page + 1} / {promotionSlides.length}
            </span>
            <button
              type="button"
              onClick={next}
              aria-label="다음 프로모션"
              className="flex h-8 w-8 items-center justify-center rounded-full bg-white/70 text-ink-700 transition hover:bg-white active:scale-95"
            >
              <ChevronRight size={16} aria-hidden="true" />
            </button>
          </div>

          <div className="mt-6 flex gap-1.5 sm:hidden">
            {promotionSlides.map((s, i) => (
              <button
                key={s.id}
                type="button"
                aria-label={`${i + 1}번째 배너로 이동`}
                aria-current={i === page}
                onClick={() => goTo(i)}
                className={`h-1.5 flex-1 rounded-full transition ${i === page ? 'bg-brand-blue' : 'bg-white/70'}`}
              />
            ))}
          </div>
        </div>
      </Container>
    </section>
  )
}
