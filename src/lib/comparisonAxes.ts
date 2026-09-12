/**
 * Presentation-only remapping of the backend's six atomic audited fields
 * into the six user-facing comparison axes. This file never talks to the
 * backend and never invents a status, evidence, or verification action --
 * it only regroups what `PostingAnalysis.fields` already contains, per
 * TASK section 3 & 4 ("기존 원자 필드 분석 결과 → presentation mapper →
 * 근거 기반 6개 비교축"). The backend contract (PostingAnalysis, AuditedField,
 * FieldName) is completely unchanged.
 *
 * Axis 5 (근로시간과 근무환경) has no backing atomic field at all in the
 * current pipeline -- the mock/real provider never extracts working-hours
 * information. Per instruction, this is never estimated: it always renders
 * as absent with the exact required message, never a guessed status.
 */
import type { AuditedField, FieldName, PostingAnalysis, VerificationAction } from './apiClient'

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
  growth_benefits: 'OJT, 멘토링, 교육기간, 직무교육, 자격증 지원, 기숙사·사택, 식사 제공, 복지제도',
}

export const WORK_CONDITIONS_UNSUPPORTED_MESSAGE =
  '현재 공고에서 근로시간·교대제·통근지원 정보를 확인할 수 없습니다.'

const WORK_CONDITIONS_QUESTION: VerificationAction = {
  field: 'employment_type', // no dedicated FieldName exists for this axis; not shown to the user
  channel: 'interview',
  prompt: '근무시간과 교대제, 통근 지원(통근버스/차량 필요 여부) 여부를 확인해 주실 수 있나요?',
  triggered_by_status: 'absent',
}

export interface AxisSubItemResult {
  subLabel: string
  sourceField: FieldName | null
  audited: AuditedField | null
  action: VerificationAction | null
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
            {
              subLabel: '연봉·월급·수당',
              sourceField: 'salary',
              audited: findField(analysis, 'salary'),
              action: findAction(analysis, 'salary'),
            },
            {
              subLabel: '수습 중 급여',
              sourceField: 'probation_terms',
              audited: findField(analysis, 'probation_terms'),
              action: findAction(analysis, 'probation_terms'),
            },
          ],
        }
      case 'employment_stability':
        return {
          id,
          label: AXIS_LABELS[id],
          subItems: [
            {
              subLabel: '정규직·계약직·계약기간',
              sourceField: 'employment_type',
              audited: findField(analysis, 'employment_type'),
              action: findAction(analysis, 'employment_type'),
            },
            {
              subLabel: '수습기간',
              sourceField: 'probation_terms',
              audited: findField(analysis, 'probation_terms'),
              action: findAction(analysis, 'probation_terms'),
            },
          ],
        }
      case 'duties_fit':
        return {
          id,
          label: AXIS_LABELS[id],
          subItems: [
            {
              subLabel: '실제 수행 업무',
              sourceField: 'duties',
              audited: findField(analysis, 'duties'),
              action: findAction(analysis, 'duties'),
            },
          ],
        }
      case 'skills_requirements':
        return {
          id,
          label: AXIS_LABELS[id],
          subItems: [
            {
              subLabel: '기술·도구·자격증',
              sourceField: 'tools_or_skills',
              audited: findField(analysis, 'tools_or_skills'),
              action: findAction(analysis, 'tools_or_skills'),
            },
            // 경력·학력: no structured field exists in the current public
            // metadata or analysis pipeline, so it is never shown as a
            // row here rather than fabricated.
          ],
        }
      case 'work_conditions':
        return {
          id,
          label: AXIS_LABELS[id],
          subItems: [
            {
              subLabel: '근로시간·교대제·통근',
              sourceField: null,
              audited: {
                field: 'employment_type', // placeholder; sourceField:null means "not from an atomic field"
                status: 'absent',
                evidence: null,
                reason_code: 'no_extractor_for_this_axis',
              },
              action: WORK_CONDITIONS_QUESTION,
            },
          ],
        }
      case 'growth_benefits':
        return {
          id,
          label: AXIS_LABELS[id],
          subItems: [
            {
              subLabel: 'OJT·멘토링·복지',
              sourceField: 'training_or_mentoring',
              audited: findField(analysis, 'training_or_mentoring'),
              action: findAction(analysis, 'training_or_mentoring'),
            },
          ],
        }
    }
  })
}
