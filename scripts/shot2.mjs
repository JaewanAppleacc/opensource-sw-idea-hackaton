import { chromium } from 'playwright-core'

const url = 'http://localhost:5183/'
const browser = await chromium.launch()

// Desktop: GNB dropdown open
{
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto(url, { waitUntil: 'load' })
  await page.getByRole('button', { name: '채용정보', exact: true }).click()
  await page.waitForTimeout(200)
  await page.screenshot({ path: 'shots/desktop-gnb-open.png' })

  await page.getByRole('button', { name: '전체 메뉴' }).click()
  await page.waitForTimeout(200)
  await page.screenshot({ path: 'shots/desktop-allmenu-open.png' })
  await page.close()
}

// Mobile: hamburger menu open
{
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
  await page.goto(url, { waitUntil: 'load' })
  await page.getByRole('button', { name: '전체 메뉴 열기' }).click()
  await page.waitForTimeout(200)
  await page.screenshot({ path: 'shots/mobile-menu-open.png' })
  await page.close()
}

// Hero search close-up
{
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto(url, { waitUntil: 'load' })
  const box = await page.locator('form').first().boundingBox()
  if (box) {
    await page.screenshot({
      path: 'shots/hero-search-closeup.png',
      clip: { x: box.x - 20, y: box.y - 20, width: box.width + 40, height: box.height + 40 },
    })
  }
  await page.close()
}

await browser.close()
