import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function ProtectedRoute() {
  const { utilisateur, chargement } = useAuth()

  if (chargement) return null
  if (!utilisateur) return <Navigate to="/connexion" replace />
  if (utilisateur.must_change_password) return <Navigate to="/changer-mot-de-passe" replace />

  return <Outlet />
}
