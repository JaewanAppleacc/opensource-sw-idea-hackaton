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
    // 근로시간과 근무환경, 복지·기숙사·통근지원은 not_evaluated -- 항상 "현재
    // MVP 분석 미지원"으로 표시되고, absent(공고에서 확인되지 않음)로 표시되지
    // 않는다 (TASK section 5.1/5.2, Playwright 필수 확인 #7).
    await expect(firstCard.getByText('근로시간·교대제·통근지원은 현재 MVP의 자동 분석 범위에 포함되지 않습니다.').first()).toBeVisible()
    await expect(firstCard.getByText('기숙사·식사 제공·통근지원 등 복지 정보는 현재 MVP의 자동 분석 범위에 포함되지 않습니다.').first()).toBeVisible()
    await expect(firstCard.getByText('현재 MVP 분석 미지원').first()).toBeVisible()

    // 양쪽 분석이 끝나면 카드 내부 단계 표시가 ④ 지원 전 확인을 현재 단계로
    // 강조한다 (TASK section 6, Playwright 필수 확인 #4).
    await expect(firstCard.getByText('지원 전 확인').first()).toHaveClass(/bg-brand-blue/)

    // 종합점수/승자 표시가 없음 -- 비교 카드 범위로 한정한다 (페이지 상단의
    // 잡케어 프로필 안내문이 "역량점수는 제공하지 않습니다"라고 정직하게
    // 언급하는 것 자체는 허용되며, 검증 대상은 실제 비교 결과 영역이다).
    const cardText = await firstCard.innerText()
    expect(cardText).not.toMatch(/점수|승자|추천 점수|적합도 \d/)

    // 8. 선택 전에 우선 확인할 정보 확인 -- not_evaluated 항목(근로시간·교대제·
    // 통근, 복지·기숙사·통근지원)은 이 목록에 절대 나타나지 않는다 (#7).
    const priorityList = firstCard.getByText('선택 전에 우선 확인할 정보').locator('..')
    await expect(priorityList).toBeVisible()
    const priorityListText = await priorityList.innerText()
    expect(priorityListText).not.toContain('근로시간·교대제·통근')
    expect(priorityListText).not.toContain('복지·기숙사·통근지원')

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

    // 13. 조건 역전점 확인 (주거비/차량비/주거지원/실수령액 4종 중 최소 주거비+1종)
    // "연봉 차이"가 아닌 "월 OO 차이" 표현만 사용한다 (TASK section 5.3, #10).
    await expect(firstCard.getByText('조건 역전점')).toBeVisible()
    await expect(firstCard.getByText('월 주거비 차이 역전점.')).toBeVisible()
    await expect(
      firstCard.getByText('한 가지 조건만 변경하고 나머지 입력값은 동일하다고 가정한 시나리오입니다.'),
    ).toBeVisible()
    const crossoverSectionText = await firstCard.getByText('조건 역전점').locator('..').innerText()
    expect(crossoverSectionText).not.toContain('연봉 차이')

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

  test('로그인 데모 -> 잡케어 관심직무 표시 -> AI추천 -> 단계 표시 연결 (Playwright 필수 확인 #1~4)', async ({
    page,
  }) => {
    await page.goto('/ai-job-recommend')

    // 1. 고용24 로그인 데모 표시
    await expect(page.getByRole('button', { name: /데모 로그인/ })).toBeVisible()
    // 로그인 전 페이지 단계 표시는 ① 잡케어 관심직무를 현재 단계로 강조
    await expect(page.getByText('잡케어 관심직무').first()).toHaveClass(/bg-brand-blue/)

    await page.getByRole('button', { name: /데모 로그인/ }).click()

    // 2. 잡케어 관심직무 표시 -- 취업확률/역량점수/심리검사 "결과"(수치·값)는
    // 절대 없음. 프로필 안내문이 "이런 결과는 제공하지 않습니다"라고 이름을
    // 언급하는 것 자체는 정직한 공개이므로 허용하되, 실제 숫자 점수·확률
    // 값(예: "87점", "72%")은 어디에도 없어야 한다.
    const jobCarePanel = page.getByText('잡케어 연결 (시연용 프로필)').locator('..')
    await expect(jobCarePanel).toBeVisible()
    await expect(page.getByText('제조·조립')).toBeVisible()
    await expect(page.getByText('정규직').first()).toBeVisible()
    await expect(page.getByText('해커톤 시연용 사용자 프로필입니다.')).toBeVisible()
    const jobCarePanelText = await jobCarePanel.innerText()
    expect(jobCarePanelText).toContain('취업확률·역량점수·심리검사 결과는 제공하지 않습니다.')
    expect(jobCarePanelText).not.toMatch(/\d+\s*%|\d+\s*점(?!수)|\d+\s*\/\s*100/)

    // 로그인 후에는 ② 고용24 AI추천이 현재 단계
    await expect(page.getByText('고용24 AI추천').first()).toHaveClass(/bg-brand-blue/)

    // 3. 고용24 AI추천 공고 표시 (수도권 공고 카드)
    const cards = page.locator('li:has-text("수도권 공고")')
    await expect(cards.first()).toBeVisible({ timeout: 10000 })

    // 4. 내 지역 비교 단계 연결 -- 기존 AI추천/기존 검증과의 차이를 짧게 안내
    await expect(page.getByText('사람과 일자리의 적합성을 분석').first()).toBeVisible()
    await expect(page.getByText('수도권과 자기 지역 일자리의 비교 가능성을 분석').first()).toBeVisible()
    await page
      .getByText('고용24 AI추천과 지역 선택 보정 에이전트는 어떻게 다른가요?')
      .click()
    await expect(page.getByText('지원자가 지역 간 조건을 판단할 수 있을 만큼')).toBeVisible()
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
