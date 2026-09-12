import { BarChart3, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { getGapStats, type GapStats } from '../../lib/apiClient'

type GapStatsState =
  | { status: 'loading' }
  | { status: 'not_ready' }
  | { status: 'ready'; stats: GapStats }
  | { status: 'error' }

/**
 * Optional supplementary panel: calls GET /data/gap-stats and shows its
 * honest not-ready state rather than skipping this endpoint entirely. Never
 * shows the AI-A/B consensus reference set here -- gap-stats only ever
 * reads adjudicated human gold, and stays "준비되지 않음" until that exists.
 */
export function GapStatsNotice() {
  const [state, setState] = useState<GapStatsState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false
    getGapStats()
      .then((res) => {
        if (cancelled) return
        setState(res.ready && res.stats ? { status: 'ready', stats: res.stats } : { status: 'not_ready' })
      })
      .catch(() => {
        if (!cancelled) setState({ status: 'error' })
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="rounded-card border border-ink-border bg-surface-muted p-4 text-sm text-ink-500">
      <p className="flex items-center gap-1.5 font-semibold text-ink-700">
        <BarChart3 size={14} aria-hidden="true" />
        지역 결손 통계
      </p>
      {state.status === 'loading' && (
        <p className="mt-1 flex items-center gap-1.5">
          <Loader2 size={13} aria-hidden="true" className="animate-spin" />
          확인 중...
        </p>
      )}
      {state.status === 'not_ready' && (
        <p className="mt-1">
          아직 준비되지 않았습니다. 두 명의 독립적인 사람이 라벨링한 human gold가 확정된 뒤에만 이 통계가
          제공됩니다 — AI 검수 결과로 대체 표시하지 않습니다.
        </p>
      )}
      {state.status === 'ready' && (
        <p className="mt-1">
          탐색적 표본 통계 (n={state.stats.sample_size_postings}건, exploratory) — 전체 전북/수도권 채용시장에
          대한 결론이 아닙니다.
        </p>
      )}
      {state.status === 'error' && <p className="mt-1">통계를 불러오지 못했습니다.</p>}
    </div>
  )
}
