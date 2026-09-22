import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import { AdministrationAgents } from './pages/AdministrationAgents'
import { AValider } from './pages/AValider'
import { ChangerMotDePasse } from './pages/ChangerMotDePasse'
import { Connexion } from './pages/Connexion'
import { DemandeDetail } from './pages/DemandeDetail'
import { MesDemandes } from './pages/MesDemandes'
import { NouvelleDemande } from './pages/NouvelleDemande'
import { VerificationPublique } from './pages/VerificationPublique'

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/connexion" element={<Connexion />} />
        <Route path="/verification/:numeroSerie" element={<VerificationPublique />} />
        <Route path="/changer-mot-de-passe" element={<ChangerMotDePasse />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Navigate to="/mes-demandes" replace />} />
            <Route path="/nouvelle-demande" element={<NouvelleDemande />} />
            <Route path="/mes-demandes" element={<MesDemandes />} />
            <Route path="/a-valider" element={<AValider />} />
            <Route path="/demandes/:id" element={<DemandeDetail />} />
            <Route path="/administration/agents" element={<AdministrationAgents />} />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default App
