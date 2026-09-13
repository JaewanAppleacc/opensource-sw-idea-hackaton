import { CheckCircle2, Printer } from 'lucide-react'
import type { MatchCandidate, PostingListItem } from '../../../lib/apiClient'
import { AXIS_LABELS, type AxisId } from '../../../lib/comparisonAxes'

interface ReportSummaryStepProps {
  metroPosting: PostingListItem
  jeonbukCandidate: MatchCandidate
  selectedAxisIds: AxisId[]
  confirmedCount: number
  questionCount: number
  financeCompleted: boolean
  onClose: () => void
  onRequestAnotherCandidate: () => void
}

/**
 * Report step 6/6 -- "이제 무엇을 확인할지 정리됐어요". Read-only recap of
 * what steps 1-5 already established; introduces no new data or judgment
 * (no score, no winner). No file download or server save is added here --
 * printing uses window.print() plus the print stylesheet only.
 */
export function ReportSummaryStep({
  metroPosting,
  jeonbukCandidate,
  selectedAxisIds,
  confirmedCount,
  questionCount,
  financeCompleted,
  onClose,
  onRequestAnotherCandidate,
}: ReportSummaryStepProps) {
  const rows: { label: string; value: string }[] = [
    {
      label: '비교한 두 기업',
      value: `${metroPosting.company_name ?? metroPosting.posting_id} · ${jeonbukCandidate.company_name ?? jeonbukCandidate.posting_id}`,
    },
    {
      label: '내가 중요하게 선택한 조건',
      value: selectedAxisIds.length > 0 ? selectedAxisIds.map((id) => AXIS_LABELS[id]).join(', ') : '선택 안 함',
    },
    { label: '확인된 조건 개수', value: `${confirmedCount}개` },
    { label: '추가로 물어볼 질문 개수', value: `${questionCount}개` },
    { label: '자금 시나리오 실행 여부', value: financeCompleted ? '실행함' : '실행하지 않음' },
  ]

  return (
    <div className="report-print-area space-y-4">
      <div className="rounded-card border border-ink-border bg-white">
        <div className="flex items-center gap-2 border-b border-ink-border px-4 py-2.5">
          <CheckCircle2 size={16} aria-hidden="true" className="text-brand-green" />
          <p className="text-sm font-bold text-ink-900">지원 전 체크리스트</p>
        </div>
        <dl className="divide-y divide-ink-border">
          {rows.map((row) => (
            <div key={row.label} className="flex items-center justify-between gap-3 px-4 py-2.5 text-sm">
              <dt className="text-ink-500">{row.label}</dt>
              <dd className="text-right font-semibold text-ink-900">{row.value}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="report-print-hide flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onClose}
          className="rounded-pill border border-ink-border bg-white px-4 py-2 text-sm font-semibold text-ink-700 transition-colors duration-150 hover:border-brand-blue hover:text-brand-blue"
        >
          리포트 닫기
        </button>
        <button
          type="button"
          onClick={onRequestAnotherCandidate}
          className="rounded-pill bg-brand-blue px-4 py-2 text-sm font-semibold text-white transition-colors duration-150 hover:bg-brand-blue-dark"
        >
          다른 전북 공고 비교
        </button>
        <button
          type="button"
          onClick={() => window.print()}
          className="flex items-center gap-1.5 rounded-pill border border-ink-border bg-white px-4 py-2 text-sm font-semibold text-ink-500 transition-colors duration-150 hover:border-brand-blue hover:text-brand-blue"
        >
          <Printer size={14} aria-hidden="true" />
          인쇄하기
        </button>
      </div>
    </div>
  )
}
