import { expect, type Page, test } from '@playwright/test'

/**
 * Coverage for the step-by-step comparison report dialog (TASK "단계형
 * 리포트 모달"). Real backend, LLM_PROVIDER=mock. Most scenarios need both
 * postings' analyses to actually succeed, which requires real private
 * posting text staged locally under data/private/intake_raw/** -- when it
 * is not staged (this repo's default state on a fresh checkout), every
 * analyze call fails closed and the modal never opens by design (see test
 * "백엔드 장애 시..." below, which specifically exercises that path and does
 * NOT skip). All other tests that need a successful report follow the same
 * test.skip convention as e2e/inline-jeonbuk-agent.spec.ts.
 */
test.describe('비교 리포트 모달', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => window.localStorage.clear())
  })

  async function selectFirstCapitalPosting(page: Page) {
    await page.goto('/ai-job-recommend')
    await page.getByRole('button', { name: /전북 데모 프로필로 시작/ }).click()
    const rows = page.getByTestId('capital-posting-list').getByRole('listitem')
    await expect(rows.first()).toBeVisible({ timeout: 10000 })
    await rows.first().getByRole('button', { name: /지역 비교/ }).click()
  }

  /** Selects the first 전북 후보 and waits for the settle. Returns whether
   * both analyses actually succeeded (dialog opened) so callers can skip
   * dialog-dependent assertions the same way the rest of the suite does. */
  async function selectFirstCandidateAndWait(page: Page): Promise<boolean> {
    const sidePanel = page.getByTestId('jeonbuk-comparison-panel')
    const candidateButton = sidePanel.locator('ul > li button').first()
    await expect(candidateButton).toBeVisible({ timeout: 10000 })
    await candidateButton.click()

    const dialog = page.getByRole('dialog')
    const jeonbukError = sidePanel.getByText(/후보:/)
    await expect(dialog.or(jeonbukError)).toBeVisible({ timeout: 15000 })
    return await dialog.isVisible()
  }

  test('1. 수도권 공고 선택 후 전북 후보가 최대 3건 표시된다', async ({ page }) => {
    await selectFirstCapitalPosting(page)
    const sidePanel = page.getByTestId('jeonbuk-comparison-panel')
    const candidates = sidePanel.locator('ul > li button')
    await expect(candidates.first()).toBeVisible({ timeout: 10000 })
    expect(await candidates.count()).toBeLessThanOrEqual(3)
    await expect(page.getByRole('dialog')).toHaveCount(0)
  })

  test('2-3. 전북 후보 선택 시 분석 완료 후 dialog가 열리고 두 기업명과 제목이 보인다', async ({ page }) => {
    await selectFirstCapitalPosting(page)
    const succeeded = await selectFirstCandidateAndWait(page)
    test.skip(!succeeded, 'data/private/intake_raw/**가 이 머신에 없어 분석이 fail-closed로 종료됨')

    const dialog = page.getByRole('dialog')
    await expect(dialog).toHaveAttribute('aria-modal', 'true')
    await expect(dialog).toHaveAttribute('aria-labelledby', 'comparison-report-title')
    // 시각적 제목(h2)만 대상으로 한다 -- ReportProgress의 sr-only aria-live
    // 안내문("N/6단계: {제목}")도 같은 문자열을 포함하므로 getByText만 쓰면
    // strict-mode violation이 난다.
    await expect(dialog.getByRole('heading', { name: '두 공고를 같은 기준으로 살펴봤어요' })).toBeVisible()
    await expect(dialog.getByText('수도권 공고').first()).toBeVisible()
    await expect(dialog.getByText('전북특별자치도 후보', { exact: false })).toBeVisible()
    await expect(dialog.getByText('동일 모집직종·고용형태 그룹의 비교 공고')).toBeVisible()
    // 우승/승자/추천 점수 없음 -- 모달 전체 범위.
    const dialogText = await dialog.innerText()
    expect(dialogText).not.toMatch(/승자|추천 점수|적합도 \d|가장 유사한|최적의|더 좋은 기업/)
  })

  test('4-5. 다음/이전 버튼으로 단계를 이동하면 제목과 progress가 갱신된다', async ({ page }) => {
    await selectFirstCapitalPosting(page)
    const succeeded = await selectFirstCandidateAndWait(page)
    test.skip(!succeeded, 'data/private/intake_raw/**가 이 머신에 없어 분석이 fail-closed로 종료됨')

    const dialog = page.getByRole('dialog')
    await expect(dialog.getByText('1/6단계', { exact: false })).toBeAttached()

    await dialog.getByRole('button', { name: '다음' }).click()
    await expect(dialog.getByRole('heading', { name: '지원 판단에 필요한 조건을 비교했어요' })).toBeVisible()
    await expect(dialog.getByText('2/6단계', { exact: false })).toBeAttached()

    await dialog.getByRole('button', { name: '이전' }).click()
    await expect(dialog.getByRole('heading', { name: '두 공고를 같은 기준으로 살펴봤어요' })).toBeVisible()
    await expect(dialog.getByRole('button', { name: '이전' })).toBeDisabled()
  })

  test('6-7. 6개 표시축이 모두 렌더링되고 not_evaluated는 별도 표시되어 absent로 집계되지 않는다', async ({ page }) => {
    await selectFirstCapitalPosting(page)
    const succeeded = await selectFirstCandidateAndWait(page)
    test.skip(!succeeded, 'data/private/intake_raw/**가 이 머신에 없어 분석이 fail-closed로 종료됨')

    const dialog = page.getByRole('dialog')
    await dialog.getByRole('button', { name: '다음' }).click() // -> conditions
    // ComparisonReportModal은 전환 애니메이션을 위해 6개 스텝을 전부 동시에
    // DOM에 유지한다(비활성 스텝은 CSS로만 숨김) -- 다른 스텝(우선순위·질문·
    // 요약)도 같은 축 이름 문자열을 재사용하므로, 보이는 요소만 걸러야
    // strict-mode violation 없이 "지금 이 스텝에 실제로 보이는" 라벨만 검증한다.
    for (const label of ['임금·보상', '고용안정성', '담당 업무와 직무 적합성', '필요 역량과 지원조건', '근로시간과 근무환경', '성장·복지 지원']) {
      await expect(dialog.getByText(label).and(page.locator(':visible')).first()).toBeVisible()
    }
    await expect(dialog.getByText('현재 MVP 분석 미지원').and(page.locator(':visible')).first()).toBeVisible()

    // 항목 클릭 전에는 근거 문구가 보이지 않는다 (기본 접힘).
    await expect(dialog.getByText('근거 문구 없음')).toHaveCount(0)

    // 우선 확인할 조건(unknowns)에는 not_evaluated 항목이 절대 나타나지 않는다.
    await dialog.getByRole('button', { name: '다음' }).click() // -> unknowns
    const unknownsText = await dialog.innerText()
    expect(unknownsText).not.toContain('근로시간·교대제·통근')
    expect(unknownsText).not.toContain('복지·기숙사·통근지원')
  })

  test('클릭하면 원문 근거가 펼쳐진다', async ({ page }) => {
    await selectFirstCapitalPosting(page)
    const succeeded = await selectFirstCandidateAndWait(page)
    test.skip(!succeeded, 'data/private/intake_raw/**가 이 머신에 없어 분석이 fail-closed로 종료됨')

    const dialog = page.getByRole('dialog')
    await dialog.getByRole('button', { name: '다음' }).click() // -> conditions
    const firstRow = dialog.locator('button[aria-expanded="false"]').first()
    await firstRow.click()
    await expect(dialog.locator('button[aria-expanded="true"]').first()).toBeVisible()
  })

  test('8. 질문 복사 버튼을 누르면 복사 완료 안내가 표시된다', async ({ page }) => {
    await selectFirstCapitalPosting(page)
    const succeeded = await selectFirstCandidateAndWait(page)
    test.skip(!succeeded, 'data/private/intake_raw/**가 이 머신에 없어 분석이 fail-closed로 종료됨')

    const dialog = page.getByRole('dialog')
    await dialog.getByRole('button', { name: '다음' }).click() // conditions
    await dialog.getByRole('button', { name: '다음' }).click() // unknowns
    await dialog.getByRole('button', { name: '다음' }).click() // questions

    const copyButton = dialog.getByRole('button', { name: '복사' }).first()
    test.skip((await copyButton.count()) === 0, '이 조합에는 확인 질문이 없음')
    await copyButton.click()
    await expect(page.getByText('질문을 복사했어요.')).toBeVisible()
  })

  test('9. 자금 단계는 계산 전에는 안내를, 계산 후에는 결과를 보여준다', async ({ page }) => {
    await selectFirstCapitalPosting(page)
    const succeeded = await selectFirstCandidateAndWait(page)
    test.skip(!succeeded, 'data/private/intake_raw/**가 이 머신에 없어 분석이 fail-closed로 종료됨')

    const dialog = page.getByRole('dialog')
    await dialog.getByRole('button', { name: '다음' }).click() // conditions
    await dialog.getByRole('button', { name: '다음' }).click() // unknowns
    await dialog.getByRole('button', { name: '다음' }).click() // questions
    await dialog.getByRole('button', { name: '다음' }).click() // finance

    await expect(dialog.getByText('조건을 입력하면 계산할 수 있습니다.')).toBeVisible()
    await dialog.getByRole('button', { name: '자금 비교 계산하기' }).click()
    await expect(dialog.getByText('월 가용자금').first()).toBeVisible({ timeout: 10000 })

    await dialog.getByRole('button', { name: '다음' }).click() // summary
    await expect(dialog.getByText('실행함')).toBeVisible()
  })

  test('10-11-14. 마지막 단계에서 닫기, Escape 닫기, 닫은 뒤 focus가 복귀한다', async ({ page }) => {
    await selectFirstCapitalPosting(page)
    const succeeded = await selectFirstCandidateAndWait(page)
    test.skip(!succeeded, 'data/private/intake_raw/**가 이 머신에 없어 분석이 fail-closed로 종료됨')

    const sidePanel = page.getByTestId('jeonbuk-comparison-panel')
    const candidateButton = sidePanel.locator('ul > li button').first()
    const dialog = page.getByRole('dialog')

    for (let i = 0; i < 5; i++) await dialog.getByRole('button', { name: '다음' }).click()
    await expect(dialog.getByRole('heading', { name: '이제 무엇을 확인할지 정리됐어요' })).toBeVisible()
    // 헤더의 아이콘 버튼도 같은 접근성 이름("리포트 닫기")을 쓰므로, 텍스트가
    // 실제로 보이는 마지막 단계의 CTA 버튼만 골라야 한다 (아이콘 버튼은
    // aria-label만 있고 텍스트 노드가 없다).
    await dialog.locator('button', { hasText: '리포트 닫기' }).click()
    await expect(dialog).toHaveCount(0)
    await expect(candidateButton).toBeFocused()

    await page.getByRole('button', { name: '비교 리포트 다시 보기' }).click()
    await expect(page.getByRole('dialog')).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(page.getByRole('dialog')).toHaveCount(0)
  })

  test('12-13. overlay 클릭으로 닫히지만 내부 클릭으로는 닫히지 않는다', async ({ page }) => {
    await selectFirstCapitalPosting(page)
    const succeeded = await selectFirstCandidateAndWait(page)
    test.skip(!succeeded, 'data/private/intake_raw/**가 이 머신에 없어 분석이 fail-closed로 종료됨')

    const dialog = page.getByRole('dialog')
    await dialog.getByRole('heading', { name: '두 공고를 같은 기준으로 살펴봤어요' }).click()
    await expect(dialog).toBeVisible()

    // overlay는 dialog의 부모 -- 좌상단 모서리는 dialog 바깥일 것이다.
    await page.mouse.click(5, 5)
    await expect(page.getByRole('dialog')).toHaveCount(0)
  })

  test('15. 다른 전북 후보를 선택하면 모달이 새 기업 정보로 갱신된다', async ({ page }) => {
    await selectFirstCapitalPosting(page)
    const sidePanel = page.getByTestId('jeonbuk-comparison-panel')
    const candidateButtons = sidePanel.locator('ul > li button')
    await expect(candidateButtons.first()).toBeVisible({ timeout: 10000 })
    const candidateCount = await candidateButtons.count()
    test.skip(candidateCount < 2, '이 수도권 공고에는 비교 후보가 2건 미만')

    const firstLabel = (await candidateButtons.nth(0).locator('span').first().innerText()).trim()
    const secondLabel = (await candidateButtons.nth(1).locator('span').first().innerText()).trim()

    await candidateButtons.nth(0).click()
    const dialog = page.getByRole('dialog')
    const jeonbukError = sidePanel.getByText(/후보:/)
    await expect(dialog.or(jeonbukError)).toBeVisible({ timeout: 15000 })
    test.skip(!(await dialog.isVisible()), 'data/private/intake_raw/**가 이 머신에 없어 분석이 fail-closed로 종료됨')
    await expect(dialog.getByText(firstLabel).first()).toBeVisible()
    await page.keyboard.press('Escape')

    await candidateButtons.nth(1).click()
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 15000 })
    await expect(page.getByRole('dialog').getByText(secondLabel).first()).toBeVisible()
  })

  test('16-17. 영문 데이터셋 설명과 금지 문구가 어디에도 노출되지 않는다', async ({ page }) => {
    await selectFirstCapitalPosting(page)
    await selectFirstCandidateAndWait(page)
    const bodyText = await page.locator('body').innerText()
    expect(bodyText).not.toMatch(/These comparison postings|REAL_DATA_ACQUISITION_HANDOFF|deterministic collection order|MVP dataset/i)
    expect(bodyText).not.toMatch(/최적의 전북|가장 유사한 기업|더 좋은 기업|AI가 깊이 생각|실시간 AI 분석 중|최적의 기업을 선정/)
  })

  test('18. 모바일에서는 리포트가 거의 전체 화면을 채운다', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await selectFirstCapitalPosting(page)
    const succeeded = await selectFirstCandidateAndWait(page)
    test.skip(!succeeded, 'data/private/intake_raw/**가 이 머신에 없어 분석이 fail-closed로 종료됨')

    const dialogBox = await page.getByRole('dialog').boundingBox()
    expect(dialogBox?.width).toBeGreaterThan(370)
    expect(dialogBox?.height).toBeGreaterThan(700)
    const hasHorizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    )
    expect(hasHorizontalOverflow).toBe(false)
  })

  test('19. prefers-reduced-motion에서도 단계 이동이 정상 동작한다', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await selectFirstCapitalPosting(page)
    const succeeded = await selectFirstCandidateAndWait(page)
    test.skip(!succeeded, 'data/private/intake_raw/**가 이 머신에 없어 분석이 fail-closed로 종료됨')

    const dialog = page.getByRole('dialog')
    await dialog.getByRole('button', { name: '다음' }).click()
    await expect(dialog.getByRole('heading', { name: '지원 판단에 필요한 조건을 비교했어요' })).toBeVisible()
  })

  test('20. 백엔드 장애(fail-closed) 시 모달을 가짜 성공 상태로 열지 않는다', async ({ page }) => {
    await selectFirstCapitalPosting(page)
    const sidePanel = page.getByTestId('jeonbuk-comparison-panel')
    const candidateButton = sidePanel.locator('ul > li button').first()
    await expect(candidateButton).toBeVisible({ timeout: 10000 })
    await candidateButton.click()

    const dialog = page.getByRole('dialog')
    const jeonbukError = sidePanel.getByText(/후보:/)
    await expect(dialog.or(jeonbukError)).toBeVisible({ timeout: 15000 })

    if (await jeonbukError.isVisible()) {
      // 실제 fail-closed 경로 -- 모달이 절대 열리지 않아야 한다.
      await expect(dialog).toHaveCount(0)
      await expect(sidePanel.getByText('비교 리포트', { exact: false })).toHaveCount(0)
    }
    // 두 분석이 모두 성공한 경우(private 데이터가 있는 머신)에는 이 시나리오
    // 자체가 재현되지 않으므로 별도 스킵 없이 여기서 종료한다.
  })
})
