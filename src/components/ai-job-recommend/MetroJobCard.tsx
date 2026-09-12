import { ChevronDown, ChevronUp, ExternalLink, MapPin } from 'lucide-react'
import { useState } from 'react'
import type { MetroJobListing } from '../../data/metroJobListings'

interface MetroJobCardProps {
  listing: MetroJobListing
  isActive: boolean
  onCompareRegion: (listing: MetroJobListing) => void
}

/**
 * A single AI추천(일자리) list card for a metropolitan-area posting. Mirrors
 * the info a real 고용24 AI추천 채용공고 card shows (TASK section 4): company,
 * title, region, employment type, wage, experience/education condition,
 * source, and a link to view the original text -- plus the entry point into
 * the Jeonbuk comparison agent.
 */
export function MetroJobCard({ listing, isActive, onCompareRegion }: MetroJobCardProps) {
  const [showFullText, setShowFullText] = useState(false)

  return (
    <li
      className={`rounded-card border bg-white p-5 transition ${
        isActive ? 'border-brand-blue ring-1 ring-brand-blue' : 'border-ink-border'
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold text-brand-blue">{listing.companyName}</p>
          <h3 className="mt-1 text-base font-bold text-ink-900">{listing.title}</h3>
          <p className="mt-1.5 flex items-center gap-1 text-xs text-ink-500">
            <MapPin size={12} aria-hidden="true" />
            {listing.region} · {listing.employmentType}
          </p>
        </div>
        <span className="rounded-pill bg-surface-muted px-2.5 py-1 text-[11px] font-medium text-ink-500">
          출처: {listing.sourceName === 'synthetic_fixture_v1' ? '합성 데모 데이터' : listing.sourceName}
        </span>
      </div>

      <dl className="mt-4 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs font-medium text-ink-500">임금 정보</dt>
          <dd className="mt-0.5 text-ink-900">{listing.salaryText ?? '공고 본문에서 확인 필요'}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-ink-500">경력·학력 조건</dt>
          <dd className="mt-0.5 text-ink-900">{listing.conditionText ?? '명시되지 않음'}</dd>
        </div>
      </dl>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => setShowFullText((v) => !v)}
          className="flex items-center gap-1 text-xs font-semibold text-ink-500 hover:text-brand-blue"
          aria-expanded={showFullText}
        >
          {showFullText ? <ChevronUp size={14} aria-hidden="true" /> : <ChevronDown size={14} aria-hidden="true" />}
          원문 보기
        </button>
        {listing.sourceUrl && (
          <a
            href={listing.sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 text-xs font-semibold text-ink-500 hover:text-brand-blue"
          >
            <ExternalLink size={13} aria-hidden="true" />
            출처 링크
          </a>
        )}
      </div>

      {showFullText && (
        <p className="mt-3 rounded-card bg-surface-muted p-3 text-xs leading-relaxed text-ink-700">{listing.fullText}</p>
      )}

      <div className="mt-4 border-t border-ink-border pt-4">
        <button
          type="button"
          onClick={() => onCompareRegion(listing)}
          aria-pressed={isActive}
          className={`w-full rounded-pill px-5 py-2.5 text-sm font-semibold transition active:scale-95 sm:w-auto ${
            isActive
              ? 'bg-brand-blue text-white'
              : 'border border-brand-blue text-brand-blue hover:bg-tint-sky/40'
          }`}
        >
          내 지역 유사 일자리 보기
        </button>
        <p className="mt-1.5 text-[11px] text-ink-400">전북특별자치도 기준</p>
      </div>
    </li>
  )
}
