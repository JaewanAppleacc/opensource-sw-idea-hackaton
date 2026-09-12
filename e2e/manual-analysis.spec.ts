import { expect, test } from '@playwright/test'

/**
 * Manual posting-paste flow, relocated from /ai-job-recommend to
 * /manual-analysis (TASK section 8): it is no longer the default landing
 * screen, but the capability itself -- and its original test coverage --
 * is preserved rather than deleted.
 */
test.describe('수동 입력(고급) 채용공고 분석 화면', () => {
  test('AI추천 목록에서 링크를 통해 진입할 수 있다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('link', { name: /다른 공고를 직접 붙여넣어 비교하고 싶다면/ }).click()
    await expect(page).toHaveURL(/\/manual-analysis$/)
    await expect(page.getByRole('heading', { name: '채용공고 직접 붙여넣어 비교하기 (데모)' })).toBeVisible()
    await expect(page.getByText('현재 MVP에서는 다음 기능이 없습니다.')).toBeVisible()
  })

  test('필수값 없이 제출하면 유효성 오류가 표시된다', async ({ page }) => {
    await page.goto('/manual-analysis')
    await page.getByRole('button', { name: '공고 분석하기' }).click()

    await expect(page.getByText('관심 직종을 입력하거나 목록에서 선택해 주세요.')).toBeVisible()
    await expect(page.getByText('채용공고 본문을 입력해 주세요.')).toBeVisible()
  })

  test('데모 공고 불러오기로 값을 채우고 제출하면 확인 카드가 표시된다', async ({ page }) => {
    await page.goto('/manual-analysis')
    await page.getByRole('button', { name: '데모 공고 불러오기' }).click()

    const categoryInput = page.getByLabel('관심 직종')
    await expect(categoryInput).toHaveValue('생산직(제조 조립원)')
    await expect(page.getByLabel(/채용공고 본문/)).not.toHaveValue('')

    await page.getByRole('button', { name: '공고 분석하기' }).click()

    await expect(page.getByRole('status').filter({ hasText: '입력 내용을 확인했어요' })).toBeVisible()
    await expect(page.getByText('생산직(제조 조립원)').first()).toBeVisible()
  })

  test('AI추천 목록으로 돌아가기/고용24 홈으로 링크가 동작한다', async ({ page }) => {
    await page.goto('/manual-analysis')
    await page.getByRole('link', { name: 'AI추천 목록으로 돌아가기' }).click()
    await expect(page).toHaveURL(/\/ai-job-recommend$/)

    await page.goto('/manual-analysis')
    await page.getByRole('link', { name: '고용24 홈으로' }).click()
    await expect(page).toHaveURL(/\/$/)
  })

  test('전북 후보를 선택하면 6개 항목 비교와 자금 비교(접힘)를 확인할 수 있다', async ({ page }) => {
    await page.goto('/manual-analysis')
    await page.getByRole('button', { name: '데모 공고 불러오기' }).click()
    await page.getByRole('button', { name: '공고 분석하기' }).click()

    const candidateButtons = page.locator('section:has(#candidates-heading) ul > li button', { hasText: '비교하기' })
    await expect(candidateButtons.first()).toBeVisible({ timeout: 10000 })
    await candidateButtons.first().click()

    await expect(page.getByRole('heading', { name: '6개 항목 분석' })).toBeVisible()
    await expect(page.getByText('공고를 분석하고 있어요...').first()).toHaveCount(0, { timeout: 15000 })

    const financeToggle = page.getByRole('button', { name: '주거비를 포함한 자금 축적 비교' })
    await expect(financeToggle).toBeVisible()
    await expect(financeToggle).toHaveAttribute('aria-expanded', 'false')
  })
})
