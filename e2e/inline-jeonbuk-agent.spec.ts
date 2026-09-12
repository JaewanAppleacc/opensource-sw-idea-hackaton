import { expect, test } from '@playwright/test'

/**
 * Full journey for the inline "전북 일자리 비교 에이전트" (real backend,
 * LLM_PROVIDER=mock, real private posting text staged locally under
 * data/private/intake_raw/** for this run). Covers TASK section 10's
 * checklist items 1-8 and 10; item 9 (backend stopped -> network error
 * banner) is verified manually per the same reasoning as the prior
 * full-flow spec (flipping server availability mid-suite is not clean).
 */
test.describe('전북 일자리 비교 에이전트 - 실제 데이터 전체 흐름', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => window.localStorage.clear())
  })

  test('수도권 공고 목록 -> 전북 비교 에이전트 -> 후보 선택 -> 6개 항목 비교 -> 확인 질문 -> 자금 비교', async ({ page }) => {
    const consoleErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text())
    })

    // 1. AI추천 페이지 진입
    await page.goto('/ai-job-recommend')

    // 2. 수도권 실제 공고 목록 확인
    const cards = page.locator('li:has-text("수도권 공고")')
    await expect(cards.first()).toBeVisible({ timeout: 10000 })
    await expect(cards.first().getByText('원문 보기')).toBeVisible()

    // 3. 공고 하나에서 전북 비교 에이전트 실행
    const firstCard = cards.first()
    await firstCard.getByRole('button', { name: /내 지역 유사 일자리 보기/ }).click()

    // 4. 전북 후보 표시 확인 (fact-based matching reasons, no score)
    await expect(firstCard.getByText('내 지역 비교 에이전트가 찾은')).toBeVisible()
    const candidateButton = firstCard.locator('ul > li button').first()
    await expect(candidateButton).toBeVisible({ timeout: 10000 })
    await expect(candidateButton.getByText('동일한 직무')).toBeVisible()
    await expect(page.getByText(/추천 점수/)).toHaveCount(0)

    // 5. 후보 선택
    await candidateButton.click()

    // 6. 6개 항목 비교 확인
    await expect(firstCard.getByText('6개 항목 비교')).toBeVisible()
    await expect(firstCard.getByText('공고를 분석하고 있어요...').first()).toHaveCount(0, { timeout: 20000 })
    await expect(firstCard.getByText('급여').first()).toBeVisible()

    // 7. vague/absent 확인 질문 확인 (mock 추출이 이 실제 공고에서 vague를 만들어냄)
    const hasStatusLabel = await firstCard
      .getByText(/구체적으로 확인됨|언급됐지만 판단하기 어려움|공고에서 확인되지 않음/)
      .first()
      .isVisible()
      .catch(() => false)
    expect(hasStatusLabel).toBeTruthy()

    // 8. 자금 비교 실행 (선택적으로 펼치는 구조)
    await expect(firstCard.getByRole('button', { name: /자금 축적 비교 펼치기/ })).toBeVisible()
    await firstCard.getByRole('button', { name: /자금 축적 비교 펼치기/ }).click()
    await expect(firstCard.getByRole('heading', { name: /자금축적 비교/ })).toBeVisible()

    // No internal terms (LLM/JSON/schema/pipeline) leaked to the user-facing copy.
    const bodyText = await page.locator('body').innerText()
    expect(bodyText).not.toMatch(/\bLLM\b|\bJSON\b|\bschema\b|\bpipeline\b/i)

    expect(consoleErrors).toEqual([])
  })

  test('로그인 후에는 내 관심 생활권 라벨이 카드 CTA에 반영된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('button', { name: /데모 로그인/ }).click()
    await expect(page.getByText(/내 지역 유사 일자리 보기/).first()).toBeVisible()
    await expect(page.getByText('(전북특별자치도 기준)').first()).toBeVisible()
  })
})

test.describe('모바일 뷰포트', () => {
  test.use({ viewport: { width: 390, height: 844 } })

  test('AI추천 목록 카드가 모바일에서 가로 스크롤 없이 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    const cards = page.locator('li:has-text("수도권 공고")')
    await expect(cards.first()).toBeVisible({ timeout: 10000 })

    const hasHorizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    )
    expect(hasHorizontalOverflow).toBe(false)
  })
})
