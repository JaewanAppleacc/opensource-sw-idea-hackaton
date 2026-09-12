import { ArrowLeft, CheckCircle2, Info, Link2, Sparkles } from 'lucide-react'
import { useId, useState } from 'react'
import { Link } from 'react-router-dom'
import { Container } from '../components/ui/Container'
import { useToast } from '../components/ui/ToastProvider'
import { demoJobPosting, jobCategoryOptions } from '../data/aiJobRecommend'

interface FormState {
  category: string
  body: string
  sourceUrl: string
}

interface FormErrors {
  category?: string
  body?: string
}

const initialState: FormState = { category: '', body: '', sourceUrl: '' }

export function AiJobRecommendPage() {
  const { announce } = useToast()
  const [form, setForm] = useState<FormState>(initialState)
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitted, setSubmitted] = useState<FormState | null>(null)

  const categoryId = useId()
  const categoryListId = useId()
  const bodyId = useId()
  const urlId = useId()

  function handleLoadDemo() {
    setForm({ category: demoJobPosting.category, body: demoJobPosting.body, sourceUrl: demoJobPosting.sourceUrl })
    setErrors({})
    setSubmitted(null)
    announce('데모 채용공고를 불러왔어요. 내용을 확인한 뒤 분석하기를 눌러보세요.')
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
    announce('입력하신 공고를 확인했어요. 실제 분석 결과 화면은 다음 단계에서 연결될 예정입니다. (데모)')
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
            <h1 className="text-xl font-bold text-ink-900 sm:text-2xl">채용공고 AI 분석 (데모)</h1>
          </div>
        </div>

        <p className="mt-4 text-sm leading-relaxed text-ink-500">
          관심 직종과 수도권 채용공고 본문을 입력하면, 이후 단계에서 AI가 공고 내용을 분석해 맞춤 정보를 제공할
          예정이에요. 이 화면은 그 첫 번째 단계인 <strong className="text-ink-700">입력 화면</strong>입니다.
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
          <div
            role="status"
            aria-live="polite"
            className="mt-8 rounded-card border border-ink-border bg-tint-mint/40 p-6"
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 size={20} aria-hidden="true" className="text-brand-green" />
              <p className="font-semibold text-ink-900">입력 내용을 확인했어요</p>
            </div>
            <dl className="mt-4 space-y-3 text-sm">
              <div>
                <dt className="font-medium text-ink-500">관심 직종</dt>
                <dd className="mt-0.5 text-ink-900">{submitted.category}</dd>
              </div>
              <div>
                <dt className="font-medium text-ink-500">채용공고 본문</dt>
                <dd className="mt-0.5 whitespace-pre-line text-ink-700">{submitted.body}</dd>
              </div>
              {submitted.sourceUrl && (
                <div>
                  <dt className="font-medium text-ink-500">원문 출처</dt>
                  <dd className="mt-0.5 break-all text-brand-blue">{submitted.sourceUrl}</dd>
                </div>
              )}
            </dl>
            <p className="mt-4 text-xs text-ink-400">
              이 데모는 입력 화면(화면 1)까지만 구현되어 있어요. 실제 AI 분석 결과 화면은 다음 단계에서 연결될
              예정입니다.
            </p>
          </div>
        )}
      </Container>
    </div>
  )
}
