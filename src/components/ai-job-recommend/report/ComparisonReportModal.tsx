import { ChevronLeft, ChevronRight, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import type { MatchCandidate, PostingListItem } from '../../../lib/apiClient'
import type { AxisId, AxisResult } from '../../../lib/comparisonAxes'
import type { PriorityItem } from '../../../lib/priorityUnresolved'
import { ReportConditionsStep } from './ReportConditionsStep'
import { ReportFinanceStep } from './ReportFinanceStep'
import { ReportProgress } from './ReportProgress'
import { ReportQuestionsStep } from './ReportQuestionsStep'
import { ReportSummaryStep } from './ReportSummaryStep'
import { ReportTargetStep } from './ReportTargetStep'
import { ReportUnknownsStep } from './ReportUnknownsStep'

export type ReportStep = 'targets' | 'conditions' | 'unknowns' | 'questions' | 'finance' | 'summary'

const STEP_ORDER: ReportStep[] = ['targets', 'conditions', 'unknowns', 'questions', 'finance', 'summary']

const STEP_COPY: Record<ReportStep, { title: string; description: string }> = {
  targets: {
    title: '두 공고를 같은 기준으로 살펴봤어요',
    description: '모집직종·고용형태·근무지역이 같은 그룹의 공고만 비교합니다.',
  },
  conditions: {
    title: '지원 판단에 필요한 조건을 비교했어요',
    description: '항목을 눌러 원문 근거를 펼쳐볼 수 있어요.',
  },
  unknowns: {
    title: '결정 전에 이 정보는 꼭 확인하세요',
    description: '내가 중요하게 선택한 조건 위주로, 확인이 필요한 항목만 모았어요.',
  },
  questions: {
    title: '담당자에게 그대로 물어보세요',
    description: '공고에서 확인되지 않은 조건을 질문으로 정리했습니다.',
  },
  finance: {
    title: '지역 선택에 따른 자금 흐름도 확인해보세요',
    description: '직접 입력한 금액으로만 계산하며, 승자는 표시하지 않습니다.',
  },
  summary: {
    title: '이제 무엇을 확인할지 정리됐어요',
    description: '지금까지 확인한 내용을 한눈에 정리했습니다.',
  },
}

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

interface ComparisonReportModalProps {
  open: boolean
  onClose: () => void
  onRequestAnotherCandidate: () => void
  metroPosting: PostingListItem
  jeonbukCandidate: MatchCandidate
  metroLabel: string
  jeonbukLabel: string
  metroAxes: AxisResult[]
  jeonbukAxes: AxisResult[]
  priorityItems: PriorityItem[]
  statusCounts: { confirmed: number; vague: number; absent: number }
  selectedAxisIds: AxisId[]
  onSelectedAxisIdsChange: (ids: AxisId[]) => void
  financeCompleted: boolean
  onFinanceComputed: () => void
}

/**
 * Accessible, step-by-step comparison report dialog (TASK "단계형 리포트
 * 모달"). Opens over the current page (no new tab, no window.open) once the
 * caller's metro+jeonbuk analyses have both already succeeded -- this
 * component never fetches or computes anything itself, it only presents
 * data the caller already has.
 */
export function ComparisonReportModal({
  open,
  onClose,
  onRequestAnotherCandidate,
  metroPosting,
  jeonbukCandidate,
  metroLabel,
  jeonbukLabel,
  metroAxes,
  jeonbukAxes,
  priorityItems,
  statusCounts,
  selectedAxisIds,
  onSelectedAxisIdsChange,
  financeCompleted,
  onFinanceComputed,
}: ComparisonReportModalProps) {
  const [shouldRender, setShouldRender] = useState(open)
  const [stepIndex, setStepIndex] = useState(0)
  const dialogRef = useRef<HTMLDivElement | null>(null)
  const titleRef = useRef<HTMLHeadingElement | null>(null)
  const openerElementRef = useRef<Element | null>(null)

  // Mount immediately on open; keep mounted briefly after `open` goes false
  // so the CSS fade/scale-out transition (160-220ms) can actually play.
  useEffect(() => {
    if (open) {
      setShouldRender(true)
      setStepIndex(0)
      openerElementRef.current = document.activeElement
    } else if (shouldRender) {
      const timer = window.setTimeout(() => setShouldRender(false), 220)
      return () => window.clearTimeout(timer)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  // Focus the title on open (첫 번째 의미 있는 요소), body scroll lock while
  // mounted, and focus restore to whatever had focus before the dialog
  // opened (typically the 전북 후보 버튼 the user just clicked).
  useEffect(() => {
    if (!open) return
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const focusTimer = window.setTimeout(() => titleRef.current?.focus(), 0)
    return () => {
      document.body.style.overflow = previousOverflow
      window.clearTimeout(focusTimer)
      const opener = openerElementRef.current
      if (opener instanceof HTMLElement) opener.focus()
    }
  }, [open])

  // Document-level Escape handler -- independent of the focus-trap keydown
  // handler below, so Escape still closes the dialog even if focus is not
  // (or is no longer) inside it for any reason.
  useEffect(() => {
    if (!open) return
    function handleDocumentKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleDocumentKeyDown)
    return () => document.removeEventListener('keydown', handleDocumentKeyDown)
  }, [open, onClose])

  const step = STEP_ORDER[stepIndex]
  const copy = STEP_COPY[step]

  const confirmedCount = statusCounts.confirmed
  const questionCount = useMemo(() => {
    const seen = new Set<string>()
    for (const item of priorityItems) {
      if (!item.action) continue
      seen.add(`${item.region}:${item.action.prompt}`)
      if (seen.size === 3) break
    }
    return seen.size
  }, [priorityItems])

  function goNext() {
    setStepIndex((i) => Math.min(i + 1, STEP_ORDER.length - 1))
  }
  function goPrev() {
    setStepIndex((i) => Math.max(i - 1, 0))
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape') {
      event.stopPropagation()
      onClose()
      return
    }
    if (event.key !== 'Tab') return
    const container = dialogRef.current
    if (!container) return
    const focusables = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(
      (el) => el.offsetParent !== null,
    )
    if (focusables.length === 0) return
    const first = focusables[0]
    const last = focusables[focusables.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  if (!shouldRender) return null

  // Portaled straight to <body> -- position:fixed only escapes to the
  // viewport when no ancestor establishes its own containing block (a
  // transform, filter, will-change, etc.), and several ancestors on this
  // page do (e.g. the `panel-update-in` entrance animation leaves a
  // non-`none` transform in its held end state). Rendering in the normal
  // tree would silently confine the overlay/dialog to whatever ancestor box
  // happens to do that, instead of covering the full viewport.
  return createPortal(
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm transition-opacity duration-200 ${
        open ? 'opacity-100' : 'opacity-0'
      }`}
      onClick={onClose}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="comparison-report-title"
        aria-describedby="comparison-report-description"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
        className={`report-print-area flex h-full w-full flex-col bg-white transition-all duration-200 sm:h-[720px] sm:max-h-[85vh] sm:w-full sm:max-w-[960px] sm:rounded-[28px] sm:shadow-softer ${
          open ? 'translate-y-0 scale-100 opacity-100' : 'translate-y-2 scale-[0.98] opacity-0'
        }`}
      >
        <div className="report-print-hide flex items-center justify-end px-4 pt-4 sm:px-6">
          <button
            type="button"
            onClick={onClose}
            aria-label="리포트 닫기"
            className="flex h-9 w-9 items-center justify-center rounded-full text-ink-400 transition-colors duration-150 hover:bg-surface-muted hover:text-ink-700"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto bg-surface-muted px-4 py-4 sm:px-6">
          <div key={step} className="report-step-in">
            {step === 'targets' && (
              <ReportTargetStep
                metroPosting={metroPosting}
                jeonbukCandidate={jeonbukCandidate}
                metroLabel={metroLabel}
                jeonbukLabel={jeonbukLabel}
              />
            )}
            {step === 'conditions' && (
              <ReportConditionsStep
                metroLabel={metroLabel}
                jeonbukLabel={jeonbukLabel}
                metroAxes={metroAxes}
                jeonbukAxes={jeonbukAxes}
                selectedAxisIds={selectedAxisIds}
                onSelectedAxisIdsChange={onSelectedAxisIdsChange}
              />
            )}
            {step === 'unknowns' && (
              <ReportUnknownsStep items={priorityItems} metroLabel={metroLabel} jeonbukLabel={jeonbukLabel} />
            )}
            {step === 'questions' && (
              <ReportQuestionsStep items={priorityItems} metroLabel={metroLabel} jeonbukLabel={jeonbukLabel} />
            )}
            {step === 'finance' && <ReportFinanceStep onComputed={onFinanceComputed} />}
            {step === 'summary' && (
              <ReportSummaryStep
                metroPosting={metroPosting}
                jeonbukCandidate={jeonbukCandidate}
                selectedAxisIds={selectedAxisIds}
                confirmedCount={confirmedCount}
                questionCount={questionCount}
                financeCompleted={financeCompleted}
                onClose={onClose}
                onRequestAnotherCandidate={onRequestAnotherCandidate}
              />
            )}
          </div>
        </div>

        <div className="report-print-hide border-t border-ink-border bg-white px-4 py-3 sm:px-6 sm:py-4">
          <h2 id="comparison-report-title" ref={titleRef} tabIndex={-1} className="text-base font-bold text-ink-900 outline-none">
            {copy.title}
          </h2>
          <p id="comparison-report-description" className="mt-0.5 text-xs text-ink-500">
            {copy.description}
          </p>
          <div className="mt-3 flex items-center justify-between gap-3">
            <ReportProgress stepIndex={stepIndex} stepCount={STEP_ORDER.length} stepTitle={copy.title} />
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={goPrev}
                disabled={stepIndex === 0}
                className="flex items-center gap-1 rounded-pill border border-ink-border bg-white px-3 py-1.5 text-sm font-semibold text-ink-700 transition-colors duration-150 hover:border-brand-blue hover:text-brand-blue disabled:cursor-not-allowed disabled:opacity-40"
              >
                <ChevronLeft size={14} aria-hidden="true" />
                이전
              </button>
              {step !== 'summary' && (
                <button
                  type="button"
                  onClick={goNext}
                  className="flex items-center gap-1 rounded-pill bg-brand-blue px-4 py-1.5 text-sm font-semibold text-white transition-colors duration-150 hover:bg-brand-blue-dark"
                >
                  다음
                  <ChevronRight size={14} aria-hidden="true" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}
