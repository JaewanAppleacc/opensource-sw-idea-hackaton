import { AlertTriangle, ChevronDown, Loader2, Sparkles, Wallet } from 'lucide-react'
import { useState } from 'react'
import {
  ApiClientError,
  analyzeByPostingId,
  getHomeRegionMatches,
  type MatchCandidate,
  type PostingListItem,
} from '../../lib/apiClient'
import { errorCodeToMessage } from '../../lib/displayLabels'
import { JeonbukCandidateList } from './JeonbukCandidateList'
import { PostingAnalysisPanel, type AnalysisState } from './PostingAnalysisPanel'
import { FinanceComparisonPanel } from './FinanceComparisonPanel'
import { GapStatsNotice } from './GapStatsNotice'

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
 * Per-card inline expansion: "전북 일자리 비교 에이전트" -- matches the
 * given capital-area posting against the server's home-region dataset via
 * the real curated pairs (never a client-chosen region), then lets the
 * user drill into a six-field comparison and an optional finance
 * comparison. Never shown as a separate tool; always anchored to the
 * specific posting card it was opened from.
 */
export function InlineJeonbukAgentPanel({ metroPosting, homeRegionLabel }: InlineJeonbukAgentPanelProps) {
  const [expanded, setExpanded] = useState(false)
  const [matchState, setMatchState] = useState<MatchState>({ status: 'idle' })
  const [selectedCandidate, setSelectedCandidate] = useState<MatchCandidate | null>(null)
  const [metroAnalysis, setMetroAnalysis] = useState<AnalysisState>({ status: 'idle' })
  const [jeonbukAnalysis, setJeonbukAnalysis] = useState<AnalysisState>({ status: 'idle' })
  const [financeOpen, setFinanceOpen] = useState(false)

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

  const analysisSettled =
    (metroAnalysis.status === 'success' || metroAnalysis.status === 'error') &&
    (jeonbukAnalysis.status === 'success' || jeonbukAnalysis.status === 'error')

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
          <div>
            <p className="font-semibold text-ink-900">내 지역 비교 에이전트가 찾은 {homeRegionLabel} 일자리</p>
            <p className="mt-0.5 text-xs text-ink-400">
              직무와 고용조건을 기준으로 비교했습니다. 확인되지 않은 정보는 추정하지 않습니다.
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
              현재 검증된 {homeRegionLabel} 비교 후보가 없습니다.
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
            <div className="space-y-3 border-t border-ink-border pt-4">
              <h4 className="text-sm font-bold text-ink-900">6개 항목 비교</h4>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <PostingAnalysisPanel title="수도권 공고" state={metroAnalysis} />
                <PostingAnalysisPanel
                  title={`${homeRegionLabel} 후보 (${selectedCandidate.company_name ?? selectedCandidate.posting_id})`}
                  state={jeonbukAnalysis}
                />
              </div>
              <GapStatsNotice />
            </div>
          )}

          {analysisSettled && (
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
