// Script ponctuel pour capturer des écrans de l'application pour le rapport de stage.
// N'est pas un test : ne pas l'exécuter via `npx playwright test` (voir rapport-de-stage/).
// Usage : node scripts/captures.cjs
const { chromium } = require('@playwright/test')
const path = require('path')

const BASE_URL = 'http://localhost:5173'
const DEST = path.join(__dirname, '..', '..', 'rapport-de-stage', 'images')
const MOT_DE_PASSE = 'Demo1234!'

async function connecter(page, matricule) {
  await page.goto(`${BASE_URL}/connexion`)
  await page.getByLabel('Matricule').fill(matricule)
  await page.getByLabel('Mot de passe').fill(MOT_DE_PASSE)
  await page.getByRole('button', { name: 'Se connecter' }).click()
  await page.waitForURL(/mes-demandes/)
}

async function deconnecter(page) {
  await page.getByRole('button', { name: 'Déconnexion' }).click()
  await page.waitForURL(/connexion/)
}

async function shot(page, nom) {
  await page.screenshot({ path: path.join(DEST, nom), fullPage: true })
  console.log('capturé :', nom)
}

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.setViewportSize({ width: 1440, height: 900 })

  // 1. Connexion
  await page.goto(`${BASE_URL}/connexion`)
  await shot(page, '01-connexion.png')

  // 2. Agent : nouvelle demande (formulaire avec justificatifs dynamiques)
  await connecter(page, 'AG001')
  await page.getByRole('link', { name: 'Nouvelle demande' }).click()
  await page.getByLabel('Type de congé').selectOption({ label: 'Congé de maladie (courte durée)' })
  const debut = new Date()
  debut.setDate(debut.getDate() + 20)
  const fin = new Date(debut)
  fin.setDate(fin.getDate() + 10)
  const fmt = (d) => d.toISOString().slice(0, 10)
  await page.getByLabel('Date de début').fill(fmt(debut))
  await page.getByLabel('Date de fin souhaitée').fill(fmt(fin))
  await shot(page, '02-nouvelle-demande.png')
  await page.getByRole('button', { name: 'Continuer' }).click()
  await page.getByRole('heading', { name: 'Pièces justificatives' }).waitFor()
  await shot(page, '03-justificatifs.png')

  // 3. Mes demandes
  await page.goto(`${BASE_URL}/mes-demandes`)
  await page.locator('table, .liste-vide').first().waitFor()
  await shot(page, '04-mes-demandes.png')

  // 4. Créer et soumettre une demande de congé exceptionnel (sans justificatif) pour la faire
  // avancer dans tout le circuit et illustrer le détail + l'attestation.
  await page.goto(`${BASE_URL}/nouvelle-demande`)
  await page.getByLabel('Type de congé').selectOption({ label: 'Congé exceptionnel' })
  const debut2 = new Date()
  debut2.setDate(debut2.getDate() + 45)
  const fin2 = new Date(debut2)
  fin2.setDate(fin2.getDate() + 2)
  await page.getByLabel('Date de début').fill(fmt(debut2))
  await page.getByLabel('Date de fin souhaitée').fill(fmt(fin2))
  await page.getByRole('button', { name: 'Continuer' }).click()
  await page.getByRole('button', { name: 'Soumettre la demande' }).click()
  await page.waitForURL(/mes-demandes/)
  await page.getByRole('link', { name: 'Voir' }).first().click()
  const demandeUrl = page.url()
  await page.getByRole('heading', { name: 'Circuit de validation' }).waitFor()
  await shot(page, '05-detail-demande-en-cours.png')
  await deconnecter(page)

  // 5. Chef de service : inbox puis décision
  await connecter(page, 'CS001')
  await page.getByRole('link', { name: 'À valider' }).click()
  await page.locator('table, .liste-vide').first().waitFor()
  await shot(page, '06-a-valider.png')
  await page.getByRole('link', { name: 'Examiner' }).first().click()
  await page.getByRole('heading', { name: 'Votre décision' }).waitFor()
  await shot(page, '07-decision-validation.png')
  await page.getByLabel('Commentaire').fill('Avis favorable.')
  await page.getByRole('button', { name: 'Approuver' }).click()
  await page.getByRole('button', { name: 'Approuver' }).waitFor({ state: 'detached' })
  await deconnecter(page)

  // 6. Directeur approuve
  await connecter(page, 'DIR001')
  await page.getByRole('link', { name: 'À valider' }).click()
  await page.getByRole('link', { name: 'Examiner' }).first().click()
  await page.getByLabel('Commentaire').fill('Accord.')
  await page.getByRole('button', { name: 'Approuver' }).click()
  await page.getByRole('button', { name: 'Approuver' }).waitFor({ state: 'detached' })
  await deconnecter(page)

  // 7. Chef de cabinet approuve -> attestation générée
  await connecter(page, 'CC001')
  await page.getByRole('link', { name: 'À valider' }).click()
  await page.getByRole('link', { name: 'Examiner' }).first().click()
  await page.getByLabel('Commentaire').fill('Validé.')
  await page.getByRole('button', { name: 'Approuver' }).click()
  await page.getByRole('heading', { name: 'Attestation' }).waitFor()
  await shot(page, '08-attestation-generee.png')
  await deconnecter(page)

  // 8. RH : administration
  await connecter(page, 'RH001')
  await page.getByRole('link', { name: 'Agents' }).click()
  await page.getByRole('heading', { name: 'Administration — Comptes agents' }).waitFor()
  await page.getByRole('cell', { name: 'AG001' }).first().waitFor()
  await shot(page, '09-administration-agents.png')
  await page.getByRole('link', { name: 'Organisation' }).click()
  await page.getByRole('heading', { name: 'Administration — Directions et services' }).waitFor()
  await page.getByRole('cell', { name: 'Direction du Budget' }).first().waitFor()
  await shot(page, '10-administration-organisation.png')

  await browser.close()
  console.log('Terminé. Demande utilisée pour les captures 05-08 :', demandeUrl)
})()
