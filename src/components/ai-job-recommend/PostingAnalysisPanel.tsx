import { AlertTriangle, HelpCircle, Loader2, Quote } from 'lucide-react'
import { ApiClientError, type PostingAnalysis } from '../../lib/apiClient'
import { CHANNEL_LABELS, FIELD_LABELS, FIELD_ORDER, STATUS_LABELS, errorCodeToMessage } from '../../lib/displayLabels'

export type AnalysisState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; analysis: PostingAnalysis }
  | { status: 'error'; error: ApiClientError }

interface PostingAnalysisPanelProps {
  title: string
  state: AnalysisState
}

const STATUS_STYLES: Record<string, string> = {
  confirmed: 'bg-tint-mint/60 text-brand-green',
  vague: 'bg-amber-100 text-amber-700',
  absent: 'bg-surface-muted text-ink-500',
}

export function PostingAnalysisPanel({ title, state }: PostingAnalysisPanelProps) {
  return (
    <div className="rounded-card border border-ink-border bg-white p-5">
      <h3 className="font-bold text-ink-900">{title}</h3>

      {state.status === 'idle' && <p className="mt-3 text-sm text-ink-400">분석 대기 중입니다.</p>}

      {state.status === 'loading' && (
        <p className="mt-3 flex items-center gap-2 text-sm text-ink-500">
          <Loader2 size={16} aria-hidden="true" className="animate-spin" />
          공고를 분석하고 있어요...
        </p>
      )}

      {state.status === 'error' && (
        <div
          role="alert"
          className="mt-3 flex items-start gap-2 rounded-card border border-red-200 bg-red-50 p-3 text-sm text-red-600"
        >
          <AlertTriangle size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
          <span>{errorCodeToMessage(state.error.code, state.error.message)}</span>
        </div>
      )}

      {state.status === 'success' && (
        <div className="mt-4 space-y-4">
          {(state.analysis.occupation || state.analysis.employment_type) && (
            <p className="text-xs text-ink-400">
              {[state.analysis.occupation, state.analysis.employment_type].filter(Boolean).join(' · ')}
            </p>
          )}

          <dl className="space-y-3">
            {FIELD_ORDER.map((field) => {
              const audited = state.analysis.fields[field]
              if (!audited) return null
              const action = state.analysis.verification_actions.find((a) => a.field === field)
              return (
                <div key={field} className="border-b border-ink-border pb-3 last:border-b-0 last:pb-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <dt className="text-sm font-semibold text-ink-900">{FIELD_LABELS[field]}</dt>
                    <span
                      className={`rounded-pill px-2 py-0.5 text-[11px] font-medium ${STATUS_STYLES[audited.status]}`}
                    >
                      {STATUS_LABELS[audited.status]}
                    </span>
                  </div>
                  <dd className="mt-1.5 text-sm text-ink-700">
                    {audited.evidence ? (
                      <span className="flex items-start gap-1.5 text-ink-700">
                        <Quote size={13} aria-hidden="true" className="mt-0.5 shrink-0 text-ink-400" />
                        <span>&ldquo;{audited.evidence.text}&rdquo;</span>
                      </span>
                    ) : (
                      <span className="text-ink-400">근거 문구 없음</span>
                    )}
                  </dd>
                  {action && (
                    <p className="mt-1.5 flex items-start gap-1.5 rounded-card bg-surface-muted p-2 text-xs text-ink-500">
                      <HelpCircle size={13} aria-hidden="true" className="mt-0.5 shrink-0 text-brand-blue" />
                      <span>
                        <strong className="font-semibold text-ink-700">확인 질문 ({CHANNEL_LABELS[action.channel]})</strong>
                        <br />
                        {action.prompt}
                      </span>
                    </p>
                  )}
                </div>
              )
            })}
          </dl>
        </div>
      )}
    </div>
  )
}
