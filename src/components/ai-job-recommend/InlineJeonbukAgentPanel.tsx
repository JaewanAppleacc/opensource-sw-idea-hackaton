import { AlertTriangle, ChevronDown, Loader2, Sparkles, Wallet } from 'lucide-react'
import { useMemo, useState } from 'react'
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
import { ServiceStepIndicator } from './ServiceStepIndicator'

type MatchState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; candidates: MatchCandidate[]; datasetDescription: string }
  | { status: 'empty' }
  | { status: 'error'; error: ApiClientError }

function toApiClientError(reason: unknown): ApiClientError {
  if (reason instanceof ApiClientError) return reason
  return new ApiClientError({ code: 'unexpected_response', message: '알 수 없는 오류가 발생했습니다.' })
}

interface InlineJeonbukAgentPanelProps {
  metroPosting: PostingListItem
  homeRegionLabel: string
}

/**
 * Per-card inline expansion: "전북 일자리 비교 에이전트" -- looks up up to
 * three home-region comparison candidates for the given capital-area
 * posting (server-enforced home region; never a client-chosen one), lets
 * the user pick exactly one of them, then lets the user pick up to three
 * important conditions, compares both postings across six evidence-grounded
 * axes, surfaces the highest-priority unresolved information first,
 * generates real questions to ask the company, and offers an optional
 * finance comparison. The three candidates are a deterministic display
 * order (pre-linked pair first, then same-group postings in collection
 * order), never a similarity ranking, and only the user's selected
 * candidate is ever sent for analysis -- the other candidates are never
 * analyzed in the background. Never shown as a separate tool; always
 * anchored to the specific posting card it was opened from. Never computes
 * or shows a combined score or a winner anywhere in this file.
 */
export function InlineJeonbukAgentPanel({ metroPosting, homeRegionLabel }: InlineJeonbukAgentPanelProps) {
  const [expanded, setExpanded] = useState(false)
  const [matchState, setMatchState] = useState<MatchState>({ status: 'idle' })
  const [selectedCandidate, setSelectedCandidate] = useState<MatchCandidate | null>(null)
  const [metroAnalysis, setMetroAnalysis] = useState<AnalysisState>({ status: 'idle' })
  const [jeonbukAnalysis, setJeonbukAnalysis] = useState<AnalysisState>({ status: 'idle' })
  const [financeOpen, setFinanceOpen] = useState(false)
  const [selectedAxisIds, setSelectedAxisIds] = useState<AxisId[]>(DEFAULT_SELECTED_AXES)

  async function handleToggle() {
    const next = !expanded
    setExpanded(next)
    if (next && matchState.status === 'idle') {
      setMatchState({ status: 'loading' })
      try {
        const response = await getHomeRegionMatches({ metro_posting_id: metroPosting.posting_id })
        setMatchState(
          response.candidates.length === 0
            ? { status: 'empty' }
            : { status: 'success', candidates: response.candidates, datasetDescription: response.dataset_description },
        )
      } catch (err) {
        if (err instanceof ApiClientError && err.code === 'no_match_found') {
          setMatchState({ status: 'empty' })
        } else {
          setMatchState({ status: 'error', error: toApiClientError(err) })
        }
      }
    }
  }

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

  return (
    <div className="mt-3 border-t border-ink-border pt-3">
      <button
        type="button"
        onClick={() => void handleToggle()}
        aria-expanded={expanded}
        className="flex w-full items-center justify-between gap-2 rounded-card border border-brand-blue/40 bg-tint-sky/20 px-4 py-2.5 text-left text-sm font-semibold text-brand-blue transition hover:bg-tint-sky/40"
      >
        <span className="flex items-center gap-1.5">
          <Sparkles size={15} aria-hidden="true" />내 지역 유사 일자리 보기
          <span className="font-normal text-ink-500">({homeRegionLabel} 기준)</span>
        </span>
        <ChevronDown
          size={16}
          aria-hidden="true"
          className={`shrink-0 transition-transform ${expanded ? 'rotate-180' : ''}`}
        />
      </button>

      {expanded && (
        <div className="mt-3 space-y-4 rounded-card border border-ink-border bg-white p-4">
          <ServiceStepIndicator currentStep={bothSucceeded || financeOpen ? 4 : 3} />
          <div>
            <p className="font-semibold text-ink-900">동일 직종·고용형태의 {homeRegionLabel} 비교 공고</p>
            <p className="mt-0.5 text-xs text-ink-400">
              수집 시 동일하게 정규화한 모집직종과 고용형태의 {homeRegionLabel} 공고를 최대 3건 표시합니다. 표시
              순서는 유사도 순위가 아니며, 가장 적합하거나 유일한 지역 대안이라는 의미는 아닙니다. 확인되지 않은
              정보는 추정하지 않습니다.
            </p>
          </div>

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
              datasetDescription={matchState.datasetDescription}
              selectedPostingId={selectedCandidate?.posting_id ?? null}
              onSelect={(candidate) => void handleSelectCandidate(candidate)}
            />
          )}

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

              {bothSucceeded && metroAxes && jeonbukAxes && (
                <>
                  <h4 className="text-sm font-bold text-ink-900">수정된 6개 비교축</h4>
                  <ComparisonAxesPanel
                    metroLabel="수도권 공고"
                    jeonbukLabel={jeonbukCardLabel}
                    metroAxes={metroAxes}
                    jeonbukAxes={jeonbukAxes}
                    selectedAxisIds={selectedAxisIds}
                  />
                  <PriorityUnresolvedPanel
                    items={priorityItems}
                    metroLabel="수도권 공고"
                    jeonbukLabel={jeonbukCardLabel}
                  />
                  <CompanyQuestionsPanel
                    items={priorityItems}
                    metroLabel="수도권 공고"
                    jeonbukLabel={jeonbukCardLabel}
                  />
                  <GapStatsNotice />
                </>
              )}
            </div>
          )}

          {analysisSettled && bothSucceeded && (
            <div className="border-t border-ink-border pt-4">
              {!financeOpen ? (
                <button
                  type="button"
                  onClick={() => setFinanceOpen(true)}
                  className="flex items-center gap-2 rounded-pill border border-ink-border bg-white px-4 py-2 text-sm font-semibold text-ink-700 transition hover:border-brand-blue hover:text-brand-blue"
                >
                  <Wallet size={15} aria-hidden="true" />
                  자금 축적 비교 펼치기 (선택)
                </button>
              ) : (
                <FinanceComparisonPanel />
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
