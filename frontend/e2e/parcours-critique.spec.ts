import { expect, test, type Page } from '@playwright/test'

/**
 * Parcours critique : connexion agent -> soumission d'une demande -> approbation aux 3 niveaux
 * hiérarchiques (chef de service, directeur, chef de cabinet) -> génération de l'attestation.
 *
 * Utilise les comptes créés par `python manage.py seed_demo` (voir backend/conges/management/
 * commands/seed_demo.py) : AG001/CS001/DIR001/CC001, mot de passe Demo1234!.
 *
 * Note de portée : le code de vérification embarqué dans le QR code de l'attestation n'est
 * exposé que dans le PDF généré (jamais par l'API, volontairement — voir conges/serializers.py).
 * Le rendu positif de la page /verification/:numeroSerie est donc couvert côté backend par
 * conges/test_api.py (test_parcours_complet), pas ici ; ce test-ci vérifie seulement son état
 * d'échec (code absent/invalide), qui ne nécessite pas de décoder le PDF.
 */

const MOT_DE_PASSE = 'Demo1234!'

async function connecter(page: Page, matricule: string) {
  await page.goto('/connexion')
  await page.getByLabel('Matricule').fill(matricule)
  await page.getByLabel('Mot de passe').fill(MOT_DE_PASSE)
  await page.getByRole('button', { name: 'Se connecter' }).click()
  await expect(page).toHaveURL(/mes-demandes/)
}

async function deconnecter(page: Page) {
  await page.getByRole('button', { name: 'Déconnexion' }).click()
  await expect(page).toHaveURL(/connexion/)
}

test('parcours critique complet : demande -> 3 niveaux d\'approbation -> attestation', async ({ page }) => {
  // 1. L'agent se connecte et soumet une demande de congé exceptionnel (aucun justificatif requis)
  await connecter(page, 'AG001')
  await page.getByRole('link', { name: 'Nouvelle demande' }).click()

  await page.getByLabel('Type de congé').selectOption({ label: 'Congé exceptionnel' })

  const debut = new Date()
  debut.setDate(debut.getDate() + 14)
  const fin = new Date(debut)
  fin.setDate(fin.getDate() + 2)
  const fmt = (d: Date) => d.toISOString().slice(0, 10)

  await page.getByLabel('Date de début').fill(fmt(debut))
  await page.getByLabel('Date de fin souhaitée').fill(fmt(fin))
  await page.getByRole('button', { name: 'Continuer' }).click()

  await expect(page.getByText("Aucun justificatif n'est requis")).toBeVisible()
  await page.getByRole('button', { name: 'Soumettre la demande' }).click()

  await expect(page).toHaveURL(/mes-demandes/)
  await expect(page.getByText('En cours de validation').first()).toBeVisible()

  await page.getByRole('link', { name: 'Voir' }).first().click()
  const demandeUrl = page.url()
  await expect(page.getByText('Chef de service')).toBeVisible()

  await deconnecter(page)

  // 2. Le chef de service approuve
  await connecter(page, 'CS001')
  await page.getByRole('link', { name: 'À valider' }).click()
  await expect(page.getByText('Ibrahima Sylla')).toBeVisible()
  await page.getByRole('link', { name: 'Examiner' }).first().click()
  await page.getByLabel('Commentaire').fill('Accord du chef de service.')
  await page.getByRole('button', { name: 'Approuver' }).click()
  await expect(page.getByText('En cours de validation').first()).toBeVisible()
  await deconnecter(page)

  // 3. Le directeur approuve
  await connecter(page, 'DIR001')
  await page.getByRole('link', { name: 'À valider' }).click()
  await page.getByRole('link', { name: 'Examiner' }).first().click()
  await page.getByLabel('Commentaire').fill('Accord du directeur.')
  await page.getByRole('button', { name: 'Approuver' }).click()
  await deconnecter(page)

  // 4. Le chef de cabinet approuve -> l'attestation doit apparaître
  await connecter(page, 'CC001')
  await page.getByRole('link', { name: 'À valider' }).click()
  await page.getByRole('link', { name: 'Examiner' }).first().click()
  await page.getByLabel('Commentaire').fill('Validé.')
  await page.getByRole('button', { name: 'Approuver' }).click()

  await expect(page.getByText('Approuvée').first()).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Attestation' })).toBeVisible()
  await expect(page.getByText(/Numéro de série/)).toBeVisible()
  await expect(page.getByRole('link', { name: "Télécharger l'attestation (PDF)" })).toHaveAttribute(
    'href',
    /\.pdf$/,
  )

  // 5. L'agent voit sa demande approuvée avec l'attestation disponible
  await deconnecter(page)
  await connecter(page, 'AG001')
  await page.goto(demandeUrl)
  await expect(page.getByRole('heading', { name: 'Attestation' })).toBeVisible()
})

test('la vérification publique rejette un code invalide', async ({ page }) => {
  await page.goto('/verification/00000000-0000-0000-0000-000000000000?code=invalide')
  await expect(page.getByText("n'a pas pu être authentifié")).toBeVisible()
})

test('un congé de maladie exige ses justificatifs avant de pouvoir être soumis', async ({ page }) => {
  await connecter(page, 'AG001')
  await page.getByRole('link', { name: 'Nouvelle demande' }).click()
  await page.getByLabel('Type de congé').selectOption({ label: 'Congé de maladie' })

  const debut = new Date()
  debut.setDate(debut.getDate() + 30)
  const fin = new Date(debut)
  fin.setDate(fin.getDate() + 3)
  const fmt = (d: Date) => d.toISOString().slice(0, 10)
  await page.getByLabel('Date de début').fill(fmt(debut))
  await page.getByLabel('Date de fin souhaitée').fill(fmt(fin))
  await page.getByRole('button', { name: 'Continuer' }).click()

  const boutonSoumettre = page.getByRole('button', { name: 'Soumettre la demande' })
  await expect(boutonSoumettre).toBeDisabled()

  await page.getByLabel('Bulletin de paie').setInputFiles({
    name: 'bulletin.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('%PDF-1.4 contenu de test'),
  })
  await expect(boutonSoumettre).toBeDisabled()

  await page.getByLabel('Rapport médical').setInputFiles({
    name: 'rapport.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('%PDF-1.4 contenu de test'),
  })
  await expect(boutonSoumettre).toBeEnabled()

  await boutonSoumettre.click()
  await expect(page).toHaveURL(/mes-demandes/)
})
