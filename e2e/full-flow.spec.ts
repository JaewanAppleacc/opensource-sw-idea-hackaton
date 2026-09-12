import { expect, test } from '@playwright/test'

/**
 * Integration smoke test against the LIVE FastAPI backend (LLM_PROVIDER=mock
 * expected to be running on VITE_API_BASE_URL, default http://localhost:8000).
 * Walks the full demo journey from TASK section 2:
 *   고용24 AI추천 일자리 목록 -> 수도권 추천 공고 열람 -> 내 지역 유사 일자리
 *   보기 -> 전북 후보 -> 6개 항목 비교 -> 확인 질문 -> 자금축적 비교
 *
 * Does NOT exercise provider_unavailable/analysis_failed (the mock provider
 * cannot produce these); the backend-unreachable state is covered
 * separately in ai-job-recommend.spec.ts via page.route (deterministic,
 * does not require actually stopping the backend process mid-suite).
 */
test.describe('전체 사용자 시연 흐름 (실제 백엔드 연동)', () => {
  test('수도권 공고 -> 전북 후보 -> 6개 항목 비교 -> 확인 질문 -> 자금 비교', async ({ page }) => {
    const consoleErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text())
    })

    await page.goto('/ai-job-recommend')

    // demo/mock badge and prototype disclaimer are visible immediately.
    await expect(page.getByText('데모 모드 · 사전 검증된 분석 결과')).toBeVisible()
    await expect(page.getByText('본 서비스는 고용24 공식 서비스가 아닌 해커톤 시연용 프로토타입입니다.')).toBeVisible()

    // 시연용 로그인 프로필: 관심 생활권 = 전북특별자치도.
    await expect(page.getByText('전북 청년 데모 사용자')).toBeVisible()
    await expect(page.getByText('전북특별자치도').first()).toBeVisible()

    // 단계 A: 수도권 AI추천 공고 열람 (첫 공고는 자동으로 전북 비교 패널이 열려 있음)
    await expect(page.getByRole('heading', { name: '수도권 AI추천 공고' })).toBeVisible()
    await expect(page.getByRole('heading', { name: '내 지역 비교 에이전트가 찾은 전북 일자리' })).toBeVisible({
      timeout: 10000,
    })

    // 단계 B: 전북 후보에서 비교하기 클릭
    const compareButtons = page.locator('section:has(#candidates-heading) ul > li button', { hasText: '비교하기' })
    await expect(compareButtons.first()).toBeVisible({ timeout: 10000 })
    await compareButtons.first().click()

    // 단계 C: 6개 항목 비교 (양쪽 모두 로딩 종료까지 대기)
    await expect(page.getByRole('heading', { name: '6개 항목 비교' })).toBeVisible()
    await expect(page.getByText('공고를 분석하고 있어요...').first()).toHaveCount(0, { timeout: 15000 })

    const comparisonSection = page.locator('section[aria-labelledby="comparison-heading"]')
    await expect(comparisonSection.getByText('급여', { exact: true })).toBeVisible()
    await expect(comparisonSection.getByText(/확인 가능|추가 확인 필요|공고에서 확인 불가/).first()).toBeVisible()

    // 단계 D: 근거와 확인 질문 (적어도 하나의 evidence 인용부호 또는 확인 질문이 존재)
    const hasEvidenceOrQuestion = await page
      .getByText(/확인이 필요한 질문|"/, { exact: false })
      .first()
      .isVisible()
      .catch(() => false)
    expect(hasEvidenceOrQuestion).toBeTruthy()

    // 단계 E: 자금축적 비교 (접힌 패널을 펼침)
    const financeToggle = page.getByRole('button', { name: '주거비를 포함한 자금 축적 비교' })
    await expect(financeToggle).toBeVisible()
    await financeToggle.click()

    const metroFields = page.locator('fieldset', { hasText: '수도권' }).first()
    const jbFields = page.locator('fieldset', { hasText: '전북' }).first()
    await metroFields.getByLabel('세후 월급 (원)').fill('3000000')
    await metroFields.getByLabel('주거비 + 관리비 (원/월)').fill('900000')
    await metroFields.getByLabel('기타 생활비 (원/월)').fill('500000')
    await metroFields.getByLabel('보증금 (원)').fill('20000000')
    await jbFields.getByLabel('세후 월급 (원)').fill('2600000')
    await jbFields.getByLabel('주거비 + 관리비 (원/월)').fill('400000')
    await jbFields.getByLabel('기타 생활비 (원/월)').fill('450000')
    await jbFields.getByLabel('보증금 (원)').fill('5000000')

    await page.getByRole('button', { name: '자금 비교 계산하기' }).click()

    await expect(page.getByText('월 잉여자금').first()).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('1년 후 유동자금').first()).toBeVisible()
    await expect(page.getByText('3년 후 유동자금 (가정 기반)').first()).toBeVisible()
    await expect(page.getByText('주거비 교차점')).toBeVisible()
    // The panel explicitly states no winner/recommendation is computed.
    await expect(page.getByText('추천 점수나 승자는 표시하지 않습니다.')).toBeVisible()

    // No unhandled console errors anywhere in the flow.
    expect(consoleErrors).toEqual([])
  })

  test('음수/누락 재정 입력은 오류로 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    const compareButtons = page.locator('section:has(#candidates-heading) ul > li button', { hasText: '비교하기' })
    await expect(compareButtons.first()).toBeVisible({ timeout: 10000 })
    await compareButtons.first().click()

    const financeToggle = page.getByRole('button', { name: '주거비를 포함한 자금 축적 비교' })
    await expect(financeToggle).toBeVisible()
    await financeToggle.click()

    // Leave every field blank and submit.
    await page.getByRole('button', { name: '자금 비교 계산하기' }).click()
    await expect(page.getByText('모든 항목을 0 이상의 숫자로 입력해 주세요.')).toBeVisible()
  })

  test('지역 결손 통계는 준비되지 않음 상태를 정직하게 표시한다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    const compareButtons = page.locator('section:has(#candidates-heading) ul > li button', { hasText: '비교하기' })
    await expect(compareButtons.first()).toBeVisible({ timeout: 10000 })
    await compareButtons.first().click()

    await expect(page.getByText('지역 결손 통계')).toBeVisible()
    await expect(page.getByText(/아직 준비되지 않았습니다/)).toBeVisible({ timeout: 10000 })
  })
})
