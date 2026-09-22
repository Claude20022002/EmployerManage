import { client } from './client'
import type { DemandeCongeDetail, DemandeCongeListe, TypeConge } from '../types'

export async function listerTypesConge(): Promise<TypeConge[]> {
  const { data } = await client.get('/types-conge/')
  return data
}

export async function creerDemande(payload: {
  type_conge: number
  date_debut: string
  date_fin_demandee: string
  motif?: string
}): Promise<DemandeCongeDetail> {
  const { data } = await client.post('/demandes/', payload)
  return data
}

export async function ajouterJustificatif(
  demandeId: number,
  typeJustificatifId: number,
  fichier: File,
): Promise<void> {
  const form = new FormData()
  form.append('type_justificatif', String(typeJustificatifId))
  form.append('fichier', fichier)
  await client.post(`/demandes/${demandeId}/justificatifs/`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export async function soumettreDemande(demandeId: number): Promise<DemandeCongeDetail> {
  const { data } = await client.post(`/demandes/${demandeId}/soumettre/`)
  return data
}

export async function mesDemandes(): Promise<DemandeCongeListe[]> {
  const { data } = await client.get('/demandes/')
  return data
}

export async function demandesAValider(): Promise<DemandeCongeListe[]> {
  const { data } = await client.get('/demandes/a-valider/')
  return data
}

export async function obtenirDemande(id: number): Promise<DemandeCongeDetail> {
  const { data } = await client.get(`/demandes/${id}/`)
  return data
}

export async function approuverEtape(
  demandeId: number,
  etapeId: number,
  commentaire: string,
  dureeAccordeeJours?: number,
): Promise<DemandeCongeDetail> {
  const { data } = await client.post(`/demandes/${demandeId}/etapes/${etapeId}/approuver/`, {
    commentaire,
    ...(dureeAccordeeJours ? { duree_accordee_jours: dureeAccordeeJours } : {}),
  })
  return data
}

export async function rejeterEtape(
  demandeId: number,
  etapeId: number,
  commentaire: string,
): Promise<DemandeCongeDetail> {
  const { data } = await client.post(`/demandes/${demandeId}/etapes/${etapeId}/rejeter/`, { commentaire })
  return data
}

export interface ResultatVerification {
  valide: boolean
  numero_serie?: string
  agent?: string
  matricule?: string
  type_conge?: string
  date_debut?: string
  date_fin?: string
  delivree_le?: string
}

export async function verifierAttestation(numeroSerie: string, code: string): Promise<ResultatVerification> {
  try {
    const { data } = await client.get(`/verification/${numeroSerie}/`, { params: { code } })
    return data
  } catch {
    return { valide: false }
  }
}
