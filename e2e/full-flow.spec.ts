import { expect, test } from '@playwright/test'

/**
 * Integration smoke test against the LIVE FastAPI backend (LLM_PROVIDER=mock
 * expected to be running on VITE_API_BASE_URL, default http://localhost:8000).
 * Walks the full user journey from TASK section 0/10:
 *   수도권 공고 선택 -> 전북 후보 요청 -> 6필드 분석 -> 근거/확인 질문 ->
 *   자금축적 비교 -> demo/mock 배지 및 비공식 프로토타입 문구
 *
 * Does NOT exercise the "backend stopped" state (that is verified manually,
 * per the report, since flipping backend availability mid-suite is not a
 * clean automated scenario) or provider_unavailable/analysis_failed (the
 * mock provider cannot produce these).
 */
test.describe('전체 사용자 시연 흐름 - 직접 비교 경로 (/manual-analysis, 실제 백엔드 연동)', () => {
  test('수도권 선택 -> 전북 후보 -> 6필드 분석 -> 근거/질문 -> 자금 비교', async ({ page }) => {
    const consoleErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text())
    })

    await page.goto('/manual-analysis')

    // demo/mock badge and prototype disclaimer are visible immediately.
    await expect(page.getByText('데모 모드 · 사전 검증된 분석 결과')).toBeVisible()
    await expect(page.getByText('본 서비스는 고용24 공식 서비스가 아닌 해커톤 시연용 프로토타입입니다.')).toBeVisible()

    // 단계 A: 수도권 공고 선택 (데모 공고 불러오기 사용)
    await page.getByRole('button', { name: '데모 공고 불러오기' }).click()
    await page.getByRole('button', { name: '공고 분석하기' }).click()

    // 단계 B: 전북 후보 요청
    await expect(page.getByRole('heading', { name: '전북 비교 후보' })).toBeVisible()
    const candidateButtons = page.locator('section:has(#candidates-heading) ul > li button')
    await expect(candidateButtons.first()).toBeVisible({ timeout: 10000 })
    await candidateButtons.first().click()

    // 단계 C: 6필드 분석 (양쪽 패널 모두 로딩 종료까지 대기)
    await expect(page.getByRole('heading', { name: '6개 항목 분석' })).toBeVisible()
    await expect(page.getByText('공고를 분석하고 있어요...').first()).toHaveCount(0, { timeout: 15000 })

    const analysisSection = page.locator('section[aria-labelledby="analysis-heading"]')
    await expect(analysisSection.getByText('수도권 공고')).toBeVisible()
    await expect(analysisSection.getByText('급여').first()).toBeVisible()
    await expect(analysisSection.getByText('구체적으로 확인됨').first()).toBeVisible()

    // 단계 D: 근거와 확인 질문 (적어도 하나의 evidence 인용부호 또는 확인 질문이 존재)
    const hasEvidenceOrQuestion = await page
      .getByText(/확인 질문|"/, { exact: false })
      .first()
      .isVisible()
      .catch(() => false)
    expect(hasEvidenceOrQuestion).toBeTruthy()

    // 단계 E: 자금축적 비교 (시연용 예시값이 미리 채워져 있음)
    await expect(page.getByRole('heading', { name: '자금축적 비교', exact: true })).toBeVisible()
    await expect(page.getByText('시연용 예시값입니다. 실제 거주지와 출퇴근 조건에 맞게 수정할 수 있습니다.')).toBeVisible()
    const metroFields = page.locator('fieldset', { hasText: '수도권' }).first()
    await expect(metroFields.getByLabel('월 실수령액 (원)')).not.toHaveValue('')

    await page.getByRole('button', { name: '자금 비교 계산하기' }).click()

    await expect(page.getByText('월 가용자금').first()).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('1년 가용자금').first()).toBeVisible()
    await expect(page.getByText('3년 가용자금 (가정 기반)').first()).toBeVisible()
    await expect(page.getByText('조건 역전점')).toBeVisible()
    await expect(page.getByText('월 주거비 차이 역전점.')).toBeVisible()
    await expect(page.getByText('한 가지 조건만 변경하고 나머지 입력값은 동일하다고 가정한 시나리오입니다.')).toBeVisible()

    // 입력값 변경 시 즉시 재계산 (디바운스 후 자동 호출)
    await metroFields.getByLabel('월세 (원/월)').fill('2000000')
    await expect(page.getByText('월 실수령액 차이 역전점.')).toBeVisible({ timeout: 10000 })

    // No unhandled console errors anywhere in the flow.
    expect(consoleErrors).toEqual([])
  })

  test('음수/누락 재정 입력은 오류로 표시된다', async ({ page }) => {
    await page.goto('/manual-analysis')
    await page.getByRole('button', { name: '데모 공고 불러오기' }).click()
    await page.getByRole('button', { name: '공고 분석하기' }).click()

    const candidateButtons = page.locator('section:has(#candidates-heading) ul > li button')
    await expect(candidateButtons.first()).toBeVisible({ timeout: 10000 })
    await candidateButtons.first().click()

    await expect(page.getByRole('heading', { name: '자금축적 비교', exact: true })).toBeVisible()
    // Clear a required field (defaults are pre-filled with example values) and submit.
    const metroFields = page.locator('fieldset', { hasText: '수도권' }).first()
    await metroFields.getByLabel('월 실수령액 (원)').fill('')
    await page.getByRole('button', { name: '자금 비교 계산하기' }).click()
    await expect(page.getByText('모든 항목을 0 이상의 숫자로 입력해 주세요.')).toBeVisible()
  })

  test('지역 결손 통계는 준비되지 않음 상태를 정직하게 표시한다', async ({ page }) => {
    await page.goto('/manual-analysis')
    await page.getByRole('button', { name: '데모 공고 불러오기' }).click()
    await page.getByRole('button', { name: '공고 분석하기' }).click()
    const candidateButtons = page.locator('section:has(#candidates-heading) ul > li button')
    await expect(candidateButtons.first()).toBeVisible({ timeout: 10000 })
    await candidateButtons.first().click()

    await expect(page.getByText('지역 결손 통계')).toBeVisible()
    await expect(page.getByText(/아직 준비되지 않았습니다/)).toBeVisible({ timeout: 10000 })
  })
})
