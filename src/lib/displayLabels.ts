/**
 * Single place for every Korean display string derived from a backend enum
 * value. Keep all of it here so no other component has to guess a label or
 * duplicate this mapping.
 */
import type { ApiErrorCode, FieldName, FieldStatus, VerificationChannel } from './apiClient'

export const FIELD_LABELS: Record<FieldName, string> = {
  salary: '급여',
  duties: '업무',
  tools_or_skills: '도구·기술',
  training_or_mentoring: '교육·멘토링',
  probation_terms: '수습조건',
  employment_type: '고용형태',
}

export const FIELD_ORDER: FieldName[] = [
  'salary',
  'duties',
  'tools_or_skills',
  'training_or_mentoring',
  'probation_terms',
  'employment_type',
]

export const STATUS_LABELS: Record<FieldStatus, string> = {
  confirmed: '구체적으로 확인됨',
  vague: '언급됐지만 판단하기 어려움',
  absent: '공고에서 확인되지 않음',
}

/** Fact-based matching-reason phrases for MatchCandidate.matching_fields /
 * mismatch_fields (see backend/app/services/real_postings.py -- these are
 * the only two fields that service currently compares; no career/education
 * similarity is computed since the real data has no structured field for
 * either, so none is claimed here). */
export const MATCH_REASON_LABELS: Record<string, string> = {
  occupation: '동일한 직무',
  employment_type: '동일한 고용형태',
}

export function matchReasonLabel(field: string): string {
  return MATCH_REASON_LABELS[field] ?? field
}

export const CHANNEL_LABELS: Record<VerificationChannel, string> = {
  email: '이메일로 문의',
  phone: '전화로 문의',
  interview: '면접에서 확인',
  document_review: '서류로 확인',
  pre_contract: '계약 전 확인',
}

/** Maps a backend/frontend ApiErrorCode to a user-facing Korean message.
 * Never shows a raw stack trace, API key, or internal path. */
export function errorCodeToMessage(code: ApiErrorCode, fallback?: string): string {
  switch (code) {
    case 'invalid_input':
      return fallback || '입력값을 확인해 주세요.'
    case 'analysis_failed':
      return '공고 분석 결과 검증에 실패했습니다 (근거 문장이 원문과 일치하지 않음). 잠시 후 다시 시도해 주세요.'
    case 'provider_unavailable':
      return '분석 서비스에 일시적으로 연결할 수 없습니다.'
    case 'no_match_found':
      return '현재 검증된 전북 비교 후보가 없습니다.'
    case 'data_not_ready':
      return '아직 준비되지 않은 데이터입니다.'
    case 'private_data_unavailable':
      return '실제 원문 데이터가 연결되지 않은 데모 환경입니다.'
    case 'network_error':
      return '백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해 주세요.'
    case 'timeout':
      return '요청이 시간 초과되었습니다. 잠시 후 다시 시도해 주세요.'
    case 'unexpected_response':
    default:
      return '알 수 없는 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'
  }
}
