import { client } from './client'
import type { Utilisateur } from '../types'

export async function connexion(matricule: string, motDePasse: string): Promise<Utilisateur> {
  const { data } = await client.post('/auth/connexion/', { matricule, mot_de_passe: motDePasse })
  return data
}

export async function deconnexion(): Promise<void> {
  await client.post('/auth/deconnexion/')
}

export async function recupererUtilisateurCourant(): Promise<Utilisateur> {
  const { data } = await client.get('/auth/moi/')
  return data
}

export async function changerMotDePasse(ancien: string, nouveau: string): Promise<void> {
  await client.post('/auth/changer-mot-de-passe/', {
    ancien_mot_de_passe: ancien,
    nouveau_mot_de_passe: nouveau,
  })
}
