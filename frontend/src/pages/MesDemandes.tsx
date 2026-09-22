import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { mesDemandes } from '../api/conges'
import { StatutBadge } from '../components/StatutBadge'
import type { DemandeCongeListe } from '../types'

export function MesDemandes() {
  const [demandes, setDemandes] = useState<DemandeCongeListe[] | null>(null)

  useEffect(() => {
    mesDemandes().then(setDemandes)
  }, [])

  return (
    <>
      <div className="entete-page">
        <h1>Mes demandes de congé</h1>
        <p>Historique et suivi de vos demandes.</p>
      </div>

      <div className="carte" style={{ padding: 0 }}>
        {demandes === null && <p style={{ padding: 20 }}>Chargement…</p>}
        {demandes?.length === 0 && <p className="liste-vide">Aucune demande pour le moment.</p>}
        {demandes && demandes.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Période</th>
                <th>Statut</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {demandes.map((d) => (
                <tr key={d.id}>
                  <td>{d.type_conge.libelle}</td>
                  <td>
                    {new Date(d.date_debut).toLocaleDateString('fr-FR')} →{' '}
                    {new Date(d.date_fin_validee ?? d.date_fin_demandee).toLocaleDateString('fr-FR')}
                  </td>
                  <td>
                    <StatutBadge statut={d.statut} />
                  </td>
                  <td>
                    <Link to={`/demandes/${d.id}`}>Voir</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
