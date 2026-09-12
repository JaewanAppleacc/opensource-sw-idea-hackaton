import { chromium } from 'playwright-core'

const url = 'http://localhost:5183/'
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
const errors = []
page.on('pageerror', (e) => errors.push(String(e)))
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })

await page.goto(url, { waitUntil: 'load' })
await page.getByRole('link', { name: /AI추천\(일자리\)/ }).click()
await page.waitForTimeout(300)
console.log('url after click:', page.url())
await page.screenshot({ path: 'shots3-1-form.png', fullPage: true })

await page.getByRole('button', { name: '데모 공고 불러오기' }).click()
await page.waitForTimeout(200)
await page.screenshot({ path: 'shots3-2-demo-loaded.png', fullPage: true })

await page.getByRole('button', { name: '공고 분석하기' }).click()
await page.waitForTimeout(300)
await page.screenshot({ path: 'shots3-3-submitted.png', fullPage: true })

console.log('errors:', errors)
await browser.close()
