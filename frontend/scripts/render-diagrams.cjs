// Rendu ponctuel des diagrammes Mermaid de docs/04-diagrammes-uml.md en PNG pour le rapport.
const { chromium } = require('@playwright/test')
const path = require('path')

const HTML = 'file:///' + 'C:/Users/clusa/AppData/Local/Temp/mermaid-render/diagrams.html'
const DEST = path.join(__dirname, '..', '..', 'rapport-de-stage', 'images', 'diagrammes')

const noms = [
  '01-cas-utilisation.png',
  '02-classes.png',
  '03-sequence.png',
  '04-etat-demande.png',
  '05-etat-etape.png',
]

;(async () => {
  const fs = require('fs')
  fs.mkdirSync(DEST, { recursive: true })

  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 2200, height: 1600 }, deviceScaleFactor: 2 })
  await page.goto(HTML)
  await page.waitForSelector('#wrap-5 svg')
  await page.waitForTimeout(300)

  for (let i = 0; i < 5; i++) {
    const el = await page.$(`#wrap-${i + 1}`)
    await el.screenshot({ path: path.join(DEST, noms[i]) })
    console.log('rendu :', noms[i])
  }

  await browser.close()
})()
