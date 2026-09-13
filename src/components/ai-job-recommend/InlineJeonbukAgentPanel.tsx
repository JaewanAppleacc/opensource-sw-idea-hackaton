import { AlertTriangle, Building2, FileText, Loader2, MapPin } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import {
  ApiClientError,
  analyzeByPostingId,
  getHomeRegionMatches,
  type MatchCandidate,
  type PostingListItem,
} from '../../lib/apiClient'
import { errorCodeToMessage } from '../../lib/displayLabels'
import { buildAxisResults, DEFAULT_SELECTED_AXES, type AxisId } from '../../lib/comparisonAxes'
import { buildPriorityUnresolvedList } from '../../lib/priorityUnresolved'
import { JeonbukCandidateList } from './JeonbukCandidateList'
import type { AnalysisState } from './PostingAnalysisPanel'
import { GapStatsNotice } from './GapStatsNotice'
import { ComparisonReportModal } from './report/ComparisonReportModal'

type MatchState =
  | { status: 'loading' }
  | { status: 'success'; candidates: MatchCandidate[] }
  | { status: 'empty' }
  | { status: 'error'; error: ApiClientError }

function toApiClientError(reason: unknown): ApiClientError {
  if (reason instanceof ApiClientError) return reason
  return new ApiClientError({ code: 'unexpected_response', message: '알 수 없는 오류가 발생했습니다.' })
}

interface InlineJeonbukAgentPanelProps {
  metroPosting: PostingListItem
  homeRegionLabel: string
  onAnalysisSettledChange?: (settled: boolean) => void
  className?: string
}

/**
 * The single right-hand 전북 비교 패널 rendered by the page for whichever
 * 수도권 공고 the user selected in the list. Looks up up to three
 * home-region comparison candidates for that posting (server-enforced home
 * region), lets the user pick exactly one, then runs the existing six-field
 * analysis on both postings. Once both succeed, the actual report is
 * presented in `ComparisonReportModal` (TASK "단계형 리포트 모달") rather
 * than inline here -- this panel now only ever shows the candidate list,
 * loading/error states, and a compact "선택한 기업 + 리포트 다시 보기"
 * summary once a report exists, so its content is never duplicated with the
 * modal's. The three candidates are a deterministic display order
 * (pre-linked pair first, then same-group postings in collection order),
 * never a similarity ranking, and only the user's selected candidate is
 * ever sent for analysis. Never computes or shows a combined score or a
 * winner anywhere in this file or the modal it opens.
 */
export function InlineJeonbukAgentPanel({
  metroPosting,
  homeRegionLabel,
  onAnalysisSettledChange,
  className = '',
}: InlineJeonbukAgentPanelProps) {
  const [matchState, setMatchState] = useState<MatchState>({ status: 'loading' })
  const [selectedCandidate, setSelectedCandidate] = useState<MatchCandidate | null>(null)
  const [metroAnalysis, setMetroAnalysis] = useState<AnalysisState>({ status: 'idle' })
  const [jeonbukAnalysis, setJeonbukAnalysis] = useState<AnalysisState>({ status: 'idle' })
  const [selectedAxisIds, setSelectedAxisIds] = useState<AxisId[]>(DEFAULT_SELECTED_AXES)
  const [reportOpen, setReportOpen] = useState(false)
  const [financeCompleted, setFinanceCompleted] = useState(false)

  // Guards against a late-arriving analyze response from a request that is
  // no longer the current selection -- without this, switching candidates
  // quickly could let a stale response overwrite newer state, or reopen a
  // report the user already closed (TASK "모달 접근성": "늦게 도착한 응답이
  // 닫힌 모달을 다시 열어서는 안 됩니다").
  const requestIdRef = useRef(0)
  // Tracks which candidate's success we've already auto-opened the modal
  // for, so re-renders don't reopen a report the user explicitly closed.
  const autoOpenedForRef = useRef<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setMatchState({ status: 'loading' })
    setSelectedCandidate(null)
    setMetroAnalysis({ status: 'idle' })
    setJeonbukAnalysis({ status: 'idle' })
    setReportOpen(false)
    setFinanceCompleted(false)
    requestIdRef.current += 1
    autoOpenedForRef.current = null
    getHomeRegionMatches({ metro_posting_id: metroPosting.posting_id })
      .then((response) => {
        if (cancelled) return
        setMatchState(
          response.candidates.length === 0 ? { status: 'empty' } : { status: 'success', candidates: response.candidates },
        )
      })
      .catch((err) => {
        if (cancelled) return
        if (err instanceof ApiClientError && err.code === 'no_match_found') {
          setMatchState({ status: 'empty' })
        } else {
          setMatchState({ status: 'error', error: toApiClientError(err) })
        }
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [metroPosting.posting_id])

  async function handleSelectCandidate(candidate: MatchCandidate) {
    const myRequestId = ++requestIdRef.current
    setSelectedCandidate(candidate)
    setReportOpen(false)
    setFinanceCompleted(false)
    setMetroAnalysis({ status: 'loading' })
    setJeonbukAnalysis({ status: 'loading' })

    const [metroResult, jeonbukResult] = await Promise.allSettled([
      analyzeByPostingId({ posting_id: metroPosting.posting_id, expected_occupation: metroPosting.occupation }),
      analyzeByPostingId({ posting_id: candidate.posting_id, expected_occupation: candidate.occupation }),
    ])

    if (requestIdRef.current !== myRequestId) return // superseded by a newer selection

    setMetroAnalysis(
      metroResult.status === 'fulfilled'
        ? { status: 'success', analysis: metroResult.value }
        : { status: 'error', error: toApiClientError(metroResult.reason) },
    )
    setJeonbukAnalysis(
      jeonbukResult.status === 'fulfilled'
        ? { status: 'success', analysis: jeonbukResult.value }
        : { status: 'error', error: toApiClientError(jeonbukResult.reason) },
    )
  }

  const bothSucceeded = metroAnalysis.status === 'success' && jeonbukAnalysis.status === 'success'
  const analysisSettled =
    (metroAnalysis.status === 'success' || metroAnalysis.status === 'error') &&
    (jeonbukAnalysis.status === 'success' || jeonbukAnalysis.status === 'error')

  useEffect(() => {
    onAnalysisSettledChange?.(analysisSettled && bothSucceeded)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analysisSettled, bothSucceeded])

  // 분석이 성공적으로 끝나는 순간(가짜 성공 아님, 실제 두 분석 모두 성공)에만
  // 자동으로 리포트 모달을 연다. 같은 후보에 대해 두 번 자동으로 열지 않는다
  // -- 사용자가 닫은 뒤에도 이 값은 그대로라 다시 열리지 않는다.
  useEffect(() => {
    if (bothSucceeded && selectedCandidate && autoOpenedForRef.current !== selectedCandidate.posting_id) {
      autoOpenedForRef.current = selectedCandidate.posting_id
      setReportOpen(true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bothSucceeded, selectedCandidate])

  const metroAxes = useMemo(
    () => (metroAnalysis.status === 'success' ? buildAxisResults(metroAnalysis.analysis) : null),
    [metroAnalysis],
  )
  const jeonbukAxes = useMemo(
    () => (jeonbukAnalysis.status === 'success' ? buildAxisResults(jeonbukAnalysis.analysis) : null),
    [jeonbukAnalysis],
  )

  const jeonbukCardLabel = `${homeRegionLabel} 후보 (${selectedCandidate?.company_name ?? selectedCandidate?.posting_id ?? ''})`

  const priorityItems = useMemo(() => {
    if (!metroAxes || !jeonbukAxes) return []
    return buildPriorityUnresolvedList(
      [
        { region: 'metro', axes: metroAxes },
        { region: 'jeonbuk', axes: jeonbukAxes },
      ],
      selectedAxisIds,
    )
  }, [metroAxes, jeonbukAxes, selectedAxisIds])

  const statusCounts = useMemo(() => {
    if (!metroAxes || !jeonbukAxes) return null
    const counts = { confirmed: 0, vague: 0, absent: 0 }
    for (const axes of [metroAxes, jeonbukAxes]) {
      for (const axis of axes) {
        for (const item of axis.subItems) {
          if (item.displayStatus === 'confirmed') counts.confirmed += 1
          else if (item.displayStatus === 'vague') counts.vague += 1
          else if (item.displayStatus === 'absent') counts.absent += 1
        }
      }
    }
    return counts
  }, [metroAxes, jeonbukAxes])

  function handleRequestAnotherCandidate() {
    setReportOpen(false)
    setSelectedCandidate(null)
    setMetroAnalysis({ status: 'idle' })
    setJeonbukAnalysis({ status: 'idle' })
    setFinanceCompleted(false)
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div>
        <p className="text-xs font-semibold text-ink-400">선택한 공고</p>
        <p className="mt-1 flex items-center gap-1.5 font-bold text-ink-900">
          <Building2 size={15} aria-hidden="true" className="shrink-0 text-ink-400" />
          {metroPosting.company_name ?? metroPosting.posting_id}
        </p>
        <p className="mt-0.5 flex items-center gap-1 text-xs text-ink-500">
          <MapPin size={11} aria-hidden="true" />
          {metroPosting.municipality ?? metroPosting.region} · {metroPosting.occupation} · {metroPosting.employment_type}
        </p>
      </div>

      <div className="border-t border-ink-border pt-4">
        <p className="text-sm font-bold text-ink-900">전북 비교 공고</p>
        <p className="mt-0.5 text-xs text-ink-400">같은 모집직종과 고용형태의 공고를 표시합니다.</p>
        <p className="text-[11px] text-ink-300">표시 순서는 유사도 순위가 아닙니다.</p>

        <div className="mt-3">
          {matchState.status === 'loading' && (
            <p className="flex items-center gap-2 text-sm text-ink-500">
              <Loader2 size={16} aria-hidden="true" className="animate-spin" />
              비교 후보를 찾고 있어요...
            </p>
          )}
          {matchState.status === 'empty' && (
            <p className="rounded-card bg-surface-muted p-3 text-sm text-ink-700">
              현재 표시할 수 있는 {homeRegionLabel} 비교 후보가 없습니다. (동일하게 정규화한 모집직종·고용형태의
              공고가 현재 배치에 없습니다)
            </p>
          )}
          {matchState.status === 'error' && (
            <p role="alert" className="flex items-start gap-2 rounded-card border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              <AlertTriangle size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
              {errorCodeToMessage(matchState.error.code, matchState.error.message)}
            </p>
          )}
          {matchState.status === 'success' && (
            <JeonbukCandidateList
              candidates={matchState.candidates}
              selectedPostingId={selectedCandidate?.posting_id ?? null}
              onSelect={(candidate) => void handleSelectCandidate(candidate)}
            />
          )}
        </div>
      </div>

      {selectedCandidate && (
        <div className="space-y-3 border-t border-ink-border pt-4">
          {!analysisSettled && (
            <p className="flex items-center gap-2 text-sm text-ink-500">
              <Loader2 size={16} aria-hidden="true" className="animate-spin" />
              채용공고의 확인 가능한 정보를 정리하고 있습니다.
            </p>
          )}

          {metroAnalysis.status === 'error' && (
            <p role="alert" className="flex items-start gap-2 rounded-card border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              <AlertTriangle size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
              수도권 공고: {errorCodeToMessage(metroAnalysis.error.code, metroAnalysis.error.message)}
            </p>
          )}
          {jeonbukAnalysis.status === 'error' && (
            <p role="alert" className="flex items-start gap-2 rounded-card border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              <AlertTriangle size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
              {homeRegionLabel} 후보: {errorCodeToMessage(jeonbukAnalysis.error.code, jeonbukAnalysis.error.message)}
            </p>
          )}

          {bothSucceeded && (
            <div className="space-y-2.5 rounded-card border border-ink-border bg-white p-3">
              <p className="text-sm text-ink-700">
                <strong className="font-semibold text-ink-900">
                  {selectedCandidate.company_name ?? selectedCandidate.posting_id}
                </strong>
                과(와)의 비교 리포트가 준비됐어요.
              </p>
              <button
                type="button"
                onClick={() => setReportOpen(true)}
                className="flex items-center gap-1.5 rounded-pill border border-brand-blue px-3.5 py-1.5 text-sm font-semibold text-brand-blue transition-colors duration-150 hover:bg-tint-sky/20"
              >
                <FileText size={14} aria-hidden="true" />
                비교 리포트 다시 보기
              </button>
            </div>
          )}

          <GapStatsNotice />
        </div>
      )}

      {bothSucceeded && metroAxes && jeonbukAxes && statusCounts && selectedCandidate && (
        <ComparisonReportModal
          open={reportOpen}
          onClose={() => setReportOpen(false)}
          onRequestAnotherCandidate={handleRequestAnotherCandidate}
          metroPosting={metroPosting}
          jeonbukCandidate={selectedCandidate}
          metroLabel="수도권 공고"
          jeonbukLabel={jeonbukCardLabel}
          metroAxes={metroAxes}
          jeonbukAxes={jeonbukAxes}
          priorityItems={priorityItems}
          statusCounts={statusCounts}
          selectedAxisIds={selectedAxisIds}
          onSelectedAxisIdsChange={setSelectedAxisIds}
          financeCompleted={financeCompleted}
          onFinanceComputed={() => setFinanceCompleted(true)}
        />
      )}
    </div>
  )
}
