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
})
