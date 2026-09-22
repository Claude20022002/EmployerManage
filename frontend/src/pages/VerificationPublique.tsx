import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { verifierAttestation, type ResultatVerification } from '../api/conges'

export function VerificationPublique() {
  const { numeroSerie } = useParams()
  const [searchParams] = useSearchParams()
  const [resultat, setResultat] = useState<ResultatVerification | null>(null)

  useEffect(() => {
    if (!numeroSerie) return
    verifierAttestation(numeroSerie, searchParams.get('code') ?? '').then(setResultat)
  }, [numeroSerie, searchParams])

  return (
    <div className="centre-page">
      <div className="panneau-connexion" style={{ maxWidth: 440 }}>
        <div className="entete">
          <div className="pays">République de Guinée</div>
          <h1 style={{ fontSize: 20 }}>Vérification d'attestation</h1>
          <p style={{ fontSize: 13 }}>Ministère de l'Économie, des Finances et du Budget</p>
        </div>

        {resultat === null && <p style={{ textAlign: 'center' }}>Vérification en cours…</p>}

        {resultat?.valide === false && (
          <div className="erreur" style={{ textAlign: 'center' }}>
            Ce document n'a pas pu être authentifié. Il est peut-être invalide, altéré ou ce lien est incorrect.
          </div>
        )}

        {resultat?.valide === true && (
          <div>
            <div className="badge badge-approuvee" style={{ marginBottom: 16 }}>
              ✓ Document authentique
            </div>
            <table>
              <tbody>
                <tr>
                  <td>Agent</td>
                  <td>{resultat.agent}</td>
                </tr>
                <tr>
                  <td>Matricule</td>
                  <td>{resultat.matricule}</td>
                </tr>
                <tr>
                  <td>Type de congé</td>
                  <td>{resultat.type_conge}</td>
                </tr>
                <tr>
                  <td>Période</td>
                  <td>
                    {resultat.date_debut && new Date(resultat.date_debut).toLocaleDateString('fr-FR')} →{' '}
                    {resultat.date_fin && new Date(resultat.date_fin).toLocaleDateString('fr-FR')}
                  </td>
                </tr>
                <tr>
                  <td>N° de série</td>
                  <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{resultat.numero_serie}</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
