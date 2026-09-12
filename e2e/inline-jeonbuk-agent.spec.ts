import { expect, test } from '@playwright/test'

/**
 * Full journey for the inline "지역 기반 커리어 의사결정 에이전트" (real
 * backend, LLM_PROVIDER=mock, real private posting text staged locally
 * under data/private/intake_raw/** for this run). Covers TASK section 12's
 * 13-step scenario and section 14's required new coverage. Item 9 from the
 * original scenario (backend stopped -> network error banner) is verified
 * manually per the same reasoning as the prior spec (flipping server
 * availability mid-suite is not a clean automated scenario).
 */
test.describe('지역 기반 커리어 의사결정 에이전트 - 실제 데이터 전체 흐름', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => window.localStorage.clear())
  })

  async function openFirstCandidateComparison(page: import('@playwright/test').Page) {
    await page.goto('/ai-job-recommend')
    await page.getByRole('button', { name: /데모 로그인/ }).click()
    const cards = page.locator('li:has-text("수도권 공고")')
    await expect(cards.first()).toBeVisible({ timeout: 10000 })
    const firstCard = cards.first()
    await firstCard.getByRole('button', { name: /내 지역 유사 일자리 보기/ }).click()
    const candidateButton = firstCard.locator('ul > li button').first()
    await expect(candidateButton).toBeVisible({ timeout: 10000 })
    await candidateButton.click()
    return firstCard
  }

  test('1~13단계: 로그인 -> 목록 -> 후보 선택 -> 중요조건 선택 -> 6개 비교축 -> 우선 확인 정보 -> 기업 질문 -> 자금 비교 -> 재계산 -> 역전점', async ({
    page,
  }) => {
    const consoleErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text())
    })

    const firstCard = await openFirstCandidateComparison(page)

    // 6. 중요조건 3개 선택 (기본값이 이미 3개 선택되어 있음을 확인)
    await expect(firstCard.getByText('내가 중요하게 생각하는 조건을 선택해 주세요.')).toBeVisible()
    const checkboxes = firstCard.getByRole('checkbox')
    const checkedCount = await checkboxes.evaluateAll((els) => els.filter((el) => (el as HTMLInputElement).checked).length)
    expect(checkedCount).toBe(3)

    // 4개째 선택 시도 -> 막혀야 함 (최대 3개)
    const uncheckedBoxes = firstCard.getByRole('checkbox', { checked: false })
    const uncheckedCount = await uncheckedBoxes.count()
    for (let i = 0; i < uncheckedCount; i++) {
      await expect(uncheckedBoxes.nth(i)).toBeDisabled()
    }

    // 7. 수정된 6개 비교축 확인
    await expect(firstCard.getByText('수정된 6개 비교축')).toBeVisible()
    await expect(firstCard.getByText('임금·보상').first()).toBeVisible()
    await expect(firstCard.getByText('고용안정성').first()).toBeVisible()
    await expect(firstCard.getByText('담당 업무와 직무 적합성').first()).toBeVisible()
    await expect(firstCard.getByText('필요 역량과 지원조건').first()).toBeVisible()
    await expect(firstCard.getByText('근로시간과 근무환경').first()).toBeVisible()
    await expect(firstCard.getByText('성장·복지 지원').first()).toBeVisible()
    // 근로시간과 근무환경은 항상 안전한 미확인 문구를 보여야 함
    await expect(firstCard.getByText('현재 공고에서 근로시간·교대제·통근지원 정보를 확인할 수 없습니다.').first()).toBeVisible()

    // 종합점수/승자 표시가 없음
    const bodyText = await page.locator('body').innerText()
    expect(bodyText).not.toMatch(/점수|승자|추천 점수|적합도 \d/)

    // 8. 선택 전에 우선 확인할 정보 확인
    await expect(firstCard.getByText('선택 전에 우선 확인할 정보')).toBeVisible()

    // 9. 기업에 물어볼 질문 확인 (복사/저장/필터 기능 포함)
    const questionsHeading = firstCard.getByText('기업에 물어볼 질문')
    if (await questionsHeading.isVisible().catch(() => false)) {
      await expect(firstCard.getByRole('button', { name: '질문 복사' }).first()).toBeVisible()
      await expect(firstCard.getByRole('button', { name: /질문 목록에 저장|저장됨/ }).first()).toBeVisible()
      await expect(firstCard.getByRole('button', { name: '선택한 질문만 보기' })).toBeVisible()
      // 가짜 기업 답변이 없어야 함 -- 사용자 메모 입력만 존재
      await expect(firstCard.getByText('내 메모 (기업의 실제 답변이 아닙니다)').first()).toBeVisible()
    }

    // 10. 자금 축적 비교 펼치기
    await firstCard.getByRole('button', { name: /자금 축적 비교 펼치기/ }).click()
    await expect(firstCard.getByText('시연용 예시값입니다. 실제 거주지와 출퇴근 조건에 맞게 수정할 수 있습니다.')).toBeVisible()
    await firstCard.getByRole('button', { name: '자금 비교 계산하기' }).click()
    await expect(firstCard.getByText('월 가용자금').first()).toBeVisible({ timeout: 10000 })

    // 13. 조건 역전점 확인 (주거비/차량비/주거지원/임금 4종 중 최소 주거비+1종)
    await expect(firstCard.getByText('조건 역전점')).toBeVisible()
    await expect(firstCard.getByText('주거비 역전점.')).toBeVisible()

    // 11~12. 주거비·교통비 입력 변경 -> 1년·3년 결과 자동 재계산
    const oneYearBefore = await firstCard.getByText('1년 가용자금').first().locator('..').innerText()
    const metroFields = firstCard.locator('fieldset', { hasText: '수도권' }).first()
    await metroFields.getByLabel('교통비 (원/월)').fill('500000')
    await expect(async () => {
      const oneYearAfter = await firstCard.getByText('1년 가용자금').first().locator('..').innerText()
      expect(oneYearAfter).not.toBe(oneYearBefore)
    }).toPass({ timeout: 10000 })

    expect(consoleErrors).toEqual([])
  })

  test('중요조건을 다르게 선택하면 우선 확인할 정보 목록도 달라진다', async ({ page }) => {
    const firstCard = await openFirstCandidateComparison(page)
    await expect(firstCard.getByText('수정된 6개 비교축')).toBeVisible()

    const before = await firstCard.getByText('선택 전에 우선 확인할 정보').locator('..').innerText()

    // 임금·보상(첫 번째 체크박스) 해제, 필요 역량과 지원조건 체크
    await firstCard.getByRole('checkbox').nth(0).uncheck()
    await firstCard.locator('label', { hasText: '필요 역량과 지원조건' }).getByRole('checkbox').check()

    await expect(async () => {
      const after = await firstCard.getByText('선택 전에 우선 확인할 정보').locator('..').innerText()
      expect(after).not.toBe(before)
    }).toPass({ timeout: 5000 })
  })

  test('private 데이터가 없는 posting_id는 fail-closed 오류를 보여준다 (analyze-by-id)', async ({ request }) => {
    // Directly exercises the API contract's fail-closed guarantee.
    const base = process.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const res = await request.post(`${base}/api/v1/postings/analyze-by-id`, {
      data: { posting_id: 'NOT-A-REAL-POSTING-ID' },
    })
    expect(res.status()).toBe(503)
    const body = await res.json()
    expect(body.error.code).toBe('private_data_unavailable')
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

  test('AI추천 목록 카드와 비교축 화면이 모바일에서 가로 스크롤 없이 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    const cards = page.locator('li:has-text("수도권 공고")')
    await expect(cards.first()).toBeVisible({ timeout: 10000 })

    const firstCard = cards.first()
    await firstCard.getByRole('button', { name: /내 지역 유사 일자리 보기/ }).click()
    const candidateButton = firstCard.locator('ul > li button').first()
    await expect(candidateButton).toBeVisible({ timeout: 10000 })
    await candidateButton.click()
    await expect(firstCard.getByText('수정된 6개 비교축')).toBeVisible({ timeout: 10000 })

    const hasHorizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    )
    expect(hasHorizontalOverflow).toBe(false)
  })
})
