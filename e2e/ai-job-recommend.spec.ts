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
    await expect(page.getByRole('heading', { name: 'AI추천 일자리' })).toBeVisible()

    // 데모 고지는 항상 접근 가능해야 하지만, 화면을 차지하지 않도록 DEMO ·
    // 전북 칩 뒤로 접혀 있다 (TASK "UI 고도화" section 5).
    await expect(page.getByText('DEMO · 전북')).toBeVisible()
    await expect(page.getByText('데모 모드 · 사전 검증된 분석 결과')).toBeHidden()
    await page.getByText('DEMO · 전북').click()
    await expect(page.getByText('데모 모드 · 사전 검증된 분석 결과')).toBeVisible()
    await expect(page.getByText('본 서비스는 고용24 공식 서비스가 아닌 해커톤 시연용 프로토타입입니다.')).toBeVisible()
  })

  test('로그인 전에는 안내 문구와 데모 로그인 버튼이 보인다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await expect(page.getByText('로그인하면 관심 생활권의 공고를 함께 비교할 수 있습니다.')).toBeVisible()
    await expect(page.getByRole('button', { name: /전북 데모 프로필로 시작/ })).toBeVisible()
  })

  test('데모 로그인 후 프로필 요약이 한 줄로 표시된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByRole('button', { name: /전북 데모 프로필로 시작/ }).click()

    const profileLine = page.getByText('전북 청년 데모 사용자')
    await expect(profileLine).toBeVisible()
    const profileText = await profileLine.locator('..').innerText()
    expect(profileText).toContain('식품 연구개발')
    expect(profileText).toContain('정규직')
    expect(profileText).toContain('전북특별자치도')

    await page.getByRole('button', { name: '로그아웃' }).click()
    await expect(page.getByRole('button', { name: /전북 데모 프로필로 시작/ })).toBeVisible()
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

  test('공고를 선택하면 우측 패널에 전북 비교 후보가 최대 3건, 유사도 순위가 아니라는 안내와 함께 표시된다', async ({
    page,
  }) => {
    await page.goto('/ai-job-recommend')
    const list = page.getByTestId('capital-posting-list')
    const rows = list.getByRole('listitem')
    await expect(rows.first()).toBeVisible({ timeout: 10000 })

    const panel = page.getByTestId('jeonbuk-comparison-panel')
    await expect(panel.getByText('왼쪽 목록에서 공고를 선택하면')).toBeVisible()

    await rows.first().getByRole('button', { name: /지역 비교/ }).click()
    await expect(panel.getByText('전북 비교 공고')).toBeVisible()

    const candidateItems = panel.locator('ul > li')
    await expect(candidateItems.first()).toBeVisible({ timeout: 10000 })
    const count = await candidateItems.count()
    expect(count).toBeGreaterThan(0)
    expect(count).toBeLessThanOrEqual(3)

    await expect(panel.getByText('표시 순서는 유사도 순위가 아닙니다.')).toBeVisible()

    // 금지 표현: 유사도 점수, 최적, 적합도, 검증된 매칭 등은 어디에도 없어야 함.
    const panelText = await panel.innerText()
    expect(panelText).not.toMatch(/유사도 상위|가장 유사한|최적의 전북|적합도 \d|추천 점수|검증된 매칭/)
  })

  test('다른 수도권 공고를 선택하면 우측 패널이 그 공고 기준으로 갱신된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    const list = page.getByTestId('capital-posting-list')
    const rows = list.getByRole('listitem')
    await expect(rows.first()).toBeVisible({ timeout: 10000 })
    const rowCount = await rows.count()
    test.skip(rowCount < 2, '비교할 두 번째 수도권 공고가 없음')

    const panel = page.getByTestId('jeonbuk-comparison-panel')

    await rows.nth(0).getByRole('button', { name: /지역 비교/ }).click()
    await expect(panel.getByText('전북 비교 공고')).toBeVisible()
    const firstSelectedName = (await rows.nth(0).locator('p').first().innerText()).trim()
    await expect(panel.getByText(firstSelectedName)).toBeVisible()

    await rows.nth(1).getByRole('button', { name: /지역 비교/ }).click()
    const secondSelectedName = (await rows.nth(1).locator('p').first().innerText()).trim()
    await expect(panel.getByText(secondSelectedName)).toBeVisible()
    await expect(rows.nth(1).getByRole('button')).toHaveAttribute('aria-pressed', 'true')
    await expect(rows.nth(0).getByRole('button')).toHaveAttribute('aria-pressed', 'false')
  })

  test('두 번째 전북 후보를 선택하면 선택 상태와 분석 대상이 갱신된다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    const list = page.getByTestId('capital-posting-list')
    const rows = list.getByRole('listitem')
    await expect(rows.first()).toBeVisible({ timeout: 10000 })

    const panel = page.getByTestId('jeonbuk-comparison-panel')
    await rows.first().getByRole('button', { name: /지역 비교/ }).click()

    const candidateButtons = panel.locator('ul > li button')
    await expect(candidateButtons.first()).toBeVisible({ timeout: 10000 })
    const candidateCount = await candidateButtons.count()
    test.skip(candidateCount < 2, '이 수도권 공고에는 비교 후보가 2건 미만이라 후보 전환을 검증할 수 없음')

    const first = candidateButtons.nth(0)
    const second = candidateButtons.nth(1)
    const secondCandidateLabel = (await second.locator('span').first().innerText()).trim()

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
    // both outcomes without assuming either one. On success, the report
    // modal opens automatically with the *second* candidate's info -- see
    // e2e/comparison-report-modal.spec.ts for the modal's own coverage.
    const dialog = page.getByRole('dialog')
    const jeonbukErrorAlert = panel.getByText(/후보:/)
    await expect(dialog.or(jeonbukErrorAlert)).toBeVisible({ timeout: 15000 })

    if (await dialog.isVisible()) {
      await expect(dialog.getByText(secondCandidateLabel).first()).toBeVisible()
    }
  })

  // TASK "기술 영문 제거·연구직 시연 전환·UI 고도화" section 15 items 1-3, 15-16.
  test('영문 데이터셋 설명과 개발 문서 파일명이 화면 어디에도 노출되지 않는다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    const list = page.getByTestId('capital-posting-list')
    await expect(list.getByRole('listitem').first()).toBeVisible({ timeout: 10000 })
    await list.getByRole('listitem').first().getByRole('button', { name: /지역 비교/ }).click()
    await expect(page.getByTestId('jeonbuk-comparison-panel').getByText('전북 비교 공고')).toBeVisible()

    const bodyText = await page.locator('body').innerText()
    expect(bodyText).not.toMatch(/These comparison postings|REAL_DATA_ACQUISITION_HANDOFF|deterministic collection order|MVP dataset/i)
    // 백엔드 원시 지역 코드 리터럴("jeonbuk")도 사용자 문구에 노출되지 않아야 한다.
    expect(bodyText).not.toMatch(/\bjeonbuk\b/)
  })

  test('한국어 데이터 안내가 DEMO 칩을 통해 항상 접근 가능하다', async ({ page }) => {
    await page.goto('/ai-job-recommend')
    await page.getByText('DEMO · 전북').click()
    await expect(
      page.getByText('실제 고용24 공고 표본을 활용한 해커톤 시연입니다. 같은 직종과 고용형태의 전북 공고를 표시하며, 표시'),
    ).toBeVisible()
  })

  test('실제 식품 연구개발 페어가 프로필과 추천 목록 최상단에 일관되게 표시된다', async ({
    page,
  }) => {
    await page.goto('/ai-job-recommend')
    const chipRow = page.getByLabel('현재 시연 직종·고용형태·생활권')
    await expect(chipRow.getByText('식품 연구개발')).toBeVisible()

    await page.getByRole('button', { name: /전북 데모 프로필로 시작/ }).click()
    const profileText = await page.getByText('전북 청년 데모 사용자').locator('..').innerText()
    expect(profileText).toContain('식품 연구개발')

    const list = page.getByTestId('capital-posting-list')
    await expect(list.getByRole('listitem').first()).toBeVisible({ timeout: 10000 })
    const firstPosting = list.getByRole('listitem').first()
    await expect(firstPosting).toContainText('주식회사누리지에프에스')
    await expect(firstPosting).toContainText('식품공학 기술자 및 연구원')

    await firstPosting.getByRole('button', { name: /지역 비교/ }).click()
    const panel = page.getByTestId('jeonbuk-comparison-panel')
    await expect(panel.getByText('(주)참고을 지평선 제2공장')).toBeVisible()
    await expect(panel.getByText(/식품공학 기술자 및 연구원/).first()).toBeVisible()
  })
})
