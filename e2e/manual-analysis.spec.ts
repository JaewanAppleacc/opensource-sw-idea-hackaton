import { expect, test } from '@playwright/test'

/**
 * The original manual paste-and-analyze flow, relocated (not deleted) from
 * /ai-job-recommend to /manual-analysis when that route became the default
 * inline "전북 일자리 비교 에이전트" listing. Same assertions as before the
 * move -- see git history of e2e/ai-job-recommend.spec.ts.
 */
test.describe('직접 비교 (수동 붙여넣기) 화면', () => {
  test('AI추천 목록의 "다른 공고 직접 비교" 링크로 진입할 수 있다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('link', { name: '다른 공고 직접 비교 (수동 붙여넣기)' }).click()
    await expect(page).toHaveURL(/\/manual-analysis$/)
    await expect(page.getByRole('heading', { name: '채용공고 직접 붙여넣어 분석 (데모)' })).toBeVisible()
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

  test('AI추천(일자리) 목록으로 링크를 누르면 목록 화면으로 돌아간다', async ({ page }) => {
    await page.goto('/manual-analysis')
    await page.getByRole('link', { name: 'AI추천(일자리) 목록으로' }).click()
    await expect(page).toHaveURL(/\/ai-job-recommend$/)
  })
})
