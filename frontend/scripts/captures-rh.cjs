// Reprise ciblée des captures RH (09, 10) après nettoyage des données de test.
const { chromium } = require('@playwright/test')
const path = require('path')

const BASE_URL = 'http://localhost:5173'
const DEST = path.join(__dirname, '..', '..', 'rapport-de-stage', 'images')

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })

  await page.goto(`${BASE_URL}/connexion`)
  await page.getByLabel('Matricule').fill('RH001')
  await page.getByLabel('Mot de passe').fill('Demo1234!')
  await page.getByRole('button', { name: 'Se connecter' }).click()
  await page.waitForURL(/mes-demandes/)

  await page.getByRole('link', { name: 'Agents' }).click()
  await page.getByRole('heading', { name: 'Administration — Comptes agents' }).waitFor()
  await page.getByRole('cell', { name: 'AG001' }).first().waitFor()
  await page.screenshot({ path: path.join(DEST, '09-administration-agents.png'), fullPage: true })
  console.log('capturé : 09-administration-agents.png')

  await page.getByRole('link', { name: 'Organisation' }).click()
  await page.getByRole('heading', { name: 'Administration — Directions et services' }).waitFor()
  await page.getByRole('cell', { name: 'Direction du Budget' }).first().waitFor()
  await page.screenshot({ path: path.join(DEST, '10-administration-organisation.png'), fullPage: true })
  console.log('capturé : 10-administration-organisation.png')

  await browser.close()
})()
