import { Building2, ExternalLink, MapPin } from 'lucide-react'
import type { PostingListItem } from '../../lib/apiClient'
import { InlineJeonbukAgentPanel } from './InlineJeonbukAgentPanel'

interface CapitalPostingCardProps {
  posting: PostingListItem
  homeRegionLabel: string
}

export function CapitalPostingCard({ posting, homeRegionLabel }: CapitalPostingCardProps) {
  return (
    <li className="rounded-card border border-ink-border bg-white p-5 shadow-softer">
      <div className="flex items-start justify-between gap-3">
        <div>
          <span className="inline-block rounded-pill bg-surface-muted px-2 py-0.5 text-[11px] font-semibold text-ink-500">
            수도권 공고
          </span>
          <p className="mt-2 flex items-center gap-1.5 font-bold text-ink-900">
            <Building2 size={16} aria-hidden="true" className="shrink-0 text-ink-400" />
            {posting.company_name ?? posting.posting_id}
          </p>
          <p className="mt-1 flex items-center gap-1 text-xs text-ink-500">
            <MapPin size={12} aria-hidden="true" />
            {posting.municipality ?? posting.region} · {posting.occupation} · {posting.employment_type}
          </p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-3 text-[11px] text-ink-400">
        {posting.collection_date && <span>수집 기준일 {posting.collection_date}</span>}
        {posting.source_url && (
          <a
            href={posting.source_url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 text-brand-blue hover:underline"
          >
            <ExternalLink size={11} aria-hidden="true" />
            원문 보기
          </a>
        )}
      </div>

      <InlineJeonbukAgentPanel metroPosting={posting} homeRegionLabel={homeRegionLabel} />
    </li>
  )
}
