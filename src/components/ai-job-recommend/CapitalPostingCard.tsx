import { Building2, CheckCircle2, ExternalLink, MapPin } from 'lucide-react'
import type { PostingListItem } from '../../lib/apiClient'

interface CapitalPostingCardProps {
  posting: PostingListItem
  isSelected: boolean
  onSelect: (posting: PostingListItem) => void
}

/**
 * One row in the 수도권 추천 공고 목록 -- a real-job-board-style compact
 * row, not a self-contained card with its own embedded comparison panel
 * (TASK "UI 고도화" section 8). Selecting a row drives the single
 * right-hand comparison panel rendered by the page; this component holds
 * no comparison state of its own.
 */
export function CapitalPostingCard({ posting, isSelected, onSelect }: CapitalPostingCardProps) {
  return (
    <li>
      <button
        type="button"
        onClick={() => onSelect(posting)}
        aria-pressed={isSelected}
        className={`flex w-full items-start justify-between gap-3 border-l-[3px] px-4 py-3.5 text-left transition-colors duration-150 ${
          isSelected ? 'border-brand-blue bg-tint-sky/15' : 'border-transparent hover:bg-surface-muted'
        }`}
      >
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 font-semibold text-ink-900">
            <Building2 size={15} aria-hidden="true" className="shrink-0 text-ink-400" />
            <span className="truncate">{posting.company_name ?? posting.posting_id}</span>
          </p>
          <p className="mt-1 truncate text-sm text-ink-600">{posting.occupation}</p>
          <p className="mt-0.5 flex flex-wrap items-center gap-x-1.5 text-xs text-ink-400">
            <span className="flex items-center gap-1">
              <MapPin size={11} aria-hidden="true" />
              {posting.municipality ?? posting.region}
            </span>
            <span>· {posting.employment_type}</span>
            {posting.collection_date && <span>· 수집 {posting.collection_date}</span>}
            {posting.source_url && (
              <a
                href={posting.source_url}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="flex items-center gap-0.5 text-brand-blue hover:underline"
              >
                <ExternalLink size={10} aria-hidden="true" />
                원문
              </a>
            )}
          </p>
        </div>
        <span
          className={`mt-0.5 flex shrink-0 items-center gap-1 rounded-pill px-2.5 py-1 text-[11px] font-semibold transition-colors duration-150 ${
            isSelected ? 'bg-brand-blue text-white' : 'border border-ink-border text-ink-500'
          }`}
        >
          {isSelected && <CheckCircle2 size={12} aria-hidden="true" />}
          지역 비교
        </span>
      </button>
    </li>
  )
}
