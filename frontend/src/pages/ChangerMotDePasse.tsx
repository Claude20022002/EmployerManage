import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { changerMotDePasse } from '../api/auth'
import { useAuth } from '../context/AuthContext'

export function ChangerMotDePasse() {
  const { utilisateur, rafraichirUtilisateur } = useAuth()
  const navigate = useNavigate()
  const [ancien, setAncien] = useState('')
  const [nouveau, setNouveau] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErreur(null)
    if (nouveau !== confirmation) {
      setErreur('La confirmation ne correspond pas au nouveau mot de passe.')
      return
    }
    setEnvoi(true)
    try {
      await changerMotDePasse(ancien, nouveau)
      await rafraichirUtilisateur()
      navigate('/')
    } catch (err: any) {
      setErreur(err?.response?.data?.ancien_mot_de_passe?.[0] ?? 'Impossible de changer le mot de passe.')
    } finally {
      setEnvoi(false)
    }
  }

  return (
    <div className="centre-page">
      <div className="panneau-connexion">
        <div className="entete">
          <h1 style={{ fontSize: 20 }}>Changement de mot de passe</h1>
          <p style={{ fontSize: 13 }}>
            {utilisateur?.must_change_password
              ? 'Votre mot de passe temporaire doit être personnalisé avant de continuer.'
              : 'Choisissez un nouveau mot de passe.'}
          </p>
        </div>
        {erreur && <div className="erreur">{erreur}</div>}
        <form onSubmit={handleSubmit}>
          <div className="groupe-champ">
            <label htmlFor="ancien">Mot de passe actuel</label>
            <input
              id="ancien"
              type="password"
              value={ancien}
              onChange={(e) => setAncien(e.target.value)}
              required
            />
          </div>
          <div className="groupe-champ">
            <label htmlFor="nouveau">Nouveau mot de passe</label>
            <input
              id="nouveau"
              type="password"
              value={nouveau}
              onChange={(e) => setNouveau(e.target.value)}
              minLength={8}
              required
            />
          </div>
          <div className="groupe-champ">
            <label htmlFor="confirmation">Confirmer le nouveau mot de passe</label>
            <input
              id="confirmation"
              type="password"
              value={confirmation}
              onChange={(e) => setConfirmation(e.target.value)}
              minLength={8}
              required
            />
          </div>
          <button type="submit" className="bouton bouton-primaire" style={{ width: '100%' }} disabled={envoi}>
            {envoi ? 'Enregistrement…' : 'Valider'}
          </button>
        </form>
      </div>
    </div>
  )
}
