import { Check } from 'lucide-react'

const STEPS = ['추천 공고', '지역 비교', '지원 전 확인'] as const

interface ServiceStepIndicatorProps {
  /** 1-3. Purely presentational progress marker, never a gate on what the
   * user can click. Rendered once at the page header (TASK "UI 고도화"
   * section 6 -- login/잡케어 folded into the profile summary rather than
   * their own step). */
  currentStep: 1 | 2 | 3
  className?: string
}

export function ServiceStepIndicator({ currentStep, className = '' }: ServiceStepIndicatorProps) {
  return (
    <ol
      className={`flex flex-wrap items-center gap-x-1 gap-y-1.5 text-[11px] ${className}`}
      data-testid="service-step-indicator"
    >
      {STEPS.map((label, i) => {
        const step = (i + 1) as 1 | 2 | 3
        const isDone = step < currentStep
        const isCurrent = step === currentStep
        return (
          <li key={label} className="flex items-center gap-1">
            <span
              className={`flex items-center gap-1 rounded-pill px-2 py-0.5 font-semibold transition-colors duration-200 ${
                isCurrent
                  ? 'bg-brand-blue text-white'
                  : isDone
                    ? 'bg-tint-mint/60 text-brand-green'
                    : 'bg-surface-muted text-ink-400'
              }`}
            >
              {isDone ? <Check size={10} aria-hidden="true" /> : <span>{step}</span>}
              {label}
            </span>
            {step < 3 && <span className="text-ink-300">→</span>}
          </li>
        )
      })}
    </ol>
  )
}
