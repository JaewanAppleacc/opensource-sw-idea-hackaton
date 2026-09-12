import { CheckCircle2, ChevronDown, ChevronUp, MapPin } from 'lucide-react'
import { useState } from 'react'
import type { MatchCandidate } from '../../lib/apiClient'
import { extractSalaryMention, matchingFieldsToReasons } from '../../lib/postingText'

interface JeonbukCandidateListProps {
  candidates: MatchCandidate[]
  datasetDescription: string
  selectedPostingId: string | null
  onSelect: (candidate: MatchCandidate) => void
}

function CandidateCard({
  candidate,
  isSelected,
  onSelect,
}: {
  candidate: MatchCandidate
  isSelected: boolean
  onSelect: (candidate: MatchCandidate) => void
}) {
  const [showFullText, setShowFullText] = useState(false)
  const reasons = matchingFieldsToReasons(candidate)
  const salary = extractSalaryMention(candidate.source_text)

  return (
    <li className={`rounded-card border p-4 ${isSelected ? 'border-brand-blue bg-tint-sky/20 ring-1 ring-brand-blue' : 'border-ink-border bg-white'}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-ink-900">{candidate.company_name ?? candidate.posting_id}</p>
          <p className="mt-0.5 text-sm text-ink-700">{candidate.occupation} 채용</p>
          <p className="mt-1 flex items-center gap-1 text-xs text-ink-500">
            <MapPin size={12} aria-hidden="true" />
            {candidate.municipality ?? candidate.region} · {candidate.employment_type}
          </p>
        </div>
        {isSelected && <CheckCircle2 size={20} aria-hidden="true" className="shrink-0 text-brand-blue" />}
      </div>

      <p className="mt-2 text-sm text-ink-900">임금: {salary ?? '공고 본문에서 확인 필요'}</p>

      {reasons.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {reasons.map((reason) => (
            <span key={reason} className="rounded-pill bg-tint-mint/60 px-2 py-0.5 text-[11px] font-medium text-brand-green">
              {reason}
            </span>
          ))}
        </div>
      )}

      {candidate.is_synthetic && (
        <p className="mt-2 text-[11px] text-ink-400">합성 데모 데이터 · {candidate.description}</p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-ink-border pt-3">
        {candidate.source_text && (
          <button
            type="button"
            onClick={() => setShowFullText((v) => !v)}
            aria-expanded={showFullText}
            className="flex items-center gap-1 text-xs font-semibold text-ink-500 hover:text-brand-blue"
          >
            {showFullText ? <ChevronUp size={14} aria-hidden="true" /> : <ChevronDown size={14} aria-hidden="true" />}
            원문 보기
          </button>
        )}
        <button
          type="button"
          onClick={() => onSelect(candidate)}
          aria-pressed={isSelected}
          className={`ml-auto rounded-pill px-4 py-2 text-xs font-semibold transition active:scale-95 ${
            isSelected ? 'bg-brand-blue text-white' : 'border border-brand-blue text-brand-blue hover:bg-tint-sky/40'
          }`}
        >
          비교하기
        </button>
      </div>

      {showFullText && candidate.source_text && (
        <p className="mt-3 rounded-card bg-surface-muted p-3 text-xs leading-relaxed text-ink-700">{candidate.source_text}</p>
      )}
      {!candidate.source_text && (
        <p className="mt-2 text-[11px] text-ink-400">이 후보는 원문을 표시할 수 없습니다 (재배포 권한 미확인).</p>
      )}
    </li>
  )
}

/**
 * "내 지역 비교 에이전트가 찾은 전북 일자리" panel (TASK section 5). Every
 * candidate here comes from the backend's POST /postings/match response --
 * no candidate is invented client-side. Matching reasons are derived only
 * from the backend's `matching_fields` (fact-based phrasing only, never a
 * quality score).
 */
export function JeonbukCandidateList({
  candidates,
  datasetDescription,
  selectedPostingId,
  onSelect,
}: JeonbukCandidateListProps) {
  return (
    <div className="rounded-card border border-ink-border bg-tint-mint/10 p-5">
      <h3 className="text-base font-bold text-ink-900">내 지역 비교 에이전트가 찾은 전북 일자리</h3>
      <p className="mt-1 text-sm text-ink-500">
        직무와 고용조건을 기준으로 비교했습니다. 공고에 없는 정보는 추정하지 않습니다.
      </p>
      <p className="mt-2 text-xs text-ink-400">{datasetDescription}</p>
      <ul className="mt-4 space-y-3">
        {candidates.slice(0, 3).map((candidate) => (
          <CandidateCard
            key={candidate.posting_id}
            candidate={candidate}
            isSelected={candidate.posting_id === selectedPostingId}
            onSelect={onSelect}
          />
        ))}
      </ul>
    </div>
  )
}
