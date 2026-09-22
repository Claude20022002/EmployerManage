import { useEffect, useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { creerAgent, listerAgents, listerServices, type AgentCree } from '../api/administration'
import { useAuth } from '../context/AuthContext'
import type { RoleHierarchique, Service, Utilisateur } from '../types'

const ROLES: { valeur: RoleHierarchique; libelle: string }[] = [
  { valeur: 'AGENT', libelle: 'Agent' },
  { valeur: 'CHEF_SERVICE', libelle: 'Chef de service' },
  { valeur: 'DIRECTEUR', libelle: 'Directeur' },
  { valeur: 'CHEF_CABINET', libelle: 'Chef de cabinet' },
]

function extraireErreur(err: any): string {
  const data = err?.response?.data
  if (!data) return 'Une erreur est survenue.'
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  return Object.entries(data)
    .map(([champ, msgs]) => `${champ} : ${(Array.isArray(msgs) ? msgs : [msgs]).join(' ')}`)
    .join(' — ')
}

export function AdministrationAgents() {
  const { utilisateur } = useAuth()
  const [agents, setAgents] = useState<Utilisateur[]>([])
  const [services, setServices] = useState<Service[]>([])
  const [matricule, setMatricule] = useState('')
  const [prenom, setPrenom] = useState('')
  const [nom, setNom] = useState('')
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<RoleHierarchique>('AGENT')
  const [serviceId, setServiceId] = useState<number | ''>('')
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)
  const [dernierAgentCree, setDernierAgentCree] = useState<AgentCree | null>(null)

  function chargerAgents() {
    listerAgents().then(setAgents)
  }

  useEffect(() => {
    if (!utilisateur?.is_staff) return
    chargerAgents()
    listerServices().then(setServices)
  }, [utilisateur])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErreur(null)
    setDernierAgentCree(null)
    setEnvoi(true)
    try {
      const cree = await creerAgent({
        matricule,
        first_name: prenom,
        last_name: nom,
        email,
        role_hierarchique: role,
        service: serviceId || null,
      })
      setDernierAgentCree(cree)
      setMatricule('')
      setPrenom('')
      setNom('')
      setEmail('')
      setRole('AGENT')
      setServiceId('')
      chargerAgents()
    } catch (err) {
      setErreur(extraireErreur(err))
    } finally {
      setEnvoi(false)
    }
  }

  if (!utilisateur?.is_staff) return <Navigate to="/mes-demandes" replace />

  return (
    <>
      <div className="entete-page">
        <h1>Administration — Comptes agents</h1>
        <p>Créer un compte agent avec un mot de passe temporaire, à communiquer directement à l'intéressé.</p>
      </div>

      {dernierAgentCree && (
        <div className="carte" style={{ borderColor: 'var(--color-success)', background: 'var(--color-success-soft)' }}>
          <h2>Compte créé — {dernierAgentCree.first_name} {dernierAgentCree.last_name} ({dernierAgentCree.matricule})</h2>
          <p>
            Mot de passe temporaire :{' '}
            <strong style={{ fontFamily: 'monospace', fontSize: 16 }}>{dernierAgentCree.mot_de_passe_temporaire}</strong>
          </p>
          <p className="aide">
            Ce mot de passe ne sera plus jamais affiché. Communiquez-le à l'agent par un canal officiel ; il devra
            le changer dès sa première connexion.
          </p>
        </div>
      )}

      <form className="carte" onSubmit={handleSubmit}>
        <h2>Nouveau compte</h2>
        {erreur && <div className="erreur">{erreur}</div>}
        <div className="ligne-champs">
          <div className="groupe-champ">
            <label htmlFor="matricule">Matricule</label>
            <input id="matricule" value={matricule} onChange={(e) => setMatricule(e.target.value)} required />
          </div>
          <div className="groupe-champ">
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
        </div>
        <div className="ligne-champs">
          <div className="groupe-champ">
            <label htmlFor="prenom">Prénom</label>
            <input id="prenom" value={prenom} onChange={(e) => setPrenom(e.target.value)} required />
          </div>
          <div className="groupe-champ">
            <label htmlFor="nom">Nom</label>
            <input id="nom" value={nom} onChange={(e) => setNom(e.target.value)} required />
          </div>
        </div>
        <div className="ligne-champs">
          <div className="groupe-champ">
            <label htmlFor="role">Rôle hiérarchique</label>
            <select id="role" value={role} onChange={(e) => setRole(e.target.value as RoleHierarchique)}>
              {ROLES.map((r) => (
                <option key={r.valeur} value={r.valeur}>
                  {r.libelle}
                </option>
              ))}
            </select>
          </div>
          <div className="groupe-champ">
            <label htmlFor="service">Service de rattachement</label>
            <select id="service" value={serviceId} onChange={(e) => setServiceId(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Aucun (directeur, chef de cabinet…)</option>
              {services.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nom} — {s.direction_nom}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button type="submit" className="bouton bouton-primaire" disabled={envoi}>
          {envoi ? 'Création…' : 'Créer le compte'}
        </button>
      </form>

      <div className="carte" style={{ padding: 0 }}>
        <h2 style={{ padding: '20px 24px 0' }}>Agents ({agents.length})</h2>
        <table>
          <thead>
            <tr>
              <th>Matricule</th>
              <th>Nom</th>
              <th>Rôle</th>
              <th>Service</th>
              <th>Email</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((a) => (
              <tr key={a.id}>
                <td>{a.matricule}</td>
                <td>
                  {a.first_name} {a.last_name}
                </td>
                <td>{ROLES.find((r) => r.valeur === a.role_hierarchique)?.libelle}</td>
                <td>{services.find((s) => s.id === a.service)?.nom ?? '—'}</td>
                <td>{a.email}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
