import { chromium } from 'playwright-core'
import fs from 'node:fs'

const url = process.env.SHOT_URL ?? 'http://localhost:5183/'
const outDir = 'shots'
fs.mkdirSync(outDir, { recursive: true })

const viewports = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'mobile', width: 390, height: 844 },
]

const browser = await chromium.launch()
for (const vp of viewports) {
  const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } })
  const errors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text())
  })
  page.on('pageerror', (err) => errors.push(String(err)))
  await page.goto(url, { waitUntil: 'load' })
  await page.waitForTimeout(700)
  await page.screenshot({ path: `${outDir}/${vp.name}-viewport.png` })
  await page.screenshot({ path: `${outDir}/${vp.name}-full.png`, fullPage: true })

  const overflow = await page.evaluate(() => {
    return document.documentElement.scrollWidth - document.documentElement.clientWidth
  })
  console.log(`[${vp.name}] horizontal overflow px:`, overflow, 'console errors:', errors.length)
  if (errors.length) console.log(errors)
  await page.close()
}
await browser.close()
