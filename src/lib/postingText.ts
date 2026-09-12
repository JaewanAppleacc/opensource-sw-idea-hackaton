/**
 * Small, deterministic text helpers for summarizing a posting's raw text on
 * list/card UI (e.g. "임금 정보" on a Jeonbuk candidate card).
 *
 * These are NOT the six-field audit (that comes from the backend's
 * evidence-validated `analyzePosting` call). They only extract a short,
 * literal mention for a compact card -- if nothing matches, callers must
 * show an honest "공고 본문에서 확인 필요" state rather than guessing.
 */

const SALARY_PATTERNS = [
  /월급\s*[\d,]+\s*만?\s*원[^.]*/,
  /급여는?\s*[^.]*원[^.]*/,
  /연봉\s*[\d,]+\s*만?\s*원[^.]*/,
]

export function extractSalaryMention(text: string | null | undefined): string | null {
  if (!text) return null
  for (const pattern of SALARY_PATTERNS) {
    const match = text.match(pattern)
    if (match) return match[0].trim()
  }
  return null
}

const CONDITION_PATTERNS = [/경력[^.]*/, /학력[^.]*/, /[^.]*우대[^.]*/]

export function extractConditionMention(text: string | null | undefined): string | null {
  if (!text) return null
  for (const pattern of CONDITION_PATTERNS) {
    const match = text.match(pattern)
    if (match) return match[0].trim()
  }
  return null
}

/**
 * Converts backend `matching_fields` (from MatchCandidate) into fact-based
 * Korean phrases only -- never a subjective quality claim. Per TASK section
 * 5: allowed phrasing is things like "동일한 제조·조립 직무" or "동일한 정규직
 * 고용형태"; never a score or a "better than" comparison.
 */
export function matchingFieldsToReasons(candidate: {
  occupation: string
  employment_type: string
  matching_fields: string[]
}): string[] {
  const reasons: string[] = []
  if (candidate.matching_fields.includes('occupation')) {
    reasons.push(`동일한 직무 (${candidate.occupation})`)
  }
  if (candidate.matching_fields.includes('employment_type')) {
    reasons.push(`동일한 ${candidate.employment_type} 고용형태`)
  }
  return reasons
}
