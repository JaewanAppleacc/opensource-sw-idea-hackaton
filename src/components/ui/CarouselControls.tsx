import { ChevronLeft, ChevronRight, Pause, Play } from 'lucide-react'

interface CarouselControlsProps {
  page: number
  pageCount: number
  onPrev: () => void
  onNext: () => void
  onGoTo: (index: number) => void
  isPlaying?: boolean
  onTogglePlaying?: () => void
  label: string
  className?: string
}

export function CarouselControls({
  page,
  pageCount,
  onPrev,
  onNext,
  onGoTo,
  isPlaying,
  onTogglePlaying,
  label,
  className = '',
}: CarouselControlsProps) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <button
        type="button"
        onClick={onPrev}
        aria-label={`${label} 이전`}
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-ink-border bg-white text-ink-700 transition hover:border-brand-blue hover:text-brand-blue active:scale-95"
      >
        <ChevronLeft size={18} aria-hidden="true" />
      </button>

      <div className="flex items-center gap-1.5" role="tablist" aria-label={`${label} 페이지`}>
        {Array.from({ length: pageCount }).map((_, i) => (
          <button
            key={i}
            type="button"
            role="tab"
            aria-selected={i === page}
            aria-label={`${label} ${i + 1}번째 페이지`}
            onClick={() => onGoTo(i)}
            className={`h-2 rounded-full transition-all active:scale-95 ${
              i === page ? 'w-6 bg-brand-blue' : 'w-2 bg-ink-border hover:bg-ink-400'
            }`}
          />
        ))}
      </div>

      <button
        type="button"
        onClick={onNext}
        aria-label={`${label} 다음`}
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-ink-border bg-white text-ink-700 transition hover:border-brand-blue hover:text-brand-blue active:scale-95"
      >
        <ChevronRight size={18} aria-hidden="true" />
      </button>

      {onTogglePlaying && (
        <button
          type="button"
          onClick={onTogglePlaying}
          aria-label={isPlaying ? `${label} 자동재생 정지` : `${label} 자동재생 시작`}
          aria-pressed={isPlaying}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-ink-border bg-white text-ink-700 transition hover:border-brand-blue hover:text-brand-blue active:scale-95"
        >
          {isPlaying ? <Pause size={16} aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}
        </button>
      )}
    </div>
  )
}
