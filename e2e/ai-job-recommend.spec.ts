import { expect, test } from '@playwright/test'

test.describe('AI추천(일자리) 공고 분석 화면', () => {
  test('일자리 찾기 탭의 AI추천(일자리)를 누르면 분석 화면으로 이동한다', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('tab', { name: '일자리 찾기' }).click()
    await page.getByRole('link', { name: /AI추천\(일자리\)/ }).click()

    await expect(page).toHaveURL(/\/ai-job-recommend$/)
    await expect(page.getByRole('heading', { name: '채용공고 AI 분석 (데모)' })).toBeVisible()
    await expect(page.getByText('현재 MVP에서는 다음 기능이 없습니다.')).toBeVisible()
  })

  test('필수값 없이 제출하면 유효성 오류가 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('button', { name: '공고 분석하기' }).click()

    await expect(page.getByText('관심 직종을 입력하거나 목록에서 선택해 주세요.')).toBeVisible()
    await expect(page.getByText('채용공고 본문을 입력해 주세요.')).toBeVisible()
  })

  test('데모 공고 불러오기로 값을 채우고 제출하면 확인 카드가 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('button', { name: '데모 공고 불러오기' }).click()

    const categoryInput = page.getByLabel('관심 직종')
    await expect(categoryInput).toHaveValue('생산직(제조 조립원)')
    await expect(page.getByLabel(/채용공고 본문/)).not.toHaveValue('')

    await page.getByRole('button', { name: '공고 분석하기' }).click()

    await expect(page.getByRole('status').filter({ hasText: '입력 내용을 확인했어요' })).toBeVisible()
    await expect(page.getByText('생산직(제조 조립원)').first()).toBeVisible()
  })

  test('고용24 홈으로 링크를 누르면 메인페이지로 돌아간다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('link', { name: '고용24 홈으로' }).click()
    await expect(page).toHaveURL(/\/$/)
    await expect(page.getByRole('heading', { name: /나만의 고용서비스/ })).toBeVisible()
  })
})
