import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { annulerDemande, approuverEtape, obtenirDemande, rejeterEtape } from '../api/conges'
import { EtapesTimeline } from '../components/EtapesTimeline'
import { StatutBadge } from '../components/StatutBadge'
import { useAuth } from '../context/AuthContext'
import type { DemandeCongeDetail } from '../types'

const API_ORIGIN = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace(/\/api\/?$/, '')

function extraireErreur(err: any): string {
  const data = err?.response?.data
  if (!data) return 'Une erreur est survenue.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  return Object.values(data).flat().join(' ')
}

export function DemandeDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { utilisateur } = useAuth()
  const [demande, setDemande] = useState<DemandeCongeDetail | null>(null)
  const [commentaire, setCommentaire] = useState('')
  const [dureeAccordee, setDureeAccordee] = useState('')
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)

  useEffect(() => {
    if (id) obtenirDemande(Number(id)).then(setDemande)
  }, [id])

  if (!demande) return <p>Chargement…</p>

  const etapeCourante = demande.etapes.find((e) => e.decision === 'EN_ATTENTE')
  const jePeuxDecider =
    demande.statut === 'EN_COURS' && etapeCourante && utilisateur && etapeCourante.validateur.id === utilisateur.id
  const jePeuxAnnuler =
    utilisateur &&
    demande.agent.id === utilisateur.id &&
    (demande.statut === 'BROUILLON' || demande.statut === 'EN_COURS')

  async function annuler() {
    if (!id) return
    if (!window.confirm('Confirmer l\'annulation de cette demande de congé ?')) return
    setErreur(null)
    setEnvoi(true)
    try {
      setDemande(await annulerDemande(Number(id)))
    } catch (err) {
      setErreur(extraireErreur(err))
    } finally {
      setEnvoi(false)
    }
  }

  async function decider(approuver: boolean) {
    if (!etapeCourante || !id) return
    setErreur(null)
    if (!approuver && !commentaire.trim()) {
      setErreur('Un commentaire est requis pour justifier un rejet.')
      return
    }
    setEnvoi(true)
    try {
      const maj = approuver
        ? await approuverEtape(
            Number(id),
            etapeCourante.id,
            commentaire,
            dureeAccordee ? Number(dureeAccordee) : undefined,
          )
        : await rejeterEtape(Number(id), etapeCourante.id, commentaire)
      setDemande(maj)
      setCommentaire('')
      setDureeAccordee('')
    } catch (err) {
      setErreur(extraireErreur(err))
    } finally {
      setEnvoi(false)
    }
  }

  return (
    <>
      <button type="button" className="bouton bouton-discret" onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>
        ← Retour
      </button>

      <div className="entete-page">
        <h1>{demande.type_conge.libelle}</h1>
        <p>
          {demande.agent.first_name} {demande.agent.last_name} ({demande.agent.matricule}) — <StatutBadge statut={demande.statut} />
        </p>
      </div>

      {erreur && !jePeuxDecider && <div className="erreur">{erreur}</div>}

      <div className="carte">
        <h2>Détails</h2>
        {jePeuxAnnuler && (
          <button
            type="button"
            className="bouton bouton-discret"
            onClick={annuler}
            disabled={envoi}
            style={{ float: 'right' }}
          >
            Annuler ma demande
          </button>
        )}
        <p>
          Période demandée : {new Date(demande.date_debut).toLocaleDateString('fr-FR')} →{' '}
          {new Date(demande.date_fin_demandee).toLocaleDateString('fr-FR')}
        </p>
        {demande.date_fin_validee && demande.date_fin_validee !== demande.date_fin_demandee && (
          <p>Période validée : jusqu'au {new Date(demande.date_fin_validee).toLocaleDateString('fr-FR')}</p>
        )}
        {demande.motif && <p>Motif : {demande.motif}</p>}
        {demande.justificatifs.length > 0 && (
          <>
            <h3 style={{ marginTop: 16 }}>Justificatifs</h3>
            <ul>
              {demande.justificatifs.map((j) => (
                <li key={j.id}>
                  {j.type_justificatif_libelle} —{' '}
                  <a href={`${API_ORIGIN}${j.fichier}`} target="_blank" rel="noreferrer">
                    voir le fichier
                  </a>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="carte">
        <h2>Circuit de validation</h2>
        <EtapesTimeline etapes={demande.etapes} />
      </div>

      {demande.attestation && (
        <div className="carte">
          <h2>Attestation</h2>
          <p>Numéro de série : {demande.attestation.numero_serie}</p>
          <a
            className="bouton bouton-primaire"
            href={`${API_ORIGIN}${demande.attestation.fichier_pdf}`}
            target="_blank"
            rel="noreferrer"
          >
            Télécharger l'attestation (PDF)
          </a>
        </div>
      )}

      {jePeuxDecider && (
        <div className="carte">
          <h2>Votre décision</h2>
          {erreur && <div className="erreur">{erreur}</div>}
          {etapeCourante?.role_attendu === 'DIRECTEUR' && (
            <div className="groupe-champ">
              <label htmlFor="duree">Durée accordée en jours (facultatif, si différente de la demande)</label>
              <input
                id="duree"
                type="number"
                min={1}
                value={dureeAccordee}
                onChange={(e) => setDureeAccordee(e.target.value)}
              />
            </div>
          )}
          <div className="groupe-champ">
            <label htmlFor="commentaire">Commentaire</label>
            <textarea id="commentaire" rows={2} value={commentaire} onChange={(e) => setCommentaire(e.target.value)} />
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button type="button" className="bouton bouton-primaire" disabled={envoi} onClick={() => decider(true)}>
              Approuver
            </button>
            <button type="button" className="bouton bouton-danger" disabled={envoi} onClick={() => decider(false)}>
              Rejeter
            </button>
          </div>
        </div>
      )}
    </>
  )
}
