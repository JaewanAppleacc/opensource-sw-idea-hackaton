interface ReportProgressProps {
  stepIndex: number
  stepCount: number
  stepTitle: string
}

/**
 * Decorative progress dots (bottom-left of the report modal, per the design
 * brief) plus a visually-hidden "N/6단계" announcement for screen readers.
 * Dots are not clickable -- step navigation only ever happens through the
 * 이전/다음 buttons, never by jumping to an arbitrary dot.
 */
export function ReportProgress({ stepIndex, stepCount, stepTitle }: ReportProgressProps) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="sr-only" aria-live="polite">
        {stepIndex + 1}/{stepCount}단계: {stepTitle}
      </span>
      <div aria-hidden="true" className="flex items-center gap-1.5">
        {Array.from({ length: stepCount }, (_, i) => (
          <span
            key={i}
            className={`h-1.5 rounded-pill transition-all duration-200 ${
              i === stepIndex ? 'w-5 bg-brand-blue' : 'w-1.5 bg-ink-border'
            }`}
          />
        ))}
      </div>
    </div>
  )
}
