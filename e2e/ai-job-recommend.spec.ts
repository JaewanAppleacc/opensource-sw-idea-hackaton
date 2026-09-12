import { expect, test } from '@playwright/test'

/**
 * AI추천(일자리) 목록 안에서 동작하는 지역 비교 에이전트 UX.
 *
 * Covers TASK section 11 scenarios 1-9 and 11 (scenario 10, backend
 * connection failure, is covered separately below using page.route to
 * deterministically simulate the backend being unreachable -- flipping a
 * real backend process on/off mid-suite is not a clean automated scenario).
 */
test.describe('AI추천(일자리) 목록 · 지역 비교 에이전트', () => {
  // ---- 1. AI추천 페이지 진입 ----
  test('일자리 찾기 탭의 AI추천(일자리)를 누르면 AI추천 목록으로 이동한다', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('tab', { name: '일자리 찾기' }).click()
    await page.getByRole('link', { name: /AI추천\(일자리\)/ }).click()

    await expect(page).toHaveURL(/\/ai-job-recommend$/)
    await expect(page.getByRole('heading', { name: 'AI추천 채용공고' })).toBeVisible()
    await expect(page.getByText('데모 모드 · 사전 검증된 분석 결과')).toBeVisible()
    await expect(page.getByText('본 서비스는 고용24 공식 서비스가 아닌 해커톤 시연용 프로토타입입니다.')).toBeVisible()
  })

  // ---- 2. 시연용 로그인 프로필 확인 ----
  test('시연용 로그인 프로필과 관심 생활권이 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')

    await expect(page.getByText('전북 청년 데모 사용자')).toBeVisible()
    await expect(page.getByText('관심 생활권:')).toBeVisible()
    await expect(page.getByText('전북특별자치도').first()).toBeVisible()
    await expect(page.getByText('현재 전북특별자치도를 기준으로 내 지역 일자리를 비교합니다.')).toBeVisible()
  })

  // ---- 3. 수도권 추천 공고 확인 ----
  test('수도권 AI추천 공고 목록이 회사명·지역·고용형태·임금과 함께 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')

    await expect(page.getByRole('heading', { name: '수도권 AI추천 공고' })).toBeVisible()
    const metroSection = page.locator('section:has(#metro-list-heading)')
    await expect(metroSection.getByText('(예시) 가상제조 서울1호(주)')).toBeVisible()
    await expect(metroSection.getByText('서울특별시').first()).toBeVisible()
    await expect(metroSection.getByText('임금 정보').first()).toBeVisible()
    await expect(metroSection.getByRole('button', { name: '내 지역 유사 일자리 보기' }).first()).toBeVisible()
    await expect(metroSection.getByText('전북특별자치도 기준').first()).toBeVisible()
  })

  // ---- 4. 내 지역 유사 일자리 보기 실행 ----
  test('다른 공고에서 내 지역 유사 일자리 보기를 누르면 그 공고 기준으로 비교 패널이 교체된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')

    const firstCard = page.locator('section:has(#metro-list-heading)').locator('ul > li').nth(0)
    const secondCard = page.locator('section:has(#metro-list-heading)').locator('ul > li').nth(1)
    await expect(secondCard).toBeVisible()

    // First card is auto-selected on load (TASK section 4 demo convenience).
    await expect(firstCard.getByRole('button', { name: '내 지역 유사 일자리 보기' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )

    await secondCard.getByRole('button', { name: '내 지역 유사 일자리 보기' }).click()

    // Selecting a different posting replaces the active card and re-triggers
    // the comparison panel for that posting.
    await expect(secondCard.getByRole('button', { name: '내 지역 유사 일자리 보기' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    await expect(firstCard.getByRole('button', { name: '내 지역 유사 일자리 보기' })).toHaveAttribute(
      'aria-pressed',
      'false',
    )
    await expect(page.getByRole('heading', { name: '내 지역 비교 에이전트가 찾은 전북 일자리' })).toBeVisible({
      timeout: 10000,
    })
  })

  // ---- 5. 전북 후보 확인 ----
  test('전북 비교 에이전트가 찾은 전북 일자리 후보(최대 3건)가 사실 기반 매칭 이유와 함께 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')

    const candidatesPanel = page.getByRole('heading', { name: '내 지역 비교 에이전트가 찾은 전북 일자리' })
    await expect(candidatesPanel).toBeVisible({ timeout: 10000 })
    await expect(
      page.getByText('직무와 고용조건을 기준으로 비교했습니다. 공고에 없는 정보는 추정하지 않습니다.'),
    ).toBeVisible()

    const candidateItems = page.locator('section:has(#candidates-heading)').locator('ul > li')
    const count = await candidateItems.count()
    expect(count).toBeGreaterThan(0)
    expect(count).toBeLessThanOrEqual(3)

    await expect(page.getByText('임금:').first()).toBeVisible()
    await expect(page.getByRole('button', { name: '비교하기' }).first()).toBeVisible()
  })

  // ---- 6. 후보 선택 & 7. 6개 항목 비교 확인 ----
  test('전북 후보를 선택(비교하기)하면 6개 항목이 수도권/전북 열로 나란히 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')

    await page.getByRole('button', { name: '비교하기' }).first().click()

    await expect(page.getByRole('heading', { name: '6개 항목 비교' })).toBeVisible()
    await expect(page.getByText('공고를 분석하고 있어요...').first()).toHaveCount(0, { timeout: 15000 })

    const comparisonSection = page.locator('section[aria-labelledby="comparison-heading"]')
    await expect(comparisonSection.getByText('급여', { exact: true })).toBeVisible()
    await expect(comparisonSection.getByText('담당 업무', { exact: true })).toBeVisible()
    await expect(comparisonSection.getByText('필요 기술·도구·자격', { exact: true })).toBeVisible()
    await expect(comparisonSection.getByText('교육·멘토링', { exact: true })).toBeVisible()
    await expect(comparisonSection.getByText('수습기간과 수습 중 급여', { exact: true })).toBeVisible()
    await expect(comparisonSection.getByText('고용형태', { exact: true }).first()).toBeVisible()

    // At least one status pill uses the renamed display labels (enum values
    // confirmed/vague/absent are unchanged; only the Korean text changes).
    const hasStatusLabel = await comparisonSection
      .getByText(/확인 가능|추가 확인 필요|공고에서 확인 불가/)
      .first()
      .isVisible()
    expect(hasStatusLabel).toBeTruthy()
  })

  // ---- 8. 확인 질문 확인 ----
  test('언급됐지만 불확실하거나 없는 항목에는 확인이 필요한 질문이 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('button', { name: '비교하기' }).first().click()

    await expect(page.getByRole('heading', { name: '6개 항목 비교' })).toBeVisible()
    await expect(page.getByText('공고를 분석하고 있어요...').first()).toHaveCount(0, { timeout: 15000 })

    await expect(page.getByText(/확인이 필요한 질문/).first()).toBeVisible()
  })

  // ---- 9. 자금 비교 실행 ----
  test('6개 항목 비교 아래 접힌 자금 축적 비교를 펼쳐서 계산할 수 있다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('button', { name: '비교하기' }).first().click()
    await expect(page.getByText('공고를 분석하고 있어요...').first()).toHaveCount(0, { timeout: 15000 })

    const toggle = page.getByRole('button', { name: '주거비를 포함한 자금 축적 비교' })
    await expect(toggle).toBeVisible()
    await expect(toggle).toHaveAttribute('aria-expanded', 'false')
    await toggle.click()
    await expect(toggle).toHaveAttribute('aria-expanded', 'true')

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
    await expect(page.getByText('보증금 (묶인 자산)').first()).toBeVisible()
    await expect(page.getByText(/보증금을 제외한 가용자금/).first()).toBeVisible()
    await expect(page.getByText('주거비 교차점')).toBeVisible()
    // The panel explicitly states no winner/recommendation is computed.
    await expect(page.getByText('추천 점수나 승자는 표시하지 않습니다.')).toBeVisible()
  })

  // ---- 11. 모바일 레이아웃 확인 ----
  test('모바일에서는 수도권 공고와 전북 후보 패널이 세로로 쌓인다', async ({ page, viewport }) => {
    test.skip(!viewport || viewport.width >= 1024, '모바일 전용 레이아웃 테스트')
    await page.goto('/ai-job-recommend')

    const metroSection = page.locator('section:has(#metro-list-heading)')
    const candidatesSection = page.locator('section:has(#candidates-heading)')
    await expect(metroSection).toBeVisible()
    await expect(candidatesSection).toBeVisible({ timeout: 10000 })

    const metroBox = await metroSection.boundingBox()
    const candidatesBox = await candidatesSection.boundingBox()
    expect(metroBox).not.toBeNull()
    expect(candidatesBox).not.toBeNull()
    // Stacked vertically: the candidates panel starts below the metro list.
    expect(candidatesBox!.y).toBeGreaterThanOrEqual(metroBox!.y + metroBox!.height - 4)

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    expect(overflow).toBeLessThanOrEqual(1)
  })

  test('데스크톱에서는 수도권 공고와 전북 후보 패널이 나란히 표시된다', async ({ page, viewport }) => {
    test.skip(!viewport || viewport.width < 1024, '데스크톱 전용 레이아웃 테스트')
    await page.goto('/ai-job-recommend')

    const metroSection = page.locator('section:has(#metro-list-heading)')
    const candidatesSection = page.locator('section:has(#candidates-heading)')
    await expect(candidatesSection).toBeVisible({ timeout: 10000 })

    const metroBox = await metroSection.boundingBox()
    const candidatesBox = await candidatesSection.boundingBox()
    expect(metroBox).not.toBeNull()
    expect(candidatesBox).not.toBeNull()
    // Side by side: vertical ranges overlap substantially instead of one
    // starting only after the other ends.
    expect(candidatesBox!.y).toBeLessThan(metroBox!.y + metroBox!.height / 2)
  })

  // ---- 10. 백엔드 연결 실패 시 오류 안내 확인 ----
  test('전북 후보 요청이 실패하면 백엔드 연결 실패 안내가 표시된다', async ({ page }) => {
    await page.route('**/api/v1/postings/match', (route) => route.abort('failed'))
    await page.goto('/ai-job-recommend')

    await expect(page.getByRole('alert')).toContainText('백엔드 서버에 연결할 수 없습니다')
  })

  test('고용24 홈으로 링크를 누르면 메인페이지로 돌아간다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('link', { name: '고용24 홈으로' }).click()
    await expect(page).toHaveURL(/\/$/)
    await expect(page.getByRole('heading', { name: /나만의 고용서비스/ })).toBeVisible()
  })

  test('수동 입력(고급) 링크로 /manual-analysis에 진입할 수 있다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('link', { name: /다른 공고를 직접 붙여넣어 비교하고 싶다면/ }).click()
    await expect(page).toHaveURL(/\/manual-analysis$/)
    await expect(page.getByRole('heading', { name: '채용공고 직접 붙여넣어 비교하기 (데모)' })).toBeVisible()
  })
})
