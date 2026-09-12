import { Keyboard, Search } from 'lucide-react'
import { useId, useState } from 'react'
import { Container } from '../ui/Container'
import { useToast } from '../ui/ToastProvider'
import { popularKeywords, searchScopes } from '../../data/content'

export function HeroSearch() {
  const { announce } = useToast()
  const [scope, setScope] = useState(searchScopes[0]!.id)
  const [query, setQuery] = useState('')
  const inputId = useId()
  const scopeId = useId()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const scopeLabel = searchScopes.find((s) => s.id === scope)?.label ?? '전체'
    if (!query.trim()) {
      announce('검색어를 입력해 주세요.')
      return
    }
    announce(`[${scopeLabel}] '${query.trim()}' 검색 결과 (Mock) — 실제 검색은 연결되어 있지 않아요.`)
  }

  function handleKeyword(keyword: string) {
    setQuery(keyword)
    announce(`[전체] '${keyword}' 검색 결과 (Mock) — 실제 검색은 연결되어 있지 않아요.`)
  }

  return (
    <section
      aria-labelledby="hero-search-heading"
      className="relative overflow-hidden bg-gradient-to-b from-white via-tint-lavender/40 to-white py-14 sm:py-16"
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -left-24 top-0 h-72 w-72 rounded-full bg-tint-lavender/60 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-16 top-10 h-64 w-64 rounded-full bg-tint-sky/60 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/3 top-24 h-56 w-56 rounded-full bg-tint-mint/50 blur-3xl"
      />

      <Container className="relative">
        <h1 id="hero-search-heading" className="text-center text-2xl font-bold text-ink-900 sm:text-3xl">
          나만의 고용서비스, <span className="text-brand-blue">고용24</span>
        </h1>

        <form
          onSubmit={handleSubmit}
          className="mx-auto mt-7 flex max-w-3xl items-stretch rounded-pill border-2 border-brand-blue bg-white shadow-soft"
        >
          <label htmlFor={scopeId} className="sr-only">
            검색 범위 선택
          </label>
          <select
            id={scopeId}
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            className="rounded-l-pill bg-transparent pl-5 pr-2 text-sm font-medium text-ink-900 outline-none"
          >
            {searchScopes.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>

          <span className="my-2.5 w-px bg-ink-border" aria-hidden="true" />

          <label htmlFor={inputId} className="sr-only">
            통합검색어 입력
          </label>
          <input
            id={inputId}
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="필요한 서비스를 검색해보세요"
            className="min-w-0 flex-1 bg-transparent px-4 text-sm text-ink-900 outline-none placeholder:text-ink-400"
          />

          <button
            type="button"
            onClick={() => announce('보안 가상 키보드는 데모에서 지원하지 않아요.')}
            aria-label="보안 가상 키보드 열기"
            className="flex w-11 shrink-0 items-center justify-center text-ink-400 transition hover:text-brand-blue"
          >
            <Keyboard size={18} aria-hidden="true" />
          </button>

          <button
            type="submit"
            aria-label="통합검색 실행"
            className="flex w-14 shrink-0 items-center justify-center rounded-r-pill bg-brand-blue text-white transition hover:bg-brand-blue-dark active:scale-95"
          >
            <Search size={20} aria-hidden="true" />
          </button>
        </form>

        <div className="mx-auto mt-4 flex max-w-3xl flex-wrap items-center justify-center gap-2">
          <span className="text-xs font-medium text-ink-400">많이 찾은 검색어</span>
          {popularKeywords.map((keyword) => (
            <button
              key={keyword}
              type="button"
              onClick={() => handleKeyword(keyword)}
              className="rounded-pill border border-ink-border bg-white px-3 py-1 text-xs text-ink-500 transition hover:border-brand-blue hover:text-brand-blue active:scale-95"
            >
              {keyword}
            </button>
          ))}
        </div>
      </Container>
    </section>
  )
}
