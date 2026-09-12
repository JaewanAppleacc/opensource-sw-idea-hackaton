import { AlertTriangle, ArrowLeft, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Container } from '../components/ui/Container'
import { DemoInfoPopover } from '../components/ai-job-recommend/DemoInfoPopover'
import { LoginStatusBar } from '../components/ai-job-recommend/LoginStatusBar'
import { CapitalPostingCard } from '../components/ai-job-recommend/CapitalPostingCard'
import { InlineJeonbukAgentPanel } from '../components/ai-job-recommend/InlineJeonbukAgentPanel'
import { ServiceStepIndicator } from '../components/ai-job-recommend/ServiceStepIndicator'
import { ApiClientError, getHomeRegionListing, type PostingListItem } from '../lib/apiClient'
import { errorCodeToMessage } from '../lib/displayLabels'
import { DEMO_PROFILE, isDemoLoggedIn, setDemoLoggedIn } from '../lib/demoAuth'

type ListingState =
  | { status: 'loading' }
  | { status: 'success'; postings: PostingListItem[]; homeRegion: string }
  | { status: 'error'; error: ApiClientError }

function toApiClientError(reason: unknown): ApiClientError {
  if (reason instanceof ApiClientError) return reason
  return new ApiClientError({ code: 'unexpected_response', message: '알 수 없는 오류가 발생했습니다.' })
}

/**
 * Default AI추천(일자리) landing experience (see TASK "고용24 AI추천 목록 내
 * 전북 일자리 비교 에이전트 통합", restyled per "AI 티 제거 및 고용24 네이티브
 * UI 고도화"): a recommended-postings list on the left, a single selected
 * posting's region-comparison panel on the right (desktop) / below (mobile)
 * -- never a separate paste-and-analyze tool. The original manual-paste
 * flow still exists, unchanged, at /manual-analysis.
 */
export function AiJobRecommendPage() {
  const [loggedIn, setLoggedIn] = useState(() => isDemoLoggedIn())
  const [listingState, setListingState] = useState<ListingState>({ status: 'loading' })
  const [selectedPosting, setSelectedPosting] = useState<PostingListItem | null>(null)
  const [analysisSettled, setAnalysisSettled] = useState(false)

  useEffect(() => {
    let cancelled = false
    getHomeRegionListing()
      .then((response) => {
        if (cancelled) return
        setListingState({ status: 'success', postings: response.postings, homeRegion: response.home_region })
      })
      .catch((err) => {
        if (!cancelled) setListingState({ status: 'error', error: toApiClientError(err) })
      })
    return () => {
      cancelled = true
    }
  }, [])

  function handleLogin() {
    setDemoLoggedIn(true)
    setLoggedIn(true)
  }

  function handleLogout() {
    setDemoLoggedIn(false)
    setLoggedIn(false)
  }

  function handleSelectPosting(posting: PostingListItem) {
    setAnalysisSettled(false)
    setSelectedPosting((prev) => (prev?.posting_id === posting.posting_id ? prev : posting))
  }

  const homeRegionLabel = loggedIn ? DEMO_PROFILE.homeRegionLabel : listingState.status === 'success' ? listingState.homeRegion : ''
  const currentStep: 1 | 2 | 3 = !selectedPosting ? 1 : analysisSettled ? 3 : 2

  return (
    <div className="py-8 sm:py-10">
      <Container className="max-w-6xl">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-ink-500 transition-colors duration-150 hover:text-brand-blue"
        >
          <ArrowLeft size={16} aria-hidden="true" />
          고용24 홈으로
        </Link>

        <div className="mt-3 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-ink-900 sm:text-2xl">AI추천 일자리</h1>
            <p className="mt-1 text-sm text-ink-500">
              수도권 공고를 살펴보고 전북의 같은 직종 공고를 함께 비교해보세요.
            </p>
          </div>
          <DemoInfoPopover />
        </div>

        <div className="mt-4">
          <LoginStatusBar loggedIn={loggedIn} onLogin={handleLogin} onLogout={handleLogout} />
        </div>

        <ServiceStepIndicator currentStep={currentStep} className="mt-4" />

        <div className="mt-5">
          {listingState.status === 'loading' && (
            <p className="flex items-center gap-2 text-sm text-ink-500">
              <Loader2 size={16} aria-hidden="true" className="animate-spin" />
              수도권 채용공고 목록을 불러오고 있어요...
            </p>
          )}

          {listingState.status === 'error' && (
            <p role="alert" className="flex items-start gap-2 rounded-card border border-red-200 bg-red-50 p-4 text-sm text-red-600">
              <AlertTriangle size={18} aria-hidden="true" className="mt-0.5 shrink-0" />
              {errorCodeToMessage(listingState.error.code, listingState.error.message)}
            </p>
          )}

          {listingState.status === 'success' && listingState.postings.length === 0 && (
            <p className="rounded-card border border-ink-border bg-surface-muted p-4 text-sm text-ink-700">
              현재 표시할 수도권 채용공고가 없습니다.
            </p>
          )}

          {listingState.status === 'success' && listingState.postings.length > 0 && (
            <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)] xl:items-start">
              <div className="rounded-card border border-ink-border bg-white">
                <p className="border-b border-ink-border px-4 py-3 text-xs font-semibold text-ink-500">
                  수도권 추천 공고 목록 ({listingState.postings.length})
                </p>
                <ul className="divide-y divide-ink-border" data-testid="capital-posting-list">
                  {listingState.postings.map((posting) => (
                    <CapitalPostingCard
                      key={posting.posting_id}
                      posting={posting}
                      isSelected={selectedPosting?.posting_id === posting.posting_id}
                      onSelect={handleSelectPosting}
                    />
                  ))}
                </ul>
              </div>

              <div
                className="rounded-card border border-ink-border bg-white p-4 sm:p-5 xl:sticky xl:top-6"
                data-testid="jeonbuk-comparison-panel"
              >
                {selectedPosting ? (
                  <InlineJeonbukAgentPanel
                    key={selectedPosting.posting_id}
                    metroPosting={selectedPosting}
                    homeRegionLabel={homeRegionLabel}
                    onAnalysisSettledChange={setAnalysisSettled}
                    className="panel-update-in"
                  />
                ) : (
                  <p className="py-6 text-center text-sm text-ink-400">
                    왼쪽 목록에서 공고를 선택하면
                    <br />
                    {homeRegionLabel || '내 지역'} 비교 공고가 여기에 표시됩니다.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="mt-10 border-t border-ink-border pt-6 text-center">
          <Link to="/manual-analysis" className="text-xs font-medium text-ink-400 underline hover:text-brand-blue">
            다른 공고 직접 비교 (수동 붙여넣기)
          </Link>
        </div>
      </Container>
    </div>
  )
}
