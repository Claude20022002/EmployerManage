import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ajouterJustificatif, creerDemande, listerTypesConge, soumettreDemande } from '../api/conges'
import type { DemandeCongeDetail, TypeConge } from '../types'

function extraireErreur(err: any): string {
  const data = err?.response?.data
  if (!data) return "Une erreur est survenue."
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  return Object.values(data).flat().join(' ')
}

export function NouvelleDemande() {
  const navigate = useNavigate()
  const [types, setTypes] = useState<TypeConge[]>([])
  const [typeId, setTypeId] = useState<number | ''>('')
  const [dateDebut, setDateDebut] = useState('')
  const [dateFin, setDateFin] = useState('')
  const [motif, setMotif] = useState('')
  const [demande, setDemande] = useState<DemandeCongeDetail | null>(null)
  const [fichiers, setFichiers] = useState<Record<number, File | null>>({})
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)

  useEffect(() => {
    listerTypesConge().then(setTypes)
  }, [])

  const typeSelectionne = types.find((t) => t.id === typeId) ?? null

  async function handleCreer(e: FormEvent) {
    e.preventDefault()
    setErreur(null)
    if (!typeId) return
    setEnvoi(true)
    try {
      const d = await creerDemande({
        type_conge: typeId,
        date_debut: dateDebut,
        date_fin_demandee: dateFin,
        motif,
      })
      setDemande(d)
    } catch (err) {
      setErreur(extraireErreur(err))
    } finally {
      setEnvoi(false)
    }
  }

  async function handleSoumettre() {
    if (!demande || !typeSelectionne) return
    setErreur(null)
    setEnvoi(true)
    try {
      for (const req of typeSelectionne.justificatifs_requis) {
        const fichier = fichiers[req.id]
        if (fichier) {
          await ajouterJustificatif(demande.id, req.id, fichier)
        }
      }
      await soumettreDemande(demande.id)
      navigate('/mes-demandes')
    } catch (err) {
      setErreur(extraireErreur(err))
    } finally {
      setEnvoi(false)
    }
  }

  const justificatifsPrets =
    typeSelectionne?.justificatifs_requis.every((j) => fichiers[j.id]) ?? true

  return (
    <>
      <div className="entete-page">
        <h1>Nouvelle demande de congé</h1>
        <p>Remplissez le formulaire puis joignez les pièces justificatives requises pour votre type de congé.</p>
      </div>

      {erreur && <div className="erreur">{erreur}</div>}

      {!demande && (
        <form className="carte" onSubmit={handleCreer}>
          <div className="groupe-champ">
            <label htmlFor="type-conge">Type de congé</label>
            <select id="type-conge" value={typeId} onChange={(e) => setTypeId(Number(e.target.value))} required>
              <option value="">Sélectionner…</option>
              {types.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.libelle}
                </option>
              ))}
            </select>
            {typeSelectionne && (
              <p className="aide">
                Durée {typeSelectionne.jours_ouvrables_uniquement ? 'ouvrable' : 'calendaire'} :{' '}
                {typeSelectionne.duree_min_jours}
                {typeSelectionne.duree_max_jours ? `–${typeSelectionne.duree_max_jours}` : '+'} jours.
                {typeSelectionne.justificatifs_requis.length > 0 &&
                  ` Justificatifs requis : ${typeSelectionne.justificatifs_requis.map((j) => j.libelle).join(', ')}.`}
              </p>
            )}
          </div>

          <div className="ligne-champs">
            <div className="groupe-champ">
              <label htmlFor="date-debut">Date de début</label>
              <input
                id="date-debut"
                type="date"
                value={dateDebut}
                onChange={(e) => setDateDebut(e.target.value)}
                required
              />
            </div>
            <div className="groupe-champ">
              <label htmlFor="date-fin">Date de fin souhaitée</label>
              <input
                id="date-fin"
                type="date"
                value={dateFin}
                onChange={(e) => setDateFin(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="groupe-champ">
            <label htmlFor="motif">Motif (facultatif)</label>
            <textarea id="motif" rows={3} value={motif} onChange={(e) => setMotif(e.target.value)} />
          </div>

          <button type="submit" className="bouton bouton-primaire" disabled={envoi || !typeId}>
            {envoi ? 'Création…' : 'Continuer'}
          </button>
        </form>
      )}

      {demande && typeSelectionne && (
        <div className="carte">
          <h2>Pièces justificatives</h2>
          {typeSelectionne.justificatifs_requis.length === 0 && (
            <p className="aide">Aucun justificatif n'est requis pour ce type de congé.</p>
          )}
          {typeSelectionne.justificatifs_requis.map((req) => (
            <div className="groupe-champ" key={req.id}>
              <label htmlFor={`justificatif-${req.id}`}>{req.libelle}</label>
              <input
                id={`justificatif-${req.id}`}
                type="file"
                onChange={(e) => setFichiers((f) => ({ ...f, [req.id]: e.target.files?.[0] ?? null }))}
              />
            </div>
          ))}
          <button
            type="button"
            className="bouton bouton-primaire"
            onClick={handleSoumettre}
            disabled={envoi || !justificatifsPrets}
          >
            {envoi ? 'Envoi…' : 'Soumettre la demande'}
          </button>
        </div>
      )}
    </>
  )
}
