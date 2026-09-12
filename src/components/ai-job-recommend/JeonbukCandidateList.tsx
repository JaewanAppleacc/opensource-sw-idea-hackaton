import { CheckCircle2, MapPin, Link2, ListFilter } from 'lucide-react'
import type { MatchCandidate } from '../../lib/apiClient'
import { matchReasonLabel } from '../../lib/displayLabels'

interface JeonbukCandidateListProps {
  candidates: MatchCandidate[]
  datasetDescription: string
  selectedPostingId: string | null
  onSelect: (candidate: MatchCandidate) => void
}

export function JeonbukCandidateList({
  candidates,
  datasetDescription,
  selectedPostingId,
  onSelect,
}: JeonbukCandidateListProps) {
  return (
    <div className="space-y-3">
      <p className="text-xs text-ink-400">{datasetDescription}</p>
      <ul className="space-y-3">
        {candidates.map((candidate) => {
          const isSelected = candidate.posting_id === selectedPostingId
          return (
            <li key={candidate.posting_id}>
              <button
                type="button"
                onClick={() => onSelect(candidate)}
                aria-pressed={isSelected}
                className={`w-full rounded-card border p-4 text-left transition ${
                  isSelected
                    ? 'border-brand-blue bg-tint-sky/30 ring-1 ring-brand-blue'
                    : 'border-ink-border bg-white hover:border-brand-blue'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-ink-900">{candidate.company_name ?? candidate.posting_id}</p>
                    <p className="mt-1 flex items-center gap-1 text-xs text-ink-500">
                      <MapPin size={12} aria-hidden="true" />
                      {candidate.municipality ?? candidate.region} · {candidate.occupation} · {candidate.employment_type}
                    </p>
                  </div>
                  {isSelected && <CheckCircle2 size={20} aria-hidden="true" className="shrink-0 text-brand-blue" />}
                </div>

                {/* 영역 A: 비교 대상으로 연결된 기준 -- 현재 실제로 후보
                    연결에 사용한 정보만 표시한다 (모집직종, 고용형태). 담당
                    업무·기술·급여 등은 연결에 쓰이지 않았으므로 여기 넣지
                    않는다 (TASK "데모 매칭 표현 정직화" section 6). */}
                <div className="mt-3 rounded-card bg-surface-muted p-2.5">
                  <p className="flex items-center gap-1 text-[11px] font-semibold text-ink-500">
                    <ListFilter size={11} aria-hidden="true" />
                    비교 대상으로 연결된 기준
                  </p>
                  <ul className="mt-1 space-y-0.5 text-[11px] text-ink-700">
                    <li>모집직종: {candidate.occupation}</li>
                    <li>고용형태: {candidate.employment_type}</li>
                  </ul>
                </div>

                <div className="mt-2 flex flex-wrap gap-1.5">
                  {candidate.matching_fields.map((field) => (
                    <span
                      key={field}
                      className="rounded-pill bg-tint-mint/60 px-2 py-0.5 text-[11px] font-medium text-brand-green"
                    >
                      {matchReasonLabel(field)}
                    </span>
                  ))}
                  {candidate.mismatch_fields.map((field) => (
                    <span
                      key={field}
                      className="rounded-pill bg-surface-muted px-2 py-0.5 text-[11px] font-medium text-ink-500"
                    >
                      {matchReasonLabel(field)} 다름
                    </span>
                  ))}
                  {candidate.is_synthetic && (
                    <span className="rounded-pill bg-surface-muted px-2 py-0.5 text-[11px] font-medium text-ink-500">
                      합성 데모 데이터
                    </span>
                  )}
                </div>

                {candidate.source_url && (
                  <p className="mt-2 flex items-center gap-1 truncate text-[11px] text-ink-400">
                    <Link2 size={11} aria-hidden="true" className="shrink-0" />
                    {candidate.source_url}
                  </p>
                )}
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
