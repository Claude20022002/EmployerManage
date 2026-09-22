import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Connexion() {
  const { connecter } = useAuth()
  const navigate = useNavigate()
  const [matricule, setMatricule] = useState('')
  const [motDePasse, setMotDePasse] = useState('')
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErreur(null)
    setEnvoi(true)
    try {
      await connecter(matricule, motDePasse)
      navigate('/')
    } catch {
      setErreur('Matricule ou mot de passe incorrect.')
    } finally {
      setEnvoi(false)
    }
  }

  return (
    <div className="centre-page">
      <div className="panneau-connexion">
        <div className="entete">
          <div className="pays">République de Guinée</div>
          <h1 style={{ fontSize: 20 }}>Gestion des congés</h1>
          <p style={{ fontSize: 13 }}>Ministère de l'Économie, des Finances et du Budget</p>
        </div>
        {erreur && <div className="erreur">{erreur}</div>}
        <form onSubmit={handleSubmit}>
          <div className="groupe-champ">
            <label htmlFor="matricule">Matricule</label>
            <input
              id="matricule"
              value={matricule}
              onChange={(e) => setMatricule(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div className="groupe-champ">
            <label htmlFor="mot-de-passe">Mot de passe</label>
            <input
              id="mot-de-passe"
              type="password"
              value={motDePasse}
              onChange={(e) => setMotDePasse(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <button type="submit" className="bouton bouton-primaire" style={{ width: '100%' }} disabled={envoi}>
            {envoi ? 'Connexion…' : 'Se connecter'}
          </button>
        </form>
      </div>
    </div>
  )
}
