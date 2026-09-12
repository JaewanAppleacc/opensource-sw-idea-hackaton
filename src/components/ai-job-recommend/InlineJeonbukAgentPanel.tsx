import { AlertTriangle, Building2, ChevronDown, Loader2, MapPin, Wallet } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
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
import { ImportantConditionsSelector } from './ImportantConditionsSelector'
import { ComparisonAxesPanel } from './ComparisonAxesPanel'
import { PriorityUnresolvedPanel } from './PriorityUnresolvedPanel'
import { CompanyQuestionsPanel } from './CompanyQuestionsPanel'
import { FinanceComparisonPanel } from './FinanceComparisonPanel'
import { GapStatsNotice } from './GapStatsNotice'

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
 * 수도권 공고 the user selected in the list (TASK "UI 고도화" section 4/9).
 * Looks up up to three home-region comparison candidates for that posting
 * (server-enforced home region), lets the user pick exactly one, then pick
 * up to three important conditions, compares both postings across six
 * evidence-grounded axes, surfaces the highest-priority unresolved
 * information first, generates real questions to ask the company, and
 * offers an optional finance comparison. The three candidates are a
 * deterministic display order (pre-linked pair first, then same-group
 * postings in collection order), never a similarity ranking, and only the
 * user's selected candidate is ever sent for analysis. Never computes or
 * shows a combined score or a winner anywhere in this file.
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
  const [financeOpen, setFinanceOpen] = useState(false)
  const [selectedAxisIds, setSelectedAxisIds] = useState<AxisId[]>(DEFAULT_SELECTED_AXES)
  const [fullComparisonOpen, setFullComparisonOpen] = useState(false)

  useEffect(() => {
    let cancelled = false
    setMatchState({ status: 'loading' })
    setSelectedCandidate(null)
    setMetroAnalysis({ status: 'idle' })
    setJeonbukAnalysis({ status: 'idle' })
    setFinanceOpen(false)
    setFullComparisonOpen(false)
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
    setSelectedCandidate(candidate)
    setFinanceOpen(false)
    setMetroAnalysis({ status: 'loading' })
    setJeonbukAnalysis({ status: 'loading' })

    const [metroResult, jeonbukResult] = await Promise.allSettled([
      analyzeByPostingId({ posting_id: metroPosting.posting_id, expected_occupation: metroPosting.occupation }),
      analyzeByPostingId({ posting_id: candidate.posting_id, expected_occupation: candidate.occupation }),
    ])

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
        <div className="space-y-4 border-t border-ink-border pt-4">
          <ImportantConditionsSelector selected={selectedAxisIds} onChange={setSelectedAxisIds} />

          {!analysisSettled && (
            <p className="flex items-center gap-2 text-sm text-ink-500">
              <Loader2 size={16} aria-hidden="true" className="animate-spin" />
              공고를 분석하고 있어요...
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

          {bothSucceeded && metroAxes && jeonbukAxes && statusCounts && (
            <div className="space-y-4 border-t border-ink-border pt-4">
              <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
                <span className="font-semibold text-brand-green">확인됨 {statusCounts.confirmed}</span>
                <span className="font-semibold text-amber-700">추가 확인 {statusCounts.vague}</span>
                <span className="font-semibold text-ink-500">공고에 없음 {statusCounts.absent}</span>
              </p>

              <PriorityUnresolvedPanel
                items={priorityItems}
                metroLabel="수도권 공고"
                jeonbukLabel={jeonbukCardLabel}
              />

              <details
                open={fullComparisonOpen}
                onToggle={(e) => setFullComparisonOpen((e.target as HTMLDetailsElement).open)}
                className="group"
              >
                <summary className="flex cursor-pointer list-none items-center gap-1 text-sm font-semibold text-brand-blue marker:content-none">
                  전체 조건 비교 보기
                  <ChevronDown
                    size={14}
                    aria-hidden="true"
                    className={`transition-transform duration-200 ${fullComparisonOpen ? 'rotate-180' : ''}`}
                  />
                </summary>
                <div className="mt-3">
                  <ComparisonAxesPanel
                    metroLabel="수도권 공고"
                    jeonbukLabel={jeonbukCardLabel}
                    metroAxes={metroAxes}
                    jeonbukAxes={jeonbukAxes}
                    selectedAxisIds={selectedAxisIds}
                  />
                </div>
              </details>

              <CompanyQuestionsPanel
                items={priorityItems}
                metroLabel="수도권 공고"
                jeonbukLabel={jeonbukCardLabel}
              />
              <GapStatsNotice />
            </div>
          )}
        </div>
      )}

      {analysisSettled && bothSucceeded && (
        <div className="border-t border-ink-border pt-4">
          {!financeOpen ? (
            <button
              type="button"
              onClick={() => setFinanceOpen(true)}
              className="flex items-center gap-2 rounded-pill border border-ink-border bg-white px-4 py-2 text-sm font-semibold text-ink-700 transition-colors duration-150 hover:border-brand-blue hover:text-brand-blue"
            >
              <Wallet size={15} aria-hidden="true" />
              생활비까지 비교해보기
            </button>
          ) : (
            <FinanceComparisonPanel />
          )}
        </div>
      )}
    </div>
  )
}
