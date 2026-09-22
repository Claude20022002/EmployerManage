import { client } from './client'
import type { RoleHierarchique, Utilisateur } from '../types'

export async function listerAgents(): Promise<Utilisateur[]> {
  const { data } = await client.get('/auth/agents/')
  return data
}

export interface CreationAgentPayload {
  matricule: string
  first_name: string
  last_name: string
  email: string
  role_hierarchique: RoleHierarchique
  service: number | null
}

export interface AgentCree extends Utilisateur {
  mot_de_passe_temporaire: string
}

export async function creerAgent(payload: CreationAgentPayload): Promise<AgentCree> {
  const { data } = await client.post('/auth/agents/', payload)
  return data
}
