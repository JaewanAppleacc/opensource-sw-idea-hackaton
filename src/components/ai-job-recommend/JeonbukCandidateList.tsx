import { Circle, CheckCircle2 } from 'lucide-react'
import type { MatchCandidate } from '../../lib/apiClient'

interface JeonbukCandidateListProps {
  candidates: MatchCandidate[]
  selectedPostingId: string | null
  onSelect: (candidate: MatchCandidate) => void
}

/**
 * Compact radio-style list of up to three home-region candidates (TASK "UI
 * 고도화" section 9) -- no nested card chrome, no repeated matching-field
 * pill soup. The English `dataset_description` from the backend response is
 * intentionally never rendered here; the caller shows one short Korean
 * caption instead.
 */
export function JeonbukCandidateList({ candidates, selectedPostingId, onSelect }: JeonbukCandidateListProps) {
  return (
    <ul className="divide-y divide-ink-border overflow-hidden rounded-card border border-ink-border">
      {candidates.map((candidate, index) => {
        const isSelected = candidate.posting_id === selectedPostingId
        return (
          <li key={candidate.posting_id} className="candidate-stagger-in" style={{ animationDelay: `${index * 50}ms` }}>
            <button
              type="button"
              onClick={() => onSelect(candidate)}
              aria-pressed={isSelected}
              className={`flex w-full items-start gap-2.5 px-3.5 py-3 text-left transition-colors duration-150 ${
                isSelected ? 'bg-tint-sky/20' : 'hover:bg-surface-muted'
              }`}
            >
              {isSelected ? (
                <CheckCircle2 size={16} aria-hidden="true" className="mt-0.5 shrink-0 text-brand-blue" />
              ) : (
                <Circle size={16} aria-hidden="true" className="mt-0.5 shrink-0 text-ink-border" />
              )}
              <span className="min-w-0">
                <span className="flex items-center gap-1.5">
                  <span className="truncate font-semibold text-ink-900">
                    {candidate.company_name ?? candidate.posting_id}
                  </span>
                  {candidate.is_synthetic && (
                    <span className="shrink-0 text-[10px] font-medium text-ink-400">(합성 데모 데이터)</span>
                  )}
                </span>
                <span className="mt-0.5 block truncate text-xs text-ink-500">
                  {candidate.municipality ?? candidate.region} · {candidate.occupation} · {candidate.employment_type}
                </span>
              </span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
