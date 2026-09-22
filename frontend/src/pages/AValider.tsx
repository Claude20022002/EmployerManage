import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { demandesAValider } from '../api/conges'
import type { DemandeCongeListe } from '../types'

export function AValider() {
  const [demandes, setDemandes] = useState<DemandeCongeListe[] | null>(null)

  useEffect(() => {
    demandesAValider().then(setDemandes)
  }, [])

  return (
    <>
      <div className="entete-page">
        <h1>Demandes à valider</h1>
        <p>Demandes en attente de votre décision.</p>
      </div>

      <div className="carte" style={{ padding: 0 }}>
        {demandes === null && <p style={{ padding: 20 }}>Chargement…</p>}
        {demandes?.length === 0 && <p className="liste-vide">Aucune demande en attente de votre décision.</p>}
        {demandes && demandes.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Agent</th>
                <th>Type</th>
                <th>Période</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {demandes.map((d) => (
                <tr key={d.id}>
                  <td>
                    {d.agent.first_name} {d.agent.last_name} ({d.agent.matricule})
                  </td>
                  <td>{d.type_conge.libelle}</td>
                  <td>
                    {new Date(d.date_debut).toLocaleDateString('fr-FR')} →{' '}
                    {new Date(d.date_fin_demandee).toLocaleDateString('fr-FR')}
                  </td>
                  <td>
                    <Link to={`/demandes/${d.id}`}>Examiner</Link>
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
