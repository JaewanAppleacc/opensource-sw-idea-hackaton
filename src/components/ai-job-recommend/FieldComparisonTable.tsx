import { AlertTriangle, HelpCircle, Loader2, Quote } from 'lucide-react'
import type { AuditedField, PostingAnalysis, VerificationAction } from '../../lib/apiClient'
import { CHANNEL_LABELS, FIELD_LABELS, FIELD_ORDER, STATUS_LABELS, errorCodeToMessage } from '../../lib/displayLabels'
import type { AnalysisState } from './PostingAnalysisPanel'

interface FieldComparisonTableProps {
  metroLabel: string
  jeonbukLabel: string
  metro: AnalysisState
  jeonbuk: AnalysisState
}

const STATUS_STYLES: Record<string, string> = {
  confirmed: 'bg-tint-mint/60 text-brand-green',
  vague: 'bg-amber-100 text-amber-700',
  absent: 'bg-surface-muted text-ink-500',
}

function SideStatus({ label, state }: { label: string; state: AnalysisState }) {
  return (
    <div className="rounded-card border border-ink-border bg-white p-5">
      <h4 className="text-sm font-bold text-ink-900">{label}</h4>
      {state.status === 'idle' && <p className="mt-3 text-sm text-ink-400">분석 대기 중입니다.</p>}
      {state.status === 'loading' && (
        <p className="mt-3 flex items-center gap-2 text-sm text-ink-500">
          <Loader2 size={16} aria-hidden="true" className="animate-spin" />
          공고를 분석하고 있어요...
        </p>
      )}
      {state.status === 'error' && (
        <div role="alert" className="mt-3 flex items-start gap-2 rounded-card border border-red-200 bg-red-50 p-3 text-sm text-red-600">
          <AlertTriangle size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
          <span>{errorCodeToMessage(state.error.code, state.error.message)}</span>
        </div>
      )}
    </div>
  )
}

function FieldCell({
  audited,
  action,
}: {
  audited: AuditedField | undefined
  action: VerificationAction | undefined
}) {
  if (!audited) {
    return <p className="text-sm text-ink-400">이 항목은 분석 결과에 포함되지 않았습니다.</p>
  }
  return (
    <div>
      <span className={`inline-flex rounded-pill px-2 py-0.5 text-[11px] font-medium ${STATUS_STYLES[audited.status]}`}>
        {STATUS_LABELS[audited.status]}
      </span>
      <p className="mt-1.5 text-sm text-ink-700">
        {audited.evidence ? (
          <span className="flex items-start gap-1.5">
            <Quote size={13} aria-hidden="true" className="mt-0.5 shrink-0 text-ink-400" />
            <span>&ldquo;{audited.evidence.text}&rdquo;</span>
          </span>
        ) : (
          <span className="text-ink-400">근거 문구 없음</span>
        )}
      </p>
      {action && (
        <p className="mt-1.5 flex items-start gap-1.5 rounded-card bg-surface-muted p-2 text-xs text-ink-500">
          <HelpCircle size={13} aria-hidden="true" className="mt-0.5 shrink-0 text-brand-blue" />
          <span>
            <strong className="font-semibold text-ink-700">확인이 필요한 질문 ({CHANNEL_LABELS[action.channel]})</strong>
            <br />
            {action.prompt}
          </span>
        </p>
      )}
    </div>
  )
}

/**
 * TASK section 6: the 6 audited fields shown as 수도권/전북 columns, one row
 * per field, so both sides are visible side by side on desktop and stacked
 * on mobile. Uses the same `confirmed | vague | absent` enum from the
 * backend contract; only the Korean display label changes (displayLabels.ts).
 */
export function FieldComparisonTable({ metroLabel, jeonbukLabel, metro, jeonbuk }: FieldComparisonTableProps) {
  const bothReady = metro.status === 'success' && jeonbuk.status === 'success'

  if (!bothReady) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <SideStatus label={metroLabel} state={metro} />
        <SideStatus label={jeonbukLabel} state={jeonbuk} />
      </div>
    )
  }

  const metroAnalysis: PostingAnalysis = metro.analysis
  const jeonbukAnalysis: PostingAnalysis = jeonbuk.analysis

  return (
    <div className="space-y-4">
      <div className="hidden grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-4 sm:grid sm:pl-[9.5rem]">
        <p className="text-xs font-semibold text-ink-500">{metroLabel}</p>
        <p className="text-xs font-semibold text-ink-500">{jeonbukLabel}</p>
      </div>
      {FIELD_ORDER.map((field) => {
        const metroField = metroAnalysis.fields[field]
        const jeonbukField = jeonbukAnalysis.fields[field]
        const metroAction = metroAnalysis.verification_actions.find((a) => a.field === field)
        const jeonbukAction = jeonbukAnalysis.verification_actions.find((a) => a.field === field)
        return (
          <div key={field} className="rounded-card border border-ink-border bg-white p-4 sm:flex sm:items-start sm:gap-4">
            <p className="mb-2 shrink-0 text-sm font-bold text-ink-900 sm:mb-0 sm:w-36">{FIELD_LABELS[field]}</p>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:flex-1">
              <div>
                <p className="mb-1 text-xs font-semibold text-ink-500 sm:hidden">{metroLabel}</p>
                <FieldCell audited={metroField} action={metroAction} />
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold text-ink-500 sm:hidden">{jeonbukLabel}</p>
                <FieldCell audited={jeonbukField} action={jeonbukAction} />
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
