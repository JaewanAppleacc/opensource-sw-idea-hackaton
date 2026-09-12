/**
 * Presentation-only remapping of the backend's six atomic audited fields
 * into the six user-facing comparison axes. This file never talks to the
 * backend and never invents a status, evidence, or verification action --
 * it only regroups what `PostingAnalysis.fields` already contains, per
 * TASK section 3 & 4 ("기존 원자 필드 분석 결과 → presentation mapper →
 * 근거 기반 6개 비교축"). The backend contract (PostingAnalysis, AuditedField,
 * FieldName, FieldStatus) is completely unchanged.
 *
 * Some sub-items (근로시간·교대제·통근, 복지·기숙사·통근지원) have no backing
 * atomic field at all in the current pipeline -- the mock/real provider
 * never extracts this information. These are never mis-labeled as the
 * backend's `absent` status (that would wrongly imply "this posting failed
 * to state it," when the truth is "this MVP's analysis doesn't check for
 * it at all"). Instead they carry a UI-only `not_evaluated` display status
 * that is never counted as a posting gap: `buildPriorityUnresolvedList`
 * (src/lib/priorityUnresolved.ts) only ever matches `'vague' | 'absent'`,
 * so `not_evaluated` items are structurally excluded from "미확인 정보
 * 우선순위", from any absent-count, and from any posting-quality judgment.
 */
import type { AuditedField, FieldName, FieldStatus, PostingAnalysis, VerificationAction } from './apiClient'

/** `FieldStatus` is the backend's closed three-value enum and must never
 * gain a fourth value (see CLAUDE.md: no `external_verified`, ever). This
 * adds a UI-only fourth state purely for axes/sub-items that have no
 * backing atomic field -- it never appears in any backend contract type. */
export type AxisDisplayStatus = FieldStatus | 'not_evaluated'

export const NOT_EVALUATED_LABEL = '현재 MVP 분석 미지원'

export type AxisId =
  | 'compensation'
  | 'employment_stability'
  | 'duties_fit'
  | 'skills_requirements'
  | 'work_conditions'
  | 'growth_benefits'

export const AXIS_ORDER: AxisId[] = [
  'compensation',
  'employment_stability',
  'duties_fit',
  'skills_requirements',
  'work_conditions',
  'growth_benefits',
]

export const DEFAULT_SELECTED_AXES: AxisId[] = ['compensation', 'employment_stability', 'work_conditions']

export const AXIS_LABELS: Record<AxisId, string> = {
  compensation: '임금·보상',
  employment_stability: '고용안정성',
  duties_fit: '담당 업무와 직무 적합성',
  skills_requirements: '필요 역량과 지원조건',
  work_conditions: '근로시간과 근무환경',
  growth_benefits: '성장·복지 지원',
}

export const AXIS_SUBITEM_HINTS: Record<AxisId, string> = {
  compensation: '연봉/월급, 상여금·수당, 수습 중 급여, 식비·교통비 등 금전적 지원',
  employment_stability: '정규직·계약직, 계약기간, 수습기간, 정규직 전환조건',
  duties_fit: '실제 수행 업무, 담당 공정·제품·서비스, 업무 범위의 구체성',
  skills_requirements: '기술·도구·자격증·경력·학력, 필수·우대조건',
  work_conditions: '출퇴근 시간, 주당 근로시간, 교대제, 야간·휴일근무, 근무장소, 차량 필요 여부, 통근버스',
  growth_benefits: 'OJT·멘토링·직무교육·자격증 지원 (기숙사·통근지원 등 복지는 현재 MVP 분석 범위 밖)',
}

export const WORK_CONDITIONS_UNSUPPORTED_MESSAGE =
  '근로시간·교대제·통근지원은 현재 MVP의 자동 분석 범위에 포함되지 않습니다.'

export const WELFARE_UNSUPPORTED_MESSAGE =
  '기숙사·식사 제공·통근지원 등 복지 정보는 현재 MVP의 자동 분석 범위에 포함되지 않습니다.'

export interface AxisSubItemResult {
  subLabel: string
  sourceField: FieldName | null
  audited: AuditedField | null
  /** Never a backend-triggered action for a `not_evaluated` sub-item --
   * `VerificationAction.triggered_by_status` is a closed `'vague' | 'absent'`
   * backend type, and this sub-item was never actually evaluated as either,
   * so fabricating one here would misuse that type. */
  action: VerificationAction | null
  /** `undefined` only for the (unreached in practice) case where the
   * backend's response omits this field entirely from `analysis.fields`. */
  displayStatus: AxisDisplayStatus | undefined
  /** Set only when `displayStatus === 'not_evaluated'`. */
  notEvaluatedMessage?: string
}

export interface AxisResult {
  id: AxisId
  label: string
  subItems: AxisSubItemResult[]
}

function findField(analysis: PostingAnalysis, field: FieldName): AuditedField | null {
  return analysis.fields[field] ?? null
}

function findAction(analysis: PostingAnalysis, field: FieldName): VerificationAction | null {
  return analysis.verification_actions.find((a) => a.field === field) ?? null
}

/** A sub-item backed by a real atomic field: status/evidence/action all
 * come straight from the backend response, never invented here. */
function realSubItem(analysis: PostingAnalysis, field: FieldName, subLabel: string): AxisSubItemResult {
  const audited = findField(analysis, field)
  return {
    subLabel,
    sourceField: field,
    audited,
    action: findAction(analysis, field),
    displayStatus: audited?.status,
  }
}

/** A sub-item with no backing atomic field at all -- always `not_evaluated`,
 * never `absent` (see the module doc comment for why that distinction
 * matters), and never carries a fabricated verification action. */
function notEvaluatedSubItem(subLabel: string, message: string): AxisSubItemResult {
  return {
    subLabel,
    sourceField: null,
    audited: null,
    action: null,
    displayStatus: 'not_evaluated',
    notEvaluatedMessage: message,
  }
}

/** Builds all six axes for one posting's analysis. Never called with two
 * postings' data mixed together -- call once per side (metro, jeonbuk). */
export function buildAxisResults(analysis: PostingAnalysis): AxisResult[] {
  return AXIS_ORDER.map((id): AxisResult => {
    switch (id) {
      case 'compensation':
        return {
          id,
          label: AXIS_LABELS[id],
          subItems: [
            realSubItem(analysis, 'salary', '연봉·월급·수당'),
            realSubItem(analysis, 'probation_terms', '수습 중 급여'),
          ],
        }
      case 'employment_stability':
        return {
          id,
          label: AXIS_LABELS[id],
          subItems: [
            realSubItem(analysis, 'employment_type', '정규직·계약직·계약기간'),
            realSubItem(analysis, 'probation_terms', '수습기간'),
          ],
        }
      case 'duties_fit':
        return {
          id,
          label: AXIS_LABELS[id],
          subItems: [realSubItem(analysis, 'duties', '실제 수행 업무')],
        }
      case 'skills_requirements':
        return {
          id,
          label: AXIS_LABELS[id],
          subItems: [
            realSubItem(analysis, 'tools_or_skills', '기술·도구·자격증'),
            // 경력·학력: no structured field exists in the current public
            // metadata or analysis pipeline, so it is never shown as a
            // row here rather than fabricated.
          ],
        }
      case 'work_conditions':
        return {
          id,
          label: AXIS_LABELS[id],
          subItems: [notEvaluatedSubItem('근로시간·교대제·통근', WORK_CONDITIONS_UNSUPPORTED_MESSAGE)],
        }
      case 'growth_benefits':
        // 교육(training_or_mentoring)과 복지(기숙사·통근지원 등)는 서로 다른
        // 정보다 -- training_or_mentoring 하나만으로 복지까지 확인됐다고
        // 표시하지 않는다 (TASK section 5.2).
        return {
          id,
          label: AXIS_LABELS[id],
          subItems: [
            realSubItem(analysis, 'training_or_mentoring', '교육·성장 지원 (OJT·멘토링)'),
            notEvaluatedSubItem('복지·기숙사·통근지원', WELFARE_UNSUPPORTED_MESSAGE),
          ],
        }
    }
  })
}
