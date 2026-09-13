import { Building2, MapPin } from 'lucide-react'
import type { MatchCandidate, PostingListItem } from '../../../lib/apiClient'

interface ReportTargetStepProps {
  metroPosting: PostingListItem
  jeonbukCandidate: MatchCandidate
  metroLabel: string
  jeonbukLabel: string
}

function TargetCard({
  label,
  companyName,
  occupation,
  employmentType,
  place,
  accent,
}: {
  label: string
  companyName: string
  occupation: string
  employmentType: string
  place: string
  accent: boolean
}) {
  return (
    <div
      className={`flex-1 rounded-card border p-4 ${accent ? 'border-brand-blue bg-tint-sky/10' : 'border-ink-border bg-white'}`}
    >
      <p className="text-[11px] font-semibold text-ink-400">{label}</p>
      <p className="mt-1.5 flex items-center gap-1.5 text-base font-bold text-ink-900">
        <Building2 size={16} aria-hidden="true" className="shrink-0 text-ink-400" />
        {companyName}
      </p>
      <p className="mt-1 flex items-center gap-1 text-xs text-ink-500">
        <MapPin size={11} aria-hidden="true" />
        {place}
      </p>
      <p className="mt-2 text-xs text-ink-700">{occupation}</p>
      <p className="mt-0.5 text-xs text-ink-500">{employmentType}</p>
    </div>
  )
}

/**
 * Report step 1/6 -- "두 공고를 같은 기준으로 살펴봤어요". Never computes or
 * shows a winner, a recommendation score, or a similarity score: this step
 * only restates the two postings' own metadata, plus the one honest fact
 * about why they're being compared at all (same normalized occupation +
 * employment type group -- never "best match").
 */
export function ReportTargetStep({ metroPosting, jeonbukCandidate, metroLabel, jeonbukLabel }: ReportTargetStepProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row">
        <TargetCard
          label={metroLabel}
          companyName={metroPosting.company_name ?? metroPosting.posting_id}
          occupation={metroPosting.occupation}
          employmentType={metroPosting.employment_type}
          place={metroPosting.municipality ?? metroPosting.region}
          accent={false}
        />
        <TargetCard
          label={jeonbukLabel}
          companyName={jeonbukCandidate.company_name ?? jeonbukCandidate.posting_id}
          occupation={jeonbukCandidate.occupation}
          employmentType={jeonbukCandidate.employment_type}
          place={jeonbukCandidate.municipality ?? jeonbukCandidate.region}
          accent
        />
      </div>
      <p className="rounded-pill bg-surface-muted px-3 py-1.5 text-center text-xs font-medium text-ink-500">
        동일 모집직종·고용형태 그룹의 비교 공고
      </p>
    </div>
  )
}
