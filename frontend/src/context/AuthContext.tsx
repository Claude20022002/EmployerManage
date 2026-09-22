import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { assurerCookieCsrf } from '../api/client'
import * as authApi from '../api/auth'
import type { Utilisateur } from '../types'

interface AuthContextValue {
  utilisateur: Utilisateur | null
  chargement: boolean
  connecter: (matricule: string, motDePasse: string) => Promise<void>
  deconnecter: () => Promise<void>
  rafraichirUtilisateur: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [utilisateur, setUtilisateur] = useState<Utilisateur | null>(null)
  const [chargement, setChargement] = useState(true)

  useEffect(() => {
    ;(async () => {
      await assurerCookieCsrf()
      try {
        const u = await authApi.recupererUtilisateurCourant()
        setUtilisateur(u)
      } catch {
        setUtilisateur(null)
      } finally {
        setChargement(false)
      }
    })()
  }, [])

  async function connecter(matricule: string, motDePasse: string) {
    const u = await authApi.connexion(matricule, motDePasse)
    setUtilisateur(u)
  }

  async function deconnecter() {
    await authApi.deconnexion()
    setUtilisateur(null)
  }

  async function rafraichirUtilisateur() {
    const u = await authApi.recupererUtilisateurCourant()
    setUtilisateur(u)
  }

  return (
    <AuthContext.Provider value={{ utilisateur, chargement, connecter, deconnecter, rafraichirUtilisateur }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth doit être utilisé dans <AuthProvider>')
  return ctx
}
