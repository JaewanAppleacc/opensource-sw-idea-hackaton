import { AlertTriangle, ArrowLeft, ListChecks, Loader2, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Container } from '../components/ui/Container'
import { DemoModeNotice } from '../components/ai-job-recommend/DemoModeNotice'
import { LoginStatusBar } from '../components/ai-job-recommend/LoginStatusBar'
import { CapitalPostingCard } from '../components/ai-job-recommend/CapitalPostingCard'
import { JobCareProfilePanel } from '../components/ai-job-recommend/JobCareProfilePanel'
import { ServiceStepIndicator } from '../components/ai-job-recommend/ServiceStepIndicator'
import { ServiceDifferentiationNotice } from '../components/ai-job-recommend/ServiceDifferentiationNotice'
import { ApiClientError, getHomeRegionListing, type PostingListItem } from '../lib/apiClient'
import { errorCodeToMessage } from '../lib/displayLabels'
import { DEMO_PROFILE, isDemoLoggedIn, setDemoLoggedIn } from '../lib/demoAuth'

type ListingState =
  | { status: 'loading' }
  | { status: 'success'; postings: PostingListItem[]; homeRegion: string; datasetDescription: string }
  | { status: 'error'; error: ApiClientError }

function toApiClientError(reason: unknown): ApiClientError {
  if (reason instanceof ApiClientError) return reason
  return new ApiClientError({ code: 'unexpected_response', message: '알 수 없는 오류가 발생했습니다.' })
}

/**
 * Default AI추천(일자리) landing experience (see TASK "고용24 AI추천 목록 내
 * 전북 일자리 비교 에이전트 통합"): a recommended-postings list using real
 * capital-area posting metadata, each with an inline "내 지역 비교 공고
 * 보기" agent -- never a separate paste-and-analyze tool. The original
 * manual-paste flow still exists, unchanged, at /manual-analysis.
 */
export function AiJobRecommendPage() {
  const [loggedIn, setLoggedIn] = useState(() => isDemoLoggedIn())
  const [listingState, setListingState] = useState<ListingState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false
    getHomeRegionListing()
      .then((response) => {
        if (cancelled) return
        setListingState({
          status: 'success',
          postings: response.postings,
          homeRegion: response.home_region,
          datasetDescription: response.dataset_description,
        })
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

  return (
    <div className="py-10 sm:py-14">
      <Container className="max-w-3xl">
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
            <h1 className="text-xl font-bold text-ink-900 sm:text-2xl">수도권 채용공고 + 전북 일자리 비교 에이전트</h1>
          </div>
        </div>

        <ServiceStepIndicator currentStep={loggedIn ? 2 : 1} className="mt-4" />

        <div className="mt-4 space-y-3">
          <DemoModeNotice />
          <LoginStatusBar loggedIn={loggedIn} onLogin={handleLogin} onLogout={handleLogout} />
          {loggedIn && <JobCareProfilePanel />}
        </div>

        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          <div className="rounded-card border border-ink-border bg-surface-muted p-3 text-xs">
            <p className="font-semibold text-ink-900">고용24 AI추천</p>
            <p className="mt-0.5 text-ink-500">사람과 일자리의 적합성을 분석</p>
          </div>
          <div className="rounded-card border border-brand-blue/30 bg-tint-sky/20 p-3 text-xs">
            <p className="font-semibold text-ink-900">지역 선택 보정 에이전트</p>
            <p className="mt-0.5 text-ink-500">수도권과 자기 지역 일자리의 비교 가능성을 분석</p>
          </div>
        </div>
        <div className="mt-2">
          <ServiceDifferentiationNotice />
        </div>

        <p className="mt-4 text-sm leading-relaxed text-ink-500">
          아래 수도권 채용공고 목록에서 관심 있는 공고의 <strong className="text-ink-700">내 지역 비교 공고 보기</strong>를
          누르면, 전북 일자리 비교 에이전트가 직무·고용조건을 기준으로 비교 가능한 전북 공고를 찾아 같은 화면에서
          보여드려요. 추천은 기업 우수성 평가가 아닌 공고 간 비교 결과이며, 확인되지 않은 정보는 추정하지 않습니다.
        </p>

        <div className="mt-6">
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
            <div className="space-y-4">
              <p className="flex items-center gap-1.5 text-xs text-ink-400">
                <ListChecks size={13} aria-hidden="true" />
                {listingState.datasetDescription}
              </p>
              <ul className="space-y-4">
                {listingState.postings.map((posting) => (
                  <CapitalPostingCard
                    key={posting.posting_id}
                    posting={posting}
                    homeRegionLabel={loggedIn ? DEMO_PROFILE.homeRegionLabel : listingState.homeRegion}
                  />
                ))}
              </ul>
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
