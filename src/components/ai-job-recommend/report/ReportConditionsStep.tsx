import { AlertTriangle, ChevronDown, HelpCircle, Quote } from 'lucide-react'
import { useState } from 'react'
import type { FieldStatus } from '../../../lib/apiClient'
import {
  AXIS_ORDER,
  NOT_EVALUATED_LABEL,
  STRUCTURED_ABSENT_LABEL,
  type AxisId,
  type AxisResult,
  type AxisSubItemResult,
} from '../../../lib/comparisonAxes'
import { CHANNEL_LABELS, STATUS_LABELS } from '../../../lib/displayLabels'
import { ImportantConditionsSelector } from '../ImportantConditionsSelector'

const STATUS_STYLES: Record<FieldStatus, string> = {
  confirmed: 'bg-tint-mint/60 text-brand-green',
  vague: 'bg-amber-100 text-amber-700',
  absent: 'bg-surface-muted text-ink-500',
}
const NOT_EVALUATED_STYLE = 'border border-dashed border-ink-border bg-white text-ink-400'

/** One collapsible sub-item row -- status + one-line label always visible;
 * the original evidence quote and any verification question only render
 * once the user clicks to expand (TASK "단계형 리포트 모달" section 2: "각
 * 항목을 클릭했을 때만 원문 근거가 펼쳐지게").
 *
 * `item.sourceField === null` covers every sub-item with no backing
 * AuditedField -- not_evaluated, structured_absent, and the Work24
 * registry-confirmed 근로시간 case alike -- and renders `notEvaluatedMessage`
 * as plain display text instead of a quoted evidence span (TASK "Work24
 * Structured Data + sLLM Hybrid Audit Pipeline" section 6). A small source
 * label ("고용24 등록 정보" / "공고 본문 분석") is shown for every sub-item
 * that has one -- never developer terms like SLM/LLM/JSON (TASK section 7).
 */
function SubItemRow({ item }: { item: AxisSubItemResult }) {
  const [open, setOpen] = useState(false)
  const hasNoBackingField = item.sourceField === null
  const isNotEvaluated = item.displayStatus === 'not_evaluated'
  const isStructuredAbsent = item.displayStatus === 'structured_absent'
  return (
    <div className="border-t border-ink-border pt-2 first:border-t-0 first:pt-0">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-2 text-left"
      >
        <span className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs font-semibold text-ink-700">{item.subLabel}</span>
          {isNotEvaluated ? (
            <span className={`rounded-pill px-1.5 py-0.5 text-[10px] font-medium ${NOT_EVALUATED_STYLE}`}>
              {NOT_EVALUATED_LABEL}
            </span>
          ) : isStructuredAbsent ? (
            <span className={`rounded-pill px-1.5 py-0.5 text-[10px] font-medium ${NOT_EVALUATED_STYLE}`}>
              {STRUCTURED_ABSENT_LABEL}
            </span>
          ) : (
            item.displayStatus &&
            item.displayStatus !== 'not_evaluated' &&
            item.displayStatus !== 'structured_absent' && (
              <span className={`rounded-pill px-1.5 py-0.5 text-[10px] font-medium ${STATUS_STYLES[item.displayStatus]}`}>
                {STATUS_LABELS[item.displayStatus]}
              </span>
            )
          )}
          {item.sourceLabel && (
            <span className="rounded-pill bg-surface-muted px-1.5 py-0.5 text-[10px] text-ink-400">
              {item.sourceLabel}
            </span>
          )}
        </span>
        <ChevronDown
          size={13}
          aria-hidden="true"
          className={`shrink-0 text-ink-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>
      {open && (
        <div className="mt-1.5 pl-0.5">
          <p className="text-xs text-ink-700">
            {hasNoBackingField ? (
              <span className="text-ink-400">{item.notEvaluatedMessage}</span>
            ) : item.audited?.evidence ? (
              <span className="flex items-start gap-1 text-ink-700">
                <Quote size={11} aria-hidden="true" className="mt-0.5 shrink-0 text-ink-400" />
                <span>&ldquo;{item.audited.evidence.text}&rdquo;</span>
              </span>
            ) : (
              <span className="text-ink-400">근거 문구 없음</span>
            )}
          </p>
          {item.conflictMessage && (
            <p className="mt-1 flex items-start gap-1 rounded-card border border-amber-200 bg-amber-50 p-1.5 text-[11px] text-amber-800">
              <AlertTriangle size={11} aria-hidden="true" className="mt-0.5 shrink-0 text-amber-600" />
              <span>{item.conflictMessage}</span>
            </p>
          )}
          {item.action && (
            <p className="mt-1 flex items-start gap-1 rounded-card bg-surface-muted p-1.5 text-[11px] text-ink-500">
              <HelpCircle size={11} aria-hidden="true" className="mt-0.5 shrink-0 text-brand-blue" />
              <span>
                ({CHANNEL_LABELS[item.action.channel]}) {item.action.prompt}
              </span>
            </p>
          )}
        </div>
      )}
    </div>
  )
}

interface ReportConditionsStepProps {
  metroLabel: string
  jeonbukLabel: string
  metroAxes: AxisResult[]
  jeonbukAxes: AxisResult[]
  selectedAxisIds: AxisId[]
  onSelectedAxisIdsChange: (ids: AxisId[]) => void
}

/**
 * Report step 2/6 -- "지원 판단에 필요한 조건을 비교했어요". Reuses the same
 * six-axis data (`comparisonAxes.ts`) and the same important-conditions
 * control as the rest of the app; only the presentation differs (status +
 * one-line summary, evidence collapsed by default).
 */
export function ReportConditionsStep({
  metroLabel,
  jeonbukLabel,
  metroAxes,
  jeonbukAxes,
  selectedAxisIds,
  onSelectedAxisIdsChange,
}: ReportConditionsStepProps) {
  const metroById = new Map(metroAxes.map((a) => [a.id, a]))
  const jeonbukById = new Map(jeonbukAxes.map((a) => [a.id, a]))
  const orderedIds = [...selectedAxisIds, ...AXIS_ORDER.filter((id) => !selectedAxisIds.includes(id))]

  return (
    <div className="space-y-4">
      <details className="rounded-card border border-ink-border bg-white">
        <summary className="cursor-pointer list-none px-3 py-2.5 text-xs font-semibold text-brand-blue marker:content-none">
          중요하게 생각하는 조건 다시 선택하기
        </summary>
        <div className="border-t border-ink-border p-3">
          <ImportantConditionsSelector selected={selectedAxisIds} onChange={onSelectedAxisIdsChange} />
        </div>
      </details>

      <div className="space-y-3">
        {orderedIds.map((id) => {
          const metroAxis = metroById.get(id)
          const jeonbukAxis = jeonbukById.get(id)
          if (!metroAxis || !jeonbukAxis) return null
          const isSelected = selectedAxisIds.includes(id)
          return (
            <div
              key={id}
              className={`rounded-card border p-3 ${isSelected ? 'border-brand-blue bg-tint-sky/10' : 'border-ink-border bg-white'}`}
            >
              <p className="text-sm font-bold text-ink-900">{metroAxis.label}</p>
              <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-[11px] font-semibold text-ink-500">{metroLabel}</p>
                  <div className="mt-1.5 space-y-1.5">
                    {metroAxis.subItems.map((item, i) => (
                      <SubItemRow key={`metro-${id}-${i}`} item={item} />
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-[11px] font-semibold text-ink-500">{jeonbukLabel}</p>
                  <div className="mt-1.5 space-y-1.5">
                    {jeonbukAxis.subItems.map((item, i) => (
                      <SubItemRow key={`jeonbuk-${id}-${i}`} item={item} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
