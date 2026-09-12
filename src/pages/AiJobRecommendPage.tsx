import { AlertTriangle, ArrowLeft, Loader2, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Container } from '../components/ui/Container'
import { CollapsiblePanel } from '../components/ui/CollapsiblePanel'
import { DemoModeNotice } from '../components/ai-job-recommend/DemoModeNotice'
import { DemoLoginBanner } from '../components/ai-job-recommend/DemoLoginBanner'
import { MetroJobCard } from '../components/ai-job-recommend/MetroJobCard'
import { JeonbukCandidateList } from '../components/ai-job-recommend/JeonbukCandidateList'
import { FieldComparisonTable } from '../components/ai-job-recommend/FieldComparisonTable'
import { FinanceComparisonPanel } from '../components/ai-job-recommend/FinanceComparisonPanel'
import { GapStatsNotice } from '../components/ai-job-recommend/GapStatsNotice'
import type { AnalysisState } from '../components/ai-job-recommend/PostingAnalysisPanel'
import { METRO_JOB_LISTINGS, type MetroJobListing } from '../data/metroJobListings'
import { loadDemoProfile } from '../lib/demoProfile'
import { ApiClientError, analyzePosting, matchPostings, type MatchCandidate } from '../lib/apiClient'
import { errorCodeToMessage } from '../lib/displayLabels'

type CandidatesState =
  | { status: 'loading' }
  | { status: 'success'; candidates: MatchCandidate[]; datasetDescription: string }
  | { status: 'empty' }
  | { status: 'error'; error: ApiClientError }

function toApiClientError(reason: unknown): ApiClientError {
  if (reason instanceof ApiClientError) return reason
  return new ApiClientError({ code: 'unexpected_response', message: '알 수 없는 오류가 발생했습니다.' })
}

/**
 * 고용24 AI추천(일자리) 목록 안에서 바로 동작하는 지역 비교 에이전트 UX
 * (TASK section 2/4). Manual posting paste is no longer the landing screen
 * -- it now lives at /manual-analysis as an advanced/secondary path
 * (TASK section 8).
 */
export function AiJobRecommendPage() {
  const [profile] = useState(() => loadDemoProfile())
  const [selectedMetro, setSelectedMetro] = useState<MetroJobListing>(METRO_JOB_LISTINGS[0])
  const [candidatesState, setCandidatesState] = useState<CandidatesState>({ status: 'loading' })
  const [selectedCandidate, setSelectedCandidate] = useState<MatchCandidate | null>(null)
  const [metroAnalysis, setMetroAnalysis] = useState<AnalysisState>({ status: 'idle' })
  const [jeonbukAnalysis, setJeonbukAnalysis] = useState<AnalysisState>({ status: 'idle' })

  async function fetchCandidates(occupation: string) {
    setCandidatesState({ status: 'loading' })
    try {
      const response = await matchPostings({ occupation })
      if (response.candidates.length === 0) {
        setCandidatesState({ status: 'empty' })
      } else {
        setCandidatesState({
          status: 'success',
          candidates: response.candidates,
          datasetDescription: response.dataset_description,
        })
      }
    } catch (err) {
      if (err instanceof ApiClientError && err.code === 'no_match_found') {
        setCandidatesState({ status: 'empty' })
      } else {
        setCandidatesState({ status: 'error', error: toApiClientError(err) })
      }
    }
  }

  useEffect(() => {
    // Demo convenience (TASK section 4): the first metro posting's Jeonbuk
    // comparison panel is open on load. Selecting a different posting below
    // replaces it via handleCompareRegion.
    void fetchCandidates(selectedMetro.occupation)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function handleCompareRegion(listing: MetroJobListing) {
    setSelectedCandidate(null)
    setMetroAnalysis({ status: 'idle' })
    setJeonbukAnalysis({ status: 'idle' })
    setSelectedMetro(listing)
    void fetchCandidates(listing.occupation)
  }

  async function handleSelectCandidate(candidate: MatchCandidate) {
    setSelectedCandidate(candidate)
    setMetroAnalysis({ status: 'loading' })
    setJeonbukAnalysis({ status: 'loading' })

    // Two independent requests, run in parallel. Neither result is hidden
    // because the other failed -- each side renders its own settled state.
    const [metroResult, jeonbukResult] = await Promise.allSettled([
      analyzePosting({
        source_text: selectedMetro.fullText,
        source_url: selectedMetro.sourceUrl,
        expected_occupation: selectedMetro.occupation,
      }),
      candidate.source_text
        ? analyzePosting({
            posting_id: candidate.posting_id,
            source_text: candidate.source_text,
            source_url: candidate.source_url,
            expected_occupation: candidate.occupation,
          })
        : Promise.reject(
            new ApiClientError({
              code: 'invalid_input',
              message: '이 후보는 원문을 표시할 수 없어 분석할 수 없습니다 (재배포 권한 미확인).',
            }),
          ),
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
    <div className="py-10 sm:py-14">
      <Container className="max-w-5xl">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-ink-500 transition hover:text-brand-blue"
        >
          <ArrowLeft size={16} aria-hidden="true" />
          고용24 홈으로
        </Link>

        <div className="mt-4 flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-indigo text-white">
            <Sparkles size={22} aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-bold text-brand-blue">AI추천(일자리)</p>
            <h1 className="text-xl font-bold text-ink-900 sm:text-2xl">AI추천 채용공고</h1>
          </div>
        </div>

        <div className="mt-4">
          <DemoModeNotice />
        </div>

        <div className="mt-4">
          <DemoLoginBanner profile={profile} />
        </div>

        <p className="mt-4 text-sm leading-relaxed text-ink-500">
          관심 직종에 맞춘 수도권 AI추천 채용공고입니다. 공고 옆의 <strong className="text-ink-700">내 지역 유사 일자리 보기</strong>를
          누르면 {profile.homeRegionLabel} 지역의 비교 가능한 공고를 함께 볼 수 있어요.
        </p>

        <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2 lg:items-start">
          <section aria-labelledby="metro-list-heading" className="space-y-3">
            <h2 id="metro-list-heading" className="text-lg font-bold text-ink-900">
              수도권 AI추천 공고
            </h2>
            <ul className="space-y-4">
              {METRO_JOB_LISTINGS.map((listing) => (
                <MetroJobCard
                  key={listing.id}
                  listing={listing}
                  isActive={listing.id === selectedMetro.id}
                  onCompareRegion={handleCompareRegion}
                />
              ))}
            </ul>
          </section>

          <section aria-labelledby="candidates-heading" className="space-y-3 lg:sticky lg:top-6">
            <h2 id="candidates-heading" className="sr-only">
              전북 비교 후보
            </h2>

            {candidatesState.status === 'loading' && (
              <p className="flex items-center gap-2 text-sm text-ink-500">
                <Loader2 size={16} aria-hidden="true" className="animate-spin" />
                {selectedMetro.companyName} 공고 기준으로 전북 비교 후보를 찾고 있어요...
              </p>
            )}

            {candidatesState.status === 'empty' && (
              <p className="rounded-card border border-ink-border bg-surface-muted p-4 text-sm text-ink-700">
                현재 검증된 전북 비교 후보가 없습니다.
              </p>
            )}

            {candidatesState.status === 'error' && (
              <p role="alert" className="flex items-start gap-2 rounded-card border border-red-200 bg-red-50 p-4 text-sm text-red-600">
                <AlertTriangle size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
                {errorCodeToMessage(candidatesState.error.code, candidatesState.error.message)}
              </p>
            )}

            {candidatesState.status === 'success' && (
              <JeonbukCandidateList
                candidates={candidatesState.candidates}
                datasetDescription={candidatesState.datasetDescription}
                selectedPostingId={selectedCandidate?.posting_id ?? null}
                onSelect={(candidate) => void handleSelectCandidate(candidate)}
              />
            )}
          </section>
        </div>

        {selectedCandidate && (
          <div className="mt-8 space-y-6">
            <section aria-labelledby="comparison-heading" className="space-y-3">
              <h2 id="comparison-heading" className="text-lg font-bold text-ink-900">
                6개 항목 비교
              </h2>
              <p className="text-sm text-ink-500">
                {selectedMetro.companyName} (수도권) ↔ {selectedCandidate.company_name ?? selectedCandidate.posting_id} (
                {profile.homeRegionLabel})
              </p>
              <FieldComparisonTable
                metroLabel={`수도권 · ${selectedMetro.companyName}`}
                jeonbukLabel={`전북 · ${selectedCandidate.company_name ?? selectedCandidate.posting_id}`}
                metro={metroAnalysis}
                jeonbuk={jeonbukAnalysis}
              />
            </section>

            <GapStatsNotice />

            {analysisSettled && (
              <CollapsiblePanel label="주거비를 포함한 자금 축적 비교">
                <FinanceComparisonPanel />
              </CollapsiblePanel>
            )}
          </div>
        )}

        <div className="mt-10 border-t border-ink-border pt-6 text-sm">
          <Link
            to="/manual-analysis"
            className="font-semibold text-ink-500 underline decoration-dotted underline-offset-2 hover:text-brand-blue"
          >
            다른 공고를 직접 붙여넣어 비교하고 싶다면 (수동 입력, 고급 기능)
          </Link>
        </div>
      </Container>
    </div>
  )
}
