/**
 * Promo capture using system Edge/Chrome (no Chromium download).
 * Run from repo root or wiki-web:
 *   node docs/promo/capture_promo.mjs
 */
import { createRequire } from 'module'
import { pathToFileURL } from 'url'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const wikiWeb = path.resolve(__dirname, '../../apps/wiki-web')
const require = createRequire(path.join(wikiWeb, 'package.json'))
const { chromium } = require('playwright')
const OUT = path.join(__dirname, 'shots')
const VID = path.join(__dirname, 'out')
const BASE = 'http://127.0.0.1:5173'
fs.mkdirSync(OUT, { recursive: true })
fs.mkdirSync(VID, { recursive: true })

const SHOTS = [
  ['/', '01-home.png'],
  ['/pages', '02-pages.png'],
  ['/weekly', '02b-weekly.png'],
  ['/ask', '06-ask.png'],
  ['/threads', '04-threads-list.png'],
  ['/experiments', '05-experiments.png'],
  ['/skills', '07-skills.png'],
]

async function probePaper() {
  try {
    const r = await fetch('http://127.0.0.1:8787/api/wiki/pages')
    const data = await r.json()
    const items = Array.isArray(data) ? data : data.pages || data.items || []
    const ranked = items.filter((p) => p && (p.path || p.id))
    const prefer = ranked.find((p) => {
      const path = String(p.path || p.id)
      return !path.includes('fake') && !path.includes('demo/')
    })
    const hit = prefer || ranked[0]
    if (hit) return hit.path || hit.id
  } catch {}
  return null
}

async function launch() {
  for (const channel of ['msedge', 'chrome', undefined]) {
    try {
      return await chromium.launch({
        headless: true,
        ...(channel ? { channel } : {}),
      })
    } catch (e) {
      console.warn('launch fail', channel || 'bundled', String(e.message || e))
    }
  }
  throw new Error('No browser available')
}

const browser = await launch()
const paper = await probePaper()
const threadId = 'mm-llm-alignment'

const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 1.5,
  locale: 'zh-CN',
})
const page = await context.newPage()

for (const [route, name] of SHOTS) {
  const url = BASE + route
  console.log('shot', name, url)
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 })
  await page.waitForTimeout(700)
  await page.screenshot({ path: path.join(OUT, name) })
}

if (paper) {
  const url = `${BASE}/page/${paper}`
  console.log('shot 03-read-dual.png', url)
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 })
  await page.waitForTimeout(900)
  await page.screenshot({ path: path.join(OUT, '03-read-dual.png') })
}

{
  const url = `${BASE}/threads/${threadId}`
  console.log('shot 04-thread.png', url)
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 })
  await page.waitForTimeout(900)
  await page.screenshot({ path: path.join(OUT, '04-thread.png') })
}

await context.close()

// Video needs playwright ffmpeg; if missing, still emit shot list for slideshow assembler
let videoOk = true
try {
  const context2 = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1.25,
    recordVideo: { dir: VID, size: { width: 1440, height: 900 } },
  })
  const page2 = await context2.newPage()
  const tour = [
    ['/', 2000],
    ['/pages', 2200],
    [paper ? `/page/${paper}` : '/pages', 3000],
    [`/threads/${threadId}`, 3000],
    ['/experiments', 2200],
    ['/ask', 2200],
    ['/', 1600],
  ]
  for (const [route, dwell] of tour) {
    console.log('tour', route)
    await page2.goto(BASE + route, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page2.waitForTimeout(dwell)
  }
  const video = page2.video()
  await context2.close()
  if (video) {
    const vpath = await video.path()
    const dest = path.join(VID, 'paper-rec-grad-demo.webm')
    try {
      fs.renameSync(vpath, dest)
    } catch {
      fs.copyFileSync(vpath, dest)
    }
    console.log('video ->', dest)
  }
} catch (e) {
  videoOk = false
  console.warn('video skipped:', String(e.message || e).split('\n')[0])
}

await browser.close()
console.log('shots ->', OUT)
if (!videoOk) console.log('run: python docs/promo/make_slideshow.py')
