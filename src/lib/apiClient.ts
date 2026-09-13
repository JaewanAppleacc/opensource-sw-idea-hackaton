/**
 * Single API client layer for the FastAPI backend (contracts/openapi.json is
 * canonical). Every type here matches the backend's wire field names
 * (snake_case) exactly -- there is no camelCase renaming anywhere in this
 * app, so there is nothing for a naming adapter to convert. If the backend
 * contract ever changes, this is the one file to update.
 *
 * Never calls Anthropic/NVIDIA directly, never reads an LLM API key: the
 * only configuration this file reads is VITE_API_BASE_URL, the backend's
 * own HTTP address.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const DEFAULT_TIMEOUT_MS = 20000

// ---- Six-field audit contract (matches backend/app/models/common.py + posting.py) ----

export type FieldName =
  | 'salary'
  | 'duties'
  | 'tools_or_skills'
  | 'training_or_mentoring'
  | 'probation_terms'
  | 'employment_type'

export type FieldStatus = 'confirmed' | 'vague' | 'absent'

export interface EvidenceSpan {
  text: string
  start: number
  end: number
}

export type Provenance = 'WORK24_STRUCTURED' | 'SLM_EXTRACTED' | 'USER_REPORTED'

export interface AuditedField {
  field: FieldName
  status: FieldStatus
  evidence: EvidenceSpan | null
  reason_code: string
  /** Where this field's value actually came from -- WORK24_STRUCTURED
   * (고용24 등록 정보, deterministic, never LLM-touched) or SLM_EXTRACTED
   * (공고 본문 자유서술 분석). USER_REPORTED exists in the backend enum for a
   * future multi-turn feature; nothing produces it yet. */
  provenance: Provenance
}

export interface WorkHoursInfo {
  weekly_hours: number | null
  detailed_work_hours: string | null
  shift_type: string | null
  /** "confirmed": at least one sub-field is stated on the Work24 registry
   * record. "structured_absent": a registry record exists for this
   * posting but states none of these -- render as "고용24 등록 정보에서
   * 확인되지 않음", never "확인 불가". */
  status: 'confirmed' | 'structured_absent'
  provenance: 'WORK24_STRUCTURED'
}

export type VerificationChannel = 'email' | 'phone' | 'interview' | 'document_review' | 'pre_contract'

export interface VerificationAction {
  field: FieldName
  channel: VerificationChannel
  prompt: string
  triggered_by_status: 'vague' | 'absent'
}

export interface ValidationWarning {
  code: string
  field: FieldName | null
  message: string
}

export interface ExternalContext {
  source: string
  reference_date: string
  description: string
  limitations: string
  values: Record<string, number | string>
}

export interface PostingInput {
  posting_id?: string | null
  source_text: string
  source_url?: string | null
  expected_occupation?: string | null
}

export interface PostingAnalysis {
  posting_id: string | null
  occupation: string | null
  employment_type: string | null
  fields: Partial<Record<FieldName, AuditedField>>
  verification_actions: VerificationAction[]
  validation_warnings: ValidationWarning[]
  external_context: ExternalContext[]
  /** null means no Work24StructuredPosting record exists for this posting
   * at all -- keep showing the existing not_evaluated MVP-scope display.
   * Non-null means a registry record exists; see WorkHoursInfo.status for
   * whether it actually states weekly_hours/detailed_work_hours/shift_type. */
  work_hours: WorkHoursInfo | null
}

// ---- Matching contract (matches backend/app/models/match.py) ----

export interface MatchRequest {
  occupation: string
  employment_type?: string | null
  posting_id?: string | null
}

export interface MatchCandidate {
  posting_id: string
  source_id: string | null
  source_url: string | null
  region: string
  municipality: string | null
  occupation: string
  employment_type: string
  company_name: string | null
  source_text: string | null
  is_synthetic: boolean
  matching_fields: string[]
  mismatch_fields: string[]
  description: string
}

export interface MatchResponse {
  query_occupation: string
  query_employment_type: string | null
  candidates: MatchCandidate[]
  dataset_description: string
}

// ---- Home-region listing/matching contract (matches backend/app/models/listing.py) ----

export interface PostingListItem {
  posting_id: string
  company_name: string | null
  region: string
  municipality: string | null
  occupation: string
  employment_type: string
  source_url: string | null
  collection_date: string | null
  is_synthetic: boolean
  private_text_available: boolean
}

export interface PostingListResponse {
  home_region: string
  postings: PostingListItem[]
  dataset_description: string
}

export interface HomeRegionMatchRequest {
  metro_posting_id: string
}

export interface AnalyzeByIdRequest {
  posting_id: string
  expected_occupation?: string | null
}

// ---- Finance contract (matches backend/app/models/finance.py) ----

export interface FinancialOption {
  label: string
  monthly_income_after_tax: number
  monthly_housing_cost: number
  monthly_other_living_cost: number
  deposit: number
}

export interface FinancialAssumptions {
  annual_income_growth_rate?: number
  annual_cost_growth_rate?: number
  rounding_unit_krw?: number
}

export interface FinancialComparisonRequest {
  metropolitan: FinancialOption
  jeonbuk: FinancialOption
  assumptions?: FinancialAssumptions
}

export interface FinancialOptionResult {
  label: string
  monthly_surplus: number
  one_year_liquid_cash: number
  three_year_liquid_cash: number
  deposit_locked: number
  one_year_total_with_deposit: number
  three_year_total_with_deposit: number
}

export interface CrossoverResult {
  varied_option: string
  comparison_option: string
  varied_variable: 'monthly_housing_cost'
  current_value: number
  threshold_value: number
  rounding_unit_krw: number
  held_constant: Record<string, number>
  interpretation: string
}

export interface FinancialComparison {
  assumptions: FinancialAssumptions
  options: Record<string, FinancialOptionResult>
  crossover: CrossoverResult
  disclaimer: string
}

// ---- Gap stats contract (matches backend/app/models/stats.py) ----

export interface GapStatsFilters {
  region: string | null
  occupation: string | null
  employment_type: string | null
}

export interface GapStats {
  sample_size_postings: number
  sample_size_cells: number
  filters: GapStatsFilters
  rubric_version: string
  label_proportions: Record<string, Record<string, number>>
  label_proportions_by_region?: Record<string, Record<string, Record<string, number>>>
  exploratory: true
}

export interface GapStatsResponse {
  ready: boolean
  stats: GapStats | null
  error: ApiErrorBody | null
}

// ---- Error envelope (matches backend/app/models/common.py: APIError) ----

export type ApiErrorCode =
  | 'invalid_input'
  | 'analysis_failed'
  | 'provider_unavailable'
  | 'no_match_found'
  | 'data_not_ready'
  | 'private_data_unavailable'
  // Frontend-only codes: the backend never returns these, but the UI needs
  // a typed way to represent "we never got a real error envelope back".
  | 'network_error'
  | 'timeout'
  | 'unexpected_response'

export interface ApiErrorBody {
  code: ApiErrorCode
  message: string
  details?: Record<string, unknown> | null
}

export class ApiClientError extends Error {
  code: ApiErrorCode
  details?: Record<string, unknown> | null

  constructor(body: ApiErrorBody) {
    super(body.message)
    this.name = 'ApiClientError'
    this.code = body.code
    this.details = body.details ?? null
  }
}

interface RequestOptions {
  timeoutMs?: number
  signal?: AbortSignal
}

async function apiFetch<T>(path: string, init: RequestInit, options: RequestOptions = {}): Promise<T> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), options.timeoutMs ?? DEFAULT_TIMEOUT_MS)

  // If the caller passed their own signal (e.g. to cancel on unmount),
  // respect it too by aborting our internal controller when it fires.
  if (options.signal) {
    if (options.signal.aborted) controller.abort()
    else options.signal.addEventListener('abort', () => controller.abort(), { once: true })
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init.headers },
      signal: controller.signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiClientError({ code: 'timeout', message: '분석 요청이 시간 초과되었습니다. 잠시 후 다시 시도해 주세요.' })
    }
    // Network failure, backend not running, CORS block, etc. Never surface
    // the raw browser error message (may contain internal detail) to the user.
    throw new ApiClientError({
      code: 'network_error',
      message: '백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해 주세요.',
    })
  } finally {
    window.clearTimeout(timeout)
  }

  let body: unknown = null
  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (!response.ok) {
    const errorBody = (body as { error?: ApiErrorBody } | null)?.error
    if (errorBody?.code && errorBody?.message) {
      throw new ApiClientError(errorBody)
    }
    throw new ApiClientError({
      code: 'unexpected_response',
      message: `백엔드가 예상하지 못한 응답을 반환했습니다 (HTTP ${response.status}).`,
    })
  }

  return body as T
}

export interface HealthResponse {
  status: string
  provider_mode: string
  dataset_available: boolean
  rubric_version: string
}

export function getHealth(options?: RequestOptions): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/api/v1/health', { method: 'GET' }, options)
}

export function analyzePosting(input: PostingInput, options?: RequestOptions): Promise<PostingAnalysis> {
  return apiFetch<PostingAnalysis>(
    '/api/v1/postings/analyze',
    { method: 'POST', body: JSON.stringify(input) },
    options,
  )
}

export function matchPostings(request: MatchRequest, options?: RequestOptions): Promise<MatchResponse> {
  return apiFetch<MatchResponse>(
    '/api/v1/postings/match',
    { method: 'POST', body: JSON.stringify(request) },
    options,
  )
}

export function compareFinance(
  request: FinancialComparisonRequest,
  options?: RequestOptions,
): Promise<FinancialComparison> {
  return apiFetch<FinancialComparison>(
    '/api/v1/finance/compare',
    { method: 'POST', body: JSON.stringify(request) },
    options,
  )
}

export function getGapStats(options?: RequestOptions): Promise<GapStatsResponse> {
  return apiFetch<GapStatsResponse>('/api/v1/data/gap-stats', { method: 'GET' }, options)
}

export function getHomeRegionListing(options?: RequestOptions): Promise<PostingListResponse> {
  return apiFetch<PostingListResponse>('/api/v1/postings/home-region-listing', { method: 'GET' }, options)
}

export function getHomeRegionMatches(
  request: HomeRegionMatchRequest,
  options?: RequestOptions,
): Promise<MatchResponse> {
  return apiFetch<MatchResponse>(
    '/api/v1/postings/home-region-matches',
    { method: 'POST', body: JSON.stringify(request) },
    options,
  )
}

export function analyzeByPostingId(
  request: AnalyzeByIdRequest,
  options?: RequestOptions,
): Promise<PostingAnalysis> {
  return apiFetch<PostingAnalysis>(
    '/api/v1/postings/analyze-by-id',
    { method: 'POST', body: JSON.stringify(request) },
    options,
  )
}
