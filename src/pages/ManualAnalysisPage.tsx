import { AlertTriangle, ArrowLeft, CheckCircle2, Info, Link2, Loader2, RotateCcw, Sparkles } from 'lucide-react'
import { useId, useState } from 'react'
import { Link } from 'react-router-dom'
import { Container } from '../components/ui/Container'
import { useToast } from '../components/ui/ToastProvider'
import { demoJobPosting, jobCategoryOptions } from '../data/aiJobRecommend'
import { DemoModeNotice } from '../components/ai-job-recommend/DemoModeNotice'
import { JeonbukCandidateList } from '../components/ai-job-recommend/JeonbukCandidateList'
import { PostingAnalysisPanel, type AnalysisState } from '../components/ai-job-recommend/PostingAnalysisPanel'
import { FinanceComparisonPanel } from '../components/ai-job-recommend/FinanceComparisonPanel'
import { GapStatsNotice } from '../components/ai-job-recommend/GapStatsNotice'
import { ApiClientError, analyzePosting, matchPostings, type MatchCandidate } from '../lib/apiClient'
import { errorCodeToMessage } from '../lib/displayLabels'

interface FormState {
  category: string
  body: string
  sourceUrl: string
}

interface FormErrors {
  category?: string
  body?: string
}

type CandidatesState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; candidates: MatchCandidate[]; datasetDescription: string }
  | { status: 'empty' }
  | { status: 'error'; error: ApiClientError }

const initialState: FormState = { category: '', body: '', sourceUrl: '' }

/**
 * Secondary, opt-in path (see TASK section 6): the original manual
 * paste-and-analyze flow, preserved unchanged and fully tested, but no
 * longer the default `/ai-job-recommend` landing experience -- that route
 * now shows the inline "전북 일자리 비교 에이전트" listing
 * (see AiJobRecommendPage.tsx). Reached via "다른 공고 직접 비교" there, or
 * directly at /manual-analysis.
 */
export function ManualAnalysisPage() {
  const { announce } = useToast()
  const [form, setForm] = useState<FormState>(initialState)
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitted, setSubmitted] = useState<FormState | null>(null)

  const [candidatesState, setCandidatesState] = useState<CandidatesState>({ status: 'idle' })
  const [selectedCandidate, setSelectedCandidate] = useState<MatchCandidate | null>(null)
  const [metroAnalysis, setMetroAnalysis] = useState<AnalysisState>({ status: 'idle' })
  const [jeonbukAnalysis, setJeonbukAnalysis] = useState<AnalysisState>({ status: 'idle' })

  const categoryId = useId()
  const categoryListId = useId()
  const bodyId = useId()
  const urlId = useId()

  function resetFlow() {
    setSubmitted(null)
    setCandidatesState({ status: 'idle' })
    setSelectedCandidate(null)
    setMetroAnalysis({ status: 'idle' })
    setJeonbukAnalysis({ status: 'idle' })
  }

  function handleLoadDemo() {
    setForm({ category: demoJobPosting.category, body: demoJobPosting.body, sourceUrl: demoJobPosting.sourceUrl })
    setErrors({})
    resetFlow()
    announce('데모 채용공고를 불러왔어요. 내용을 확인한 뒤 분석하기를 눌러보세요.')
  }

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
        setCandidatesState({
          status: 'error',
          error: err instanceof ApiClientError ? err : new ApiClientError({ code: 'unexpected_response', message: '알 수 없는 오류가 발생했습니다.' }),
        })
      }
    }
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()

    const nextErrors: FormErrors = {}
    if (!form.category.trim()) nextErrors.category = '관심 직종을 입력하거나 목록에서 선택해 주세요.'
    if (!form.body.trim()) nextErrors.body = '채용공고 본문을 입력해 주세요.'
    else if (form.body.trim().length < 20) nextErrors.body = '본문이 너무 짧아요. 채용공고 내용을 조금 더 붙여넣어 주세요.'

    setErrors(nextErrors)

    if (Object.keys(nextErrors).length > 0) {
      announce('입력값을 확인해 주세요.')
      return
    }

    setSubmitted(form)
    setSelectedCandidate(null)
    setMetroAnalysis({ status: 'idle' })
    setJeonbukAnalysis({ status: 'idle' })
    announce('입력하신 공고를 확인했어요. 전북 비교 후보를 찾고 있어요.')
    void fetchCandidates(form.category.trim())
  }

  async function handleSelectCandidate(candidate: MatchCandidate) {
    if (!submitted) return
    setSelectedCandidate(candidate)
    setMetroAnalysis({ status: 'loading' })
    setJeonbukAnalysis({ status: 'loading' })

    // Two independent requests, run in parallel. Neither result is hidden
    // because the other failed -- each panel renders its own settled state.
    const [metroResult, jeonbukResult] = await Promise.allSettled([
      analyzePosting({
        source_text: submitted.body,
        source_url: submitted.sourceUrl || null,
        expected_occupation: submitted.category,
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
      <Container className="max-w-3xl">
        <Link
          to="/ai-job-recommend"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-ink-500 transition hover:text-brand-blue"
        >
          <ArrowLeft size={16} aria-hidden="true" />
          AI추천(일자리) 목록으로
        </Link>

        <div className="mt-4 flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-indigo text-white">
            <Sparkles size={22} aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-bold text-brand-blue">AI추천(일자리) · 직접 비교</p>
            <h1 className="text-xl font-bold text-ink-900 sm:text-2xl">채용공고 직접 붙여넣어 분석 (데모)</h1>
          </div>
        </div>

        <div className="mt-4">
          <DemoModeNotice />
        </div>

        <p className="mt-4 text-sm leading-relaxed text-ink-500">
          수도권 채용공고를 입력하면 같은 직종·고용형태의 전북 비교 후보를 찾고, 두 공고를 6개 항목으로 감사한 뒤
          모호하거나 없는 조건을 확인 질문으로 보여드려요. 이후 입력한 소득·주거비로 자금축적을 비교할 수 있어요.
        </p>

        <div className="mt-6 flex gap-3 rounded-card border border-ink-border bg-surface-muted p-5">
          <Info size={20} aria-hidden="true" className="mt-0.5 shrink-0 text-brand-blue" />
          <div className="text-sm leading-relaxed text-ink-500">
            <p className="font-semibold text-ink-900">현재 MVP에서는 다음 기능이 없습니다.</p>
            <ul className="mt-2 list-inside list-disc space-y-1">
              <li>URL에서 채용공고 자동 수집</li>
              <li>PDF 업로드 및 분석</li>
              <li>민간 채용사이트 자동 스크래핑</li>
            </ul>
            <p className="mt-2">
              출처 URL은 <strong className="text-ink-700">원문 출처를 표시하기 위한 용도로만</strong> 사용되며,
              자동으로 내용을 가져오지 않아요.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} noValidate className="mt-8 space-y-6">
          <div>
            <label htmlFor={categoryId} className="block text-sm font-semibold text-ink-900">
              관심 직종
            </label>
            <input
              id={categoryId}
              list={categoryListId}
              type="text"
              value={form.category}
              onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
              placeholder="예: 생산직(제조 조립원)"
              aria-invalid={Boolean(errors.category)}
              aria-describedby={errors.category ? `${categoryId}-error` : undefined}
              className={`mt-2 w-full rounded-card border bg-white px-4 py-3 text-sm text-ink-900 outline-none transition placeholder:text-ink-400 focus:border-brand-blue ${
                errors.category ? 'border-red-400' : 'border-ink-border'
              }`}
            />
            <datalist id={categoryListId}>
              {jobCategoryOptions.map((option) => (
                <option key={option} value={option} />
              ))}
            </datalist>
            {errors.category && (
              <p id={`${categoryId}-error`} className="mt-1.5 text-xs font-medium text-red-500">
                {errors.category}
              </p>
            )}
          </div>

          <div>
            <label htmlFor={bodyId} className="block text-sm font-semibold text-ink-900">
              채용공고 본문 <span className="font-normal text-ink-400">(수도권 채용공고)</span>
            </label>
            <textarea
              id={bodyId}
              value={form.body}
              onChange={(e) => setForm((f) => ({ ...f, body: e.target.value }))}
              placeholder="수도권 채용공고 본문을 직접 붙여넣어 주세요."
              rows={10}
              aria-invalid={Boolean(errors.body)}
              aria-describedby={errors.body ? `${bodyId}-error` : undefined}
              className={`mt-2 w-full resize-y rounded-card border bg-white px-4 py-3 text-sm leading-relaxed text-ink-900 outline-none transition placeholder:text-ink-400 focus:border-brand-blue ${
                errors.body ? 'border-red-400' : 'border-ink-border'
              }`}
            />
            {errors.body && (
              <p id={`${bodyId}-error`} className="mt-1.5 text-xs font-medium text-red-500">
                {errors.body}
              </p>
            )}
          </div>

          <div>
            <label htmlFor={urlId} className="block text-sm font-semibold text-ink-900">
              원문 출처 URL <span className="font-normal text-ink-400">(선택 입력)</span>
            </label>
            <div className="mt-2 flex items-center gap-2 rounded-card border border-ink-border bg-white px-4 py-3 focus-within:border-brand-blue">
              <Link2 size={16} aria-hidden="true" className="shrink-0 text-ink-400" />
              <input
                id={urlId}
                type="url"
                value={form.sourceUrl}
                onChange={(e) => setForm((f) => ({ ...f, sourceUrl: e.target.value }))}
                placeholder="https://example.com/notice/12345"
                className="w-full min-w-0 bg-transparent text-sm text-ink-900 outline-none placeholder:text-ink-400"
              />
            </div>
          </div>

          <div className="flex flex-col-reverse gap-3 sm:flex-row">
            <button
              type="button"
              onClick={handleLoadDemo}
              className="rounded-pill border border-ink-border bg-white px-5 py-3 text-sm font-semibold text-ink-700 transition hover:border-brand-blue hover:text-brand-blue active:scale-95"
            >
              데모 공고 불러오기
            </button>
            <button
              type="submit"
              className="rounded-pill bg-brand-blue px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-blue-dark active:scale-95"
            >
              공고 분석하기
            </button>
          </div>
        </form>

        {submitted && (
          <div className="mt-8 space-y-6">
            <div role="status" aria-live="polite" className="rounded-card border border-ink-border bg-tint-mint/40 p-6">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={20} aria-hidden="true" className="text-brand-green" />
                  <p className="font-semibold text-ink-900">입력 내용을 확인했어요</p>
                </div>
                <button
                  type="button"
                  onClick={resetFlow}
                  className="flex items-center gap-1 text-xs font-medium text-ink-500 hover:text-brand-blue"
                >
                  <RotateCcw size={13} aria-hidden="true" />
                  처음부터 다시
                </button>
              </div>
              <dl className="mt-4 space-y-3 text-sm">
                <div>
                  <dt className="font-medium text-ink-500">관심 직종</dt>
                  <dd className="mt-0.5 text-ink-900">{submitted.category}</dd>
                </div>
              </dl>
            </div>

            <section aria-labelledby="candidates-heading" className="space-y-3">
              <h2 id="candidates-heading" className="text-lg font-bold text-ink-900">
                전북 비교 후보
              </h2>

              {candidatesState.status === 'loading' && (
                <p className="flex items-center gap-2 text-sm text-ink-500">
                  <Loader2 size={16} aria-hidden="true" className="animate-spin" />
                  전북 비교 후보를 찾고 있어요...
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

            {selectedCandidate && (
              <section aria-labelledby="analysis-heading" className="space-y-3">
                <h2 id="analysis-heading" className="text-lg font-bold text-ink-900">
                  6개 항목 분석
                </h2>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <PostingAnalysisPanel title="수도권 공고" state={metroAnalysis} />
                  <PostingAnalysisPanel
                    title={`전북 후보 (${selectedCandidate.company_name ?? selectedCandidate.posting_id})`}
                    state={jeonbukAnalysis}
                  />
                </div>
                <GapStatsNotice />
              </section>
            )}

            {analysisSettled && (
              <section aria-labelledby="finance-heading" className="space-y-3">
                <h2 id="finance-heading" className="text-lg font-bold text-ink-900">
                  자금축적 비교
                </h2>
                <FinanceComparisonPanel />
              </section>
            )}
          </div>
        )}
      </Container>
    </div>
  )
}

function toApiClientError(reason: unknown): ApiClientError {
  if (reason instanceof ApiClientError) return reason
  return new ApiClientError({ code: 'unexpected_response', message: '알 수 없는 오류가 발생했습니다.' })
}
