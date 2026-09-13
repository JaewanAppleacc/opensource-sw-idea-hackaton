import { expect, type Locator, type Page, test } from '@playwright/test'

/**
 * Full journey for the region-comparison agent (real backend,
 * LLM_PROVIDER=mock, real private posting text staged locally under
 * data/private/intake_raw/** for this run). Covers the same functional
 * scenario as before the "AI 티 제거 및 고용24 네이티브 UI 고도화" pass, with
 * selectors retargeted to the new master-detail layout (수도권 목록 왼쪽,
 * 전북 비교 패널 오른쪽 -- selection-driven, not a per-card accordion).
 * Item 9 from the original scenario (backend stopped -> network error
 * banner) is verified manually, same reasoning as before: flipping server
 * availability mid-suite is not a clean automated scenario.
 */
test.describe('지역 기반 커리어 의사결정 에이전트 - 실제 데이터 전체 흐름', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => window.localStorage.clear())
  })

  async function openFirstCandidateComparison(page: Page): Promise<Locator> {
    await page.goto('/ai-job-recommend')
    await page.getByRole('button', { name: /전북 데모 프로필로 시작/ }).click()
    const rows = page.getByTestId('capital-posting-list').getByRole('listitem')
    await expect(rows.first()).toBeVisible({ timeout: 10000 })
    await rows.first().getByRole('button', { name: /지역 비교/ }).click()

    const panel = page.getByTestId('jeonbuk-comparison-panel')
    const candidateButton = panel.locator('ul > li button').first()
    await expect(candidateButton).toBeVisible({ timeout: 10000 })
    await candidateButton.click()
    return panel
  }

  test('로그인 -> 목록 -> 후보 선택 -> 리포트 모달(조건·우선순위·질문·자금·역전점)', async ({ page }) => {
    // 리포트 모달 세부 단계(조건 비교, 우선 확인 조건, 질문, 자금, 요약)의
    // 상세 커버리지는 e2e/comparison-report-modal.spec.ts로 옮겨졌다. 이
    // 테스트는 그 진입 흐름(로그인 -> 목록 -> 후보 선택 -> 모달 오픈)과 콘솔
    // 에러 없음, 자금 재계산까지 이어지는 전체 여정만 남긴다.
    const consoleErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text())
    })

    const panel = await openFirstCandidateComparison(page)

    // 두 분석이 모두 성공(private 원문이 이 머신에 있음)해야 모달이 열리고
    // 이어지는 단계를 검증할 수 있다. 없으면 fail-closed 오류만 확인하고
    // 스킵한다 (README "장애 발생 시 데모 복구법" 참고).
    const dialog = page.getByRole('dialog')
    const jeonbukError = panel.getByText(/후보:/)
    await expect(dialog.or(jeonbukError)).toBeVisible({ timeout: 15000 })
    test.skip(
      await jeonbukError.isVisible(),
      'data/private/intake_raw/** 가 이 머신에 없어 실제 분석이 fail-closed로 종료됨 -- README 참고',
    )

    // 양쪽 분석이 끝나면 페이지 상단 단계 표시가 ③ 지원 전 확인을 현재 단계로
    // 강조한다 (모달과 무관하게, 페이지 레벨 상태).
    await expect(
      page.getByTestId('service-step-indicator').getByText('지원 전 확인'),
    ).toHaveClass(/bg-brand-blue/)

    // 종합점수/승자 표시가 없음 -- 모달 전체 범위.
    const dialogText = await dialog.innerText()
    expect(dialogText).not.toMatch(/점수|승자|추천 점수|적합도 \d/)

    // 조건 비교 단계로 이동 -> 6개 축 전부 렌더 확인
    await dialog.getByRole('button', { name: '다음' }).click()
    for (const label of ['임금·보상', '고용안정성', '담당 업무와 직무 적합성', '필요 역량과 지원조건', '근로시간과 근무환경', '성장·복지 지원']) {
      await expect(dialog.getByText(label).first()).toBeVisible()
    }
    await expect(dialog.getByText('현재 MVP 분석 미지원').first()).toBeVisible()

    // 우선 확인할 조건 단계 -> not_evaluated 항목은 절대 나타나지 않는다.
    await dialog.getByRole('button', { name: '다음' }).click()
    const unknownsText = await dialog.innerText()
    expect(unknownsText).not.toContain('근로시간·교대제·통근')
    expect(unknownsText).not.toContain('복지·기숙사·통근지원')

    // 지원 전 확인할 질문 단계 (체크리스트 + 복사, 메모는 opt-in)
    await dialog.getByRole('button', { name: '다음' }).click()
    const copyButton = dialog.getByRole('button', { name: '복사' }).first()
    if (await copyButton.isVisible().catch(() => false)) {
      const noteButton = dialog.getByRole('button', { name: '메모 추가' }).first()
      await noteButton.click()
      await expect(dialog.getByText('내 메모 (기업의 실제 답변이 아닙니다)').first()).toBeVisible()
    }

    // 자금 단계 -> 계산 -> 재계산
    await dialog.getByRole('button', { name: '다음' }).click()
    await expect(dialog.getByText('시연용 예시값입니다. 실제 거주지와 출퇴근 조건에 맞게 수정할 수 있습니다.')).toBeVisible()
    await dialog.getByRole('button', { name: '자금 비교 계산하기' }).click()
    await expect(dialog.getByText('월 가용자금').first()).toBeVisible({ timeout: 10000 })

    // 조건 역전점 확인 -- "연봉 차이"가 아닌 "월 OO 차이" 표현만 사용한다.
    await expect(dialog.getByText('조건 역전점', { exact: false })).toBeVisible()
    await expect(dialog.getByText('월 주거비 차이 역전점.')).toBeVisible()
    await expect(
      dialog.getByText('한 가지 조건만 변경하고 나머지 입력값은 동일하다고 가정한 시나리오입니다.'),
    ).toBeVisible()
    const crossoverSectionText = await dialog.getByText('조건 역전점', { exact: false }).locator('..').innerText()
    expect(crossoverSectionText).not.toContain('연봉 차이')

    // 주거비·교통비 입력 변경 -> 1년·3년 결과 자동 재계산
    const oneYearBefore = await dialog.getByText('1년 가용자금').first().locator('..').innerText()
    const metroFields = dialog.locator('fieldset', { hasText: '수도권' }).first()
    await metroFields.getByLabel('교통비 (원/월)').fill('500000')
    await expect(async () => {
      const oneYearAfter = await dialog.getByText('1년 가용자금').first().locator('..').innerText()
      expect(oneYearAfter).not.toBe(oneYearBefore)
    }).toPass({ timeout: 10000 })

    expect(consoleErrors).toEqual([])
  })

  test('중요조건을 다르게 선택하면 우선 확인할 정보 목록도 달라진다', async ({ page }) => {
    const panel = await openFirstCandidateComparison(page)
    const dialog = page.getByRole('dialog')
    const jeonbukError = panel.getByText(/후보:/)
    await expect(dialog.or(jeonbukError)).toBeVisible({ timeout: 15000 })
    test.skip(
      await jeonbukError.isVisible(),
      'data/private/intake_raw/** 가 이 머신에 없어 실제 분석이 fail-closed로 종료됨 -- README 참고',
    )

    // 조건 다시 선택하기(details)는 조건 비교 단계 안에 있다.
    await dialog.getByRole('button', { name: '다음' }).click()
    await dialog.getByText('중요하게 생각하는 조건 다시 선택하기').click()

    // 임금·보상(첫 번째 체크박스) 해제, 필요 역량과 지원조건 체크
    await dialog.getByRole('checkbox').nth(0).uncheck()
    await dialog.locator('label', { hasText: '필요 역량과 지원조건' }).getByRole('checkbox').check()

    // 우선 확인할 조건 단계로 이동하면 선택이 반영되어 있어야 한다.
    await dialog.getByRole('button', { name: '다음' }).click()
    const after = await dialog.innerText()
    expect(after).toContain('필요 역량과 지원조건')
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

  test('로그인 후에는 우측 패널이 선택한 공고 기준으로 비교 문구를 보여준다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('button', { name: /전북 데모 프로필로 시작/ }).click()
    const rows = page.getByTestId('capital-posting-list').getByRole('listitem')
    await expect(rows.first()).toBeVisible({ timeout: 10000 })
    await rows.first().getByRole('button', { name: /지역 비교/ }).click()

    const panel = page.getByTestId('jeonbuk-comparison-panel')
    await expect(panel.getByText('전북 비교 공고')).toBeVisible()
  })

  test('로그인 데모 -> 프로필 요약 -> AI추천 -> 단계 표시 연결', async ({ page }) => {
    await page.goto('/ai-job-recommend')

    const stepIndicator = page.getByTestId('service-step-indicator')

    // 로그인 데모 표시
    await expect(page.getByRole('button', { name: /전북 데모 프로필로 시작/ })).toBeVisible()
    // 로그인 전 페이지 단계 표시는 ① 추천 공고를 현재 단계로 강조
    await expect(stepIndicator.getByText('추천 공고')).toHaveClass(/bg-brand-blue/)

    await page.getByRole('button', { name: /전북 데모 프로필로 시작/ }).click()

    // 프로필 요약 표시 -- 취업확률/역량점수/심리검사 "결과"(수치·값)는 절대
    // 없음. 정보 팝오버가 "이런 결과는 제공하지 않습니다"라고 이름을 언급하는
    // 것 자체는 정직한 공개이므로 허용하되, 실제 숫자 점수·확률 값(예:
    // "87점", "72%")은 페이지 어디에도 없어야 한다.
    await expect(page.getByText('전북 청년 데모 사용자')).toBeVisible()
    // 대표 시연 페어와 동일한 실제 식품 연구개발 관심 직무를 표시한다.
    await expect(page.getByText('식품 연구개발').first()).toBeVisible()
    await expect(page.getByText('정규직').first()).toBeVisible()
    const bodyText = await page.locator('body').innerText()
    expect(bodyText).not.toMatch(/\d+\s*%|\d+\s*점(?!수)|\d+\s*\/\s*100/)

    // 공고 선택 전에는 ① 추천 공고가 현재 단계 그대로
    await expect(stepIndicator.getByText('추천 공고')).toHaveClass(/bg-brand-blue/)

    // 고용24 AI추천 공고 표시
    const rows = page.getByTestId('capital-posting-list').getByRole('listitem')
    await expect(rows.first()).toBeVisible({ timeout: 10000 })

    // 공고 선택 -> ② 지역 비교 단계로 전환, 기존 AI추천/기존 검증과의 차이는
    // DEMO 정보 팝오버 뒤에 접혀 있다.
    await rows.first().getByRole('button', { name: /지역 비교/ }).click()
    await expect(stepIndicator.getByText('지역 비교')).toHaveClass(/bg-brand-blue/)

    await page.getByText('DEMO · 전북').click()
    await expect(page.getByText('사람과 일자리의 적합성을 분석').first()).toBeVisible()
    await expect(page.getByText('수도권과 자기 지역 일자리의 비교 가능성을 분석').first()).toBeVisible()
  })
})

test.describe('모바일 뷰포트', () => {
  test.use({ viewport: { width: 390, height: 844 } })

  test('AI추천 목록과 비교 패널이 모바일에서 가로 스크롤 없이 세로로 쌓인다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    const rows = page.getByTestId('capital-posting-list').getByRole('listitem')
    await expect(rows.first()).toBeVisible({ timeout: 10000 })

    await rows.first().getByRole('button', { name: /지역 비교/ }).click()
    const panel = page.getByTestId('jeonbuk-comparison-panel')
    const candidateButton = panel.locator('ul > li button').first()
    await expect(candidateButton).toBeVisible({ timeout: 10000 })
    await candidateButton.click()
    const dialog = page.getByRole('dialog')
    const jeonbukError = panel.getByText(/후보:/)
    await expect(dialog.or(jeonbukError)).toBeVisible({ timeout: 15000 })

    const hasHorizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    )
    expect(hasHorizontalOverflow).toBe(false)
  })
})
