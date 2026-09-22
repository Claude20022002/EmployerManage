import { useEffect, useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { listerAgents } from '../api/administration'
import {
  assignerChefService,
  assignerDirecteur,
  creerDirection,
  creerService,
  listerDirections,
  listerServices,
} from '../api/organisation'
import { useAuth } from '../context/AuthContext'
import type { Direction, Service, Utilisateur } from '../types'

function extraireErreur(err: any): string {
  const data = err?.response?.data
  if (!data) return 'Une erreur est survenue.'
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  return Object.entries(data)
    .map(([champ, msgs]) => `${champ} : ${(Array.isArray(msgs) ? msgs : [msgs]).join(' ')}`)
    .join(' — ')
}

export function AdministrationOrganisation() {
  const { utilisateur } = useAuth()
  const [directions, setDirections] = useState<Direction[]>([])
  const [services, setServices] = useState<Service[]>([])
  const [agents, setAgents] = useState<Utilisateur[]>([])
  const [erreur, setErreur] = useState<string | null>(null)

  const [nomDirection, setNomDirection] = useState('')
  const [nomService, setNomService] = useState('')
  const [directionDuService, setDirectionDuService] = useState<number | ''>('')

  function recharger() {
    listerDirections().then(setDirections)
    listerServices().then(setServices)
  }

  useEffect(() => {
    if (!utilisateur?.is_staff) return
    recharger()
    listerAgents().then(setAgents)
  }, [utilisateur])

  if (!utilisateur?.is_staff) return <Navigate to="/mes-demandes" replace />

  async function handleCreerDirection(e: FormEvent) {
    e.preventDefault()
    setErreur(null)
    try {
      await creerDirection(nomDirection)
      setNomDirection('')
      recharger()
    } catch (err) {
      setErreur(extraireErreur(err))
    }
  }

  async function handleCreerService(e: FormEvent) {
    e.preventDefault()
    setErreur(null)
    if (!directionDuService) return
    try {
      await creerService(nomService, directionDuService)
      setNomService('')
      setDirectionDuService('')
      recharger()
    } catch (err) {
      setErreur(extraireErreur(err))
    }
  }

  async function handleAssignerDirecteur(directionId: number, userId: string) {
    if (!userId) return
    try {
      await assignerDirecteur(directionId, Number(userId))
      recharger()
    } catch (err) {
      setErreur(extraireErreur(err))
    }
  }

  async function handleAssignerChefService(serviceId: number, userId: string) {
    if (!userId) return
    try {
      await assignerChefService(serviceId, Number(userId))
      recharger()
    } catch (err) {
      setErreur(extraireErreur(err))
    }
  }

  return (
    <>
      <div className="entete-page">
        <h1>Administration — Directions et services</h1>
        <p>
          Structure organisationnelle utilisée pour router les demandes de congé (chef de service → directeur →
          chef de cabinet).
        </p>
      </div>

      {erreur && <div className="erreur">{erreur}</div>}

      <div className="carte">
        <h2>Directions</h2>
        <form onSubmit={handleCreerDirection} style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
          <input
            placeholder="Nom de la direction"
            value={nomDirection}
            onChange={(e) => setNomDirection(e.target.value)}
            required
          />
          <button type="submit" className="bouton bouton-primaire">
            Ajouter
          </button>
        </form>
        <table>
          <thead>
            <tr>
              <th>Nom</th>
              <th>Directeur</th>
            </tr>
          </thead>
          <tbody>
            {directions.map((d) => (
              <tr key={d.id}>
                <td>{d.nom}</td>
                <td>
                  <select
                    value={d.directeur ?? ''}
                    onChange={(e) => handleAssignerDirecteur(d.id, e.target.value)}
                  >
                    <option value="">{d.directeur_nom ?? 'Non assigné'}</option>
                    {agents
                      .filter((a) => a.role_hierarchique === 'DIRECTEUR')
                      .map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.first_name} {a.last_name} ({a.matricule})
                        </option>
                      ))}
                  </select>
                </td>
              </tr>
            ))}
            {directions.length === 0 && (
              <tr>
                <td colSpan={2} className="liste-vide">
                  Aucune direction.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="carte">
        <h2>Services</h2>
        <form onSubmit={handleCreerService} style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
          <input
            placeholder="Nom du service"
            value={nomService}
            onChange={(e) => setNomService(e.target.value)}
            required
          />
          <select
            value={directionDuService}
            onChange={(e) => setDirectionDuService(e.target.value ? Number(e.target.value) : '')}
            required
          >
            <option value="">Direction de rattachement…</option>
            {directions.map((d) => (
              <option key={d.id} value={d.id}>
                {d.nom}
              </option>
            ))}
          </select>
          <button type="submit" className="bouton bouton-primaire">
            Ajouter
          </button>
        </form>
        <table>
          <thead>
            <tr>
              <th>Nom</th>
              <th>Direction</th>
              <th>Chef de service</th>
            </tr>
          </thead>
          <tbody>
            {services.map((s) => (
              <tr key={s.id}>
                <td>{s.nom}</td>
                <td>{s.direction_nom}</td>
                <td>
                  <select value={s.chef_service ?? ''} onChange={(e) => handleAssignerChefService(s.id, e.target.value)}>
                    <option value="">{s.chef_service_nom ?? 'Non assigné'}</option>
                    {agents
                      .filter((a) => a.role_hierarchique === 'CHEF_SERVICE')
                      .map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.first_name} {a.last_name} ({a.matricule})
                        </option>
                      ))}
                  </select>
                </td>
              </tr>
            ))}
            {services.length === 0 && (
              <tr>
                <td colSpan={3} className="liste-vide">
                  Aucun service.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  )
}
