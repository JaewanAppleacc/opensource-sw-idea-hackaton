/**
 * AI추천(일자리) list of metropolitan-area ("수도권") postings shown on
 * /ai-job-recommend.
 *
 * There is no backend endpoint yet that lists metropolitan postings (the
 * contract only exposes POST /postings/match, which returns Jeonbuk
 * candidates for a given occupation -- see contracts/openapi.json). Per
 * TASK section 4, an unready API must be handled with one of: an explicit
 * demo fixture, a loading state, "분석 준비 중", or a connection-failure
 * state -- never invented data presented as real.
 *
 * This file is that explicit demo fixture. Every entry below is a literal
 * copy of a `region_group: "metro"` record from the synthetic, clearly
 * `redistributable: true` dataset already committed at
 * data/postings/postings.jsonl (fixture_build_date 2026-09-12,
 * source_name "synthetic_fixture_v1"). Nothing here is a real job posting;
 * all company names are explicitly marked "(예시)" in the source data.
 * `data/private/**` (the real, non-redistributable posting text) is never
 * read or copied here.
 *
 * Fields not literally present in the underlying full_text (e.g. no
 * explicit education requirement) are represented as `null`, not guessed --
 * the UI must render an honest "명시되지 않음" state for those.
 */

export interface MetroJobListing {
  id: string
  companyName: string
  title: string
  region: string
  employmentType: string
  /** Literal salary-related excerpt from the posting text, or null if the posting never states one. */
  salaryText: string | null
  /** Literal experience/education-related excerpt from the posting text, or null if never stated. */
  conditionText: string | null
  sourceName: string
  sourceUrl: string | null
  occupation: string
  fullText: string
  isSynthetic: true
}

export const METRO_JOB_LISTINGS: MetroJobListing[] = [
  {
    id: 'MET-001',
    companyName: '(예시) 가상제조 서울1호(주)',
    title: '완성차 부품 조립·품질검사 생산직(제조 조립원) 모집',
    region: '서울특별시',
    employmentType: '정규직',
    salaryText: '월급 270만원(세전)',
    conditionText: '지게차 운전면허 및 PLC 설비 조작 경험자 우대 (학력 조건 명시되지 않음)',
    sourceName: 'synthetic_fixture_v1',
    sourceUrl: null,
    occupation: '생산직(제조 조립원)',
    fullText:
      '(예시) 가상제조 서울1호(주)에서 생산직(제조 조립원)을 모집합니다. 완성차 부품 조립 및 품질 검사 업무를 담당합니다. 지게차 운전면허 및 PLC 설비 조작 경험자를 우대합니다. 월급 270만원(세전) 지급합니다. 입사 후 2주간 사수와 1:1 현장 OJT를 진행합니다. 수습기간 3개월, 수습기간 중 급여는 본급의 90% 지급합니다. 고용형태는 정규직입니다.',
    isSynthetic: true,
  },
  {
    id: 'MET-002',
    companyName: '(예시) 가상모터스 서울2호(주)',
    title: '사출 성형·포장 생산부서 신규 채용',
    region: '서울특별시',
    employmentType: '정규직',
    salaryText: '월급 265만원(세전)',
    conditionText: '관련 경험자 우대 (학력 조건 명시되지 않음)',
    sourceName: 'synthetic_fixture_v1',
    sourceUrl: null,
    occupation: '생산직(제조 조립원)',
    fullText:
      '(예시) 가상모터스 서울2호(주) 생산부서 채용 공고입니다. 사출 성형기 운영 및 제품 포장 업무를 수행합니다. 관련 경험자를 우대합니다. 월급 265만원(세전) 지급합니다. 매월 1회 정기 안전교육 및 사내 직무교육을 제공합니다. 수습기간 3개월, 수습기간 동안 동일 급여 지급합니다. 고용형태는 정규직입니다.',
    isSynthetic: true,
  },
  {
    id: 'MET-003',
    companyName: '(예시) 가상부품 인천1호(주)',
    title: '차량 부품 조립라인 생산직(제조 조립원) 채용',
    region: '인천광역시',
    employmentType: '정규직',
    salaryText: '월급 268만원(세전)',
    conditionText: '도면 해독 능력 및 캘리퍼스 사용 가능자 우대 (학력 조건 명시되지 않음)',
    sourceName: 'synthetic_fixture_v1',
    sourceUrl: null,
    occupation: '생산직(제조 조립원)',
    fullText:
      '(예시) 가상부품 인천1호(주)에서 생산직(제조 조립원)을 채용합니다. 차량 부품 조립 라인 근무 및 공정 검사 업무를 담당합니다. 도면 해독 능력 및 캘리퍼스 사용 가능자를 우대합니다. 월급 268만원(세전) 지급합니다. 체계적인 교육 시스템을 운영하고 있습니다. 수습기간 3개월, 수습기간 중 급여는 본급의 90% 지급합니다. 고용형태는 정규직입니다.',
    isSynthetic: true,
  },
  {
    id: 'MET-004',
    companyName: '(예시) 가상기계 인천2호',
    title: '생산라인 인원 모집 (완성차 부품 조립·품질검사)',
    region: '인천광역시',
    employmentType: '정규직',
    salaryText: null,
    conditionText: '지게차 운전면허 소지자 우대, 급여는 경력에 따라 협의 (금액 미명시)',
    sourceName: 'synthetic_fixture_v1',
    sourceUrl: null,
    occupation: '생산직(제조 조립원)',
    fullText:
      '(예시) 가상기계 인천2호 생산라인 인원 모집 공고입니다. 완성차 부품 조립 및 품질 검사 업무를 담당합니다. 지게차 운전면허 소지자를 우대합니다. 급여는 경력에 따라 협의 후 결정합니다. 입사 후 2주간 사수와 1:1 현장 OJT를 진행합니다. 수습기간 있음(세부 조건은 면접 시 안내). 고용형태는 정규직입니다.',
    isSynthetic: true,
  },
  {
    id: 'MET-010',
    companyName: '(예시) 가상제조 화성1호(주)',
    title: '완성차 부품 조립·품질검사 생산직(제조 조립원) 채용',
    region: '경기 화성시',
    employmentType: '정규직',
    salaryText: '월급 272만원(세전)',
    conditionText: '지게차 운전면허 및 PLC 설비 조작 경험자 우대 (학력 조건 명시되지 않음)',
    sourceName: 'synthetic_fixture_v1',
    sourceUrl: null,
    occupation: '생산직(제조 조립원)',
    fullText:
      '(예시) 가상제조 화성1호(주)에서 생산직(제조 조립원)을 채용합니다. 완성차 부품 조립 및 품질 검사 업무를 담당합니다. 지게차 운전면허 및 PLC 설비 조작 경험자를 우대합니다. 월급 272만원(세전) 지급합니다. 입사 후 2주간 사수와 1:1 현장 OJT를 진행합니다. 수습기간 3개월, 수습기간 중 급여는 본급의 90% 지급합니다. 채용형태는 면접 후 결정합니다.',
    isSynthetic: true,
  },
  {
    id: 'MET-011',
    companyName: '(예시) 가상전자 수원1호',
    title: '생산직(제조 조립원, 계약직) 모집',
    region: '경기 수원시',
    employmentType: '계약직',
    salaryText: '월급 225만원(세전)',
    conditionText: '경력·학력 조건 명시되지 않음',
    sourceName: 'synthetic_fixture_v1',
    sourceUrl: null,
    occupation: '생산직(제조 조립원)',
    fullText:
      '(예시) 가상전자 수원1호에서 생산직(제조 조립원, 계약직)을 모집합니다. 완성차 부품 조립 보조 업무를 수행합니다. 월급 225만원(세전) 지급합니다. 고용형태는 계약직(1년)입니다.',
    isSynthetic: true,
  },
]
