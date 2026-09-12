import { expect, test } from '@playwright/test'

test.describe('고용24 클론 메인페이지', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('핵심 랜드마크와 제목이 렌더링된다', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /나만의 고용서비스/ })).toBeVisible()
    await expect(page.getByRole('banner').first()).toBeDefined()
    await expect(page.locator('footer')).toContainText('비공식 학습용 클론')
  })

  test('콘솔 에러 없이 로드된다', async ({ page }) => {
    const errors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text())
    })
    page.on('pageerror', (err) => errors.push(String(err)))
    await page.reload()
    await page.waitForTimeout(500)
    expect(errors).toEqual([])
  })

  test('가로 스크롤(오버플로)이 발생하지 않는다', async ({ page }) => {
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    expect(overflow).toBeLessThanOrEqual(1)
  })

  test('서비스 탭을 클릭하면 활성 탭과 퀵메뉴 내용이 바뀐다', async ({ page }) => {
    const findTab = page.getByRole('tab', { name: '일자리 찾기' })
    const trainingTab = page.getByRole('tab', { name: '훈련 역량 강화' })

    await expect(findTab).toHaveAttribute('aria-selected', 'true')
    await expect(page.getByRole('tabpanel')).toContainText('일자리 찾기')

    await trainingTab.click()
    await expect(trainingTab).toHaveAttribute('aria-selected', 'true')
    await expect(findTab).toHaveAttribute('aria-selected', 'false')
    await expect(page.getByRole('tabpanel')).toContainText('국민내일배움카드')
  })

  test('통합검색 제출 시 실제 이동 없이 mock 토스트가 표시된다', async ({ page }) => {
    const input = page.getByPlaceholder('필요한 서비스를 검색해보세요')
    await input.fill('실업급여')
    await input.press('Enter')
    await expect(page.getByRole('status')).toContainText('실업급여')
    await expect(page).toHaveURL(/\/$/)
  })

  test('빈 검색어로 제출하면 안내 토스트가 표시된다', async ({ page }) => {
    await page.getByRole('button', { name: '통합검색 실행' }).click()
    await expect(page.getByRole('status')).toContainText('검색어를 입력해 주세요')
  })

  test('데스크톱 핵심 요소가 기준 화면과 같은 강조 비율을 유지한다', async ({ page, viewport }) => {
    test.skip(!viewport || viewport.width < 1024, '데스크톱 전용 시각 비율 테스트')

    const searchBox = await page.getByPlaceholder('필요한 서비스를 검색해보세요').locator('..').boundingBox()
    const firstQuickIcon = await page.getByRole('tabpanel').locator('a').first().locator('span').first().boundingBox()

    expect(searchBox?.height).toBeGreaterThanOrEqual(60)
    expect(firstQuickIcon?.width).toBeGreaterThanOrEqual(130)
    await expect(page.getByText('많이 찾은 검색어')).toHaveCount(0)
  })

  test('프로모션 배너 캐러셀 이전/다음/정지가 동작한다', async ({ page }) => {
    const counter = page.locator('text=/\\d \\/ \\d/').first()
    await expect(counter).toHaveText('1 / 4')

    await page.getByRole('button', { name: '다음 프로모션' }).click()
    await expect(counter).toHaveText('2 / 4')

    await page.getByRole('button', { name: '이전 프로모션' }).click()
    await expect(counter).toHaveText('1 / 4')

    const pauseBtn = page.getByRole('button', { name: '프로모션 자동재생 정지' })
    await pauseBtn.click()
    await expect(page.getByRole('button', { name: '프로모션 자동재생 시작' })).toBeVisible()
  })

  test('맨 위로 버튼 클릭 시 스크롤이 맨 위로 이동한다', async ({ page }) => {
    await page.evaluate(() => window.scrollTo(0, 2000))
    await expect
      .poll(() => page.evaluate(() => window.scrollY))
      .toBeGreaterThan(500)

    await page.getByRole('button', { name: '맨 위로 이동' }).click()
    await expect.poll(() => page.evaluate(() => window.scrollY), { timeout: 3000 }).toBeLessThan(50)
  })

  test('챗봇/도우미 플로팅 버튼 클릭 시 데모 안내 토스트가 표시된다', async ({ page }) => {
    await page.getByRole('button', { name: '챗봇 상담 열기' }).click()
    await expect(page.getByRole('status')).toContainText('챗봇')
  })
})

test.describe('데스크톱 GNB 드롭다운', () => {
  test.skip(({ viewport }) => !viewport || viewport.width < 1024, '데스크톱 전용 GNB 테스트')

  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('클릭으로 드롭다운을 열고 Escape로 닫을 수 있다', async ({ page }) => {
    const trigger = page.getByRole('button', { name: '채용정보', exact: true })
    await trigger.click()
    await expect(trigger).toHaveAttribute('aria-expanded', 'true')
    await expect(page.getByRole('link', { name: /채용정보 검색/ })).toBeVisible()

    await page.keyboard.press('Escape')
    await expect(trigger).toHaveAttribute('aria-expanded', 'false')
  })

  test('전체 메뉴 버튼으로 전체 내비게이션 패널을 열 수 있다', async ({ page }) => {
    await page.getByRole('button', { name: '전체 메뉴' }).click()
    await expect(page.getByRole('dialog', { name: '전체 메뉴' })).toBeVisible()
    await page.getByRole('button', { name: '메뉴 닫기' }).click()
    await expect(page.getByRole('dialog', { name: '전체 메뉴' })).toBeHidden()
  })
})

test.describe('퀵메뉴 캐러셀 페이지네이션', () => {
  test.skip(({ viewport }) => !viewport || viewport.width < 1024, '데스크톱 전용 캐러셀 테스트')

  test('아이템이 6개보다 많은 탭에서 다음/이전 페이지 전환이 동작한다', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('tab', { name: '훈련 역량 강화' }).click()

    const panel = page.getByRole('tabpanel')
    await expect(panel).toContainText('중장년 내일센터')

    await page.getByRole('button', { name: '퀵메뉴 다음' }).click()
    await expect(panel).toContainText('직장적응지원')

    await page.getByRole('button', { name: '퀵메뉴 이전' }).click()
    await expect(panel).toContainText('중장년 내일센터')
  })
})

test.describe('모바일 내비게이션', () => {
  test.skip(({ viewport }) => !viewport || viewport.width >= 1024, '모바일 전용 메뉴 테스트')

  test('햄버거 버튼으로 메뉴를 열고 아코디언과 닫기 버튼이 동작한다', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: '전체 메뉴 열기' }).click()

    const dialog = page.getByRole('dialog', { name: '전체 메뉴' })
    await expect(dialog).toBeVisible()

    await dialog.getByText('채용정보', { exact: true }).click()
    await expect(dialog.getByRole('link', { name: /채용정보 검색/ })).toBeVisible()

    await page.getByRole('button', { name: '메뉴 닫기' }).click()
    await expect(dialog).toBeHidden()
  })
})
