import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Layout() {
  const { utilisateur, deconnecter } = useAuth()
  const navigate = useNavigate()

  async function handleDeconnexion() {
    await deconnecter()
    navigate('/connexion')
  }

  return (
    <div className="app-shell">
      <div className="drapeau-barre" />
      <header className="app-header">
        <div className="titre">
          <span className="pays">République de Guinée</span>
          <span className="ministere">Gestion des congés — MEFB</span>
        </div>
        <nav className="app-nav">
          <NavLink to="/nouvelle-demande" className={({ isActive }) => (isActive ? 'actif' : '')}>
            Nouvelle demande
          </NavLink>
          <NavLink to="/mes-demandes" className={({ isActive }) => (isActive ? 'actif' : '')}>
            Mes demandes
          </NavLink>
          {utilisateur && utilisateur.role_hierarchique !== 'AGENT' && (
            <NavLink to="/a-valider" className={({ isActive }) => (isActive ? 'actif' : '')}>
              À valider
            </NavLink>
          )}
          {utilisateur?.is_staff && (
            <>
              <NavLink to="/administration/agents" className={({ isActive }) => (isActive ? 'actif' : '')}>
                Agents
              </NavLink>
              <NavLink to="/administration/organisation" className={({ isActive }) => (isActive ? 'actif' : '')}>
                Organisation
              </NavLink>
            </>
          )}
        </nav>
        <div className="compte">
          {utilisateur && (
            <span>
              {utilisateur.first_name} {utilisateur.last_name} ({utilisateur.matricule})
            </span>
          )}
          <button type="button" onClick={handleDeconnexion}>
            Déconnexion
          </button>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
