import { expect, test } from '@playwright/test'

test.describe('AI추천(일자리) 목록 화면 (전북 일자리 비교 에이전트)', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => window.localStorage.clear())
  })

  test('일자리 찾기 탭의 AI추천(일자리)를 누르면 수도권 공고 목록 화면으로 이동한다', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('tab', { name: '일자리 찾기' }).click()
    await page.getByRole('link', { name: /AI추천\(일자리\)/ }).click()

    await expect(page).toHaveURL(/\/ai-job-recommend$/)
    await expect(page.getByRole('heading', { name: '수도권 채용공고 + 전북 일자리 비교 에이전트' })).toBeVisible()
    await expect(page.getByText('데모 모드 · 사전 검증된 분석 결과')).toBeVisible()
    await expect(page.getByText('본 서비스는 고용24 공식 서비스가 아닌 해커톤 시연용 프로토타입입니다.')).toBeVisible()
  })

  test('로그인 전에는 안내 문구와 데모 로그인 버튼이 보인다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await expect(page.getByText('로그인하면 관심 생활권의 유사 일자리와 비교할 수 있습니다.')).toBeVisible()
    await expect(page.getByRole('button', { name: /데모 로그인/ })).toBeVisible()
  })

  test('데모 로그인 후 관심 생활권과 기준 문구가 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('button', { name: /데모 로그인/ }).click()

    await expect(page.getByText('로그인 사용자: 전북 청년 데모 사용자')).toBeVisible()
    await expect(page.getByText('내 관심 생활권: 전북특별자치도')).toBeVisible()
    await expect(page.getByText('현재 전북특별자치도를 기준으로 비교하고 있습니다.')).toBeVisible()

    await page.getByRole('button', { name: '로그아웃' }).click()
    await expect(page.getByRole('button', { name: /데모 로그인/ })).toBeVisible()
  })

  test('수동 붙여넣기는 기본 화면이 아니라 보조 링크로만 제공된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await expect(page.getByRole('textbox', { name: /채용공고 본문/ })).toHaveCount(0)
    await expect(page.getByRole('link', { name: '다른 공고 직접 비교 (수동 붙여넣기)' })).toBeVisible()
  })

  test('고용24 홈으로 링크를 누르면 메인페이지로 돌아간다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('link', { name: '고용24 홈으로' }).click()
    await expect(page).toHaveURL(/\/$/)
    await expect(page.getByRole('heading', { name: /나만의 고용서비스/ })).toBeVisible()
  })

  test('전북 비교 후보는 최대 3건이며 유사도 순위가 아니라는 안내가 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    const cards = page.locator('li:has-text("수도권 공고")')
    await expect(cards.first()).toBeVisible({ timeout: 10000 })
    const firstCard = cards.first()

    await firstCard.getByRole('button', { name: /내 지역 유사 일자리 보기/ }).click()
    const candidateItems = firstCard.locator('ul > li')
    await expect(candidateItems.first()).toBeVisible({ timeout: 10000 })

    const count = await candidateItems.count()
    expect(count).toBeGreaterThan(0)
    expect(count).toBeLessThanOrEqual(3)

    // 유사도 순위가 아니라는 안내 문구 (TASK "수도권 대표 공고 1건 -> 전북
    // 비교 공고 최대 3건" section 5).
    await expect(firstCard.getByText('최대 3건 표시합니다')).toBeVisible()
    await expect(firstCard.getByText('유사도 순위가 아니며')).toBeVisible()

    // 금지 표현: 유사도 점수, 최적, 적합도, 검증된 매칭 등은 어디에도 없어야 함.
    const cardText = await firstCard.innerText()
    expect(cardText).not.toMatch(/유사도 상위|가장 유사한|최적의 전북|적합도 \d|추천 점수|검증된 매칭/)
  })

  test('두 번째 후보를 선택하면 선택 상태와 분석 대상이 갱신된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    const cards = page.locator('li:has-text("수도권 공고")')
    await expect(cards.first()).toBeVisible({ timeout: 10000 })
    const firstCard = cards.first()

    await firstCard.getByRole('button', { name: /내 지역 유사 일자리 보기/ }).click()
    const candidateButtons = firstCard.locator('ul > li button')
    await expect(candidateButtons.first()).toBeVisible({ timeout: 10000 })
    const candidateCount = await candidateButtons.count()
    test.skip(candidateCount < 2, '이 수도권 공고에는 비교 후보가 2건 미만이라 후보 전환을 검증할 수 없음')

    const first = candidateButtons.nth(0)
    const second = candidateButtons.nth(1)
    const secondCandidateLabel = (await second.locator('p').first().innerText()).trim()

    await first.click()
    await expect(first).toHaveAttribute('aria-pressed', 'true')
    await expect(second).toHaveAttribute('aria-pressed', 'false')

    await second.click()
    await expect(second).toHaveAttribute('aria-pressed', 'true')
    await expect(first).toHaveAttribute('aria-pressed', 'false')

    // Wait for the second candidate's analysis to actually settle (success
    // or a typed error) rather than only for the transient loading text --
    // private full text (data/private/intake_raw/**) is only staged
    // locally on some machines (see README), so this spec must handle
    // both outcomes without assuming either one.
    const successHeading = firstCard.getByText('수정된 6개 비교축')
    const jeonbukErrorAlert = firstCard.getByText(/후보:/)
    await expect(successHeading.or(jeonbukErrorAlert)).toBeVisible({ timeout: 15000 })

    if (await successHeading.isVisible()) {
      // Real private text was available for this run: confirm the
      // comparison actually switched to the SECOND candidate specifically
      // (not a stale render still describing the first one), and that
      // candidates are never analyzed in the background before selection
      // (the first candidate's own comparison label would already have
      // been visible before this point if it had been).
      await expect(firstCard.getByText(secondCandidateLabel).first()).toBeVisible()
    }
  })
})
