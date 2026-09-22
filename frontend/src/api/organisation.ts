import { client } from './client'
import type { Direction, Service } from '../types'

export async function listerDirections(): Promise<Direction[]> {
  const { data } = await client.get('/auth/directions/')
  return data
}

export async function creerDirection(nom: string): Promise<Direction> {
  const { data } = await client.post('/auth/directions/', { nom })
  return data
}

export async function assignerDirecteur(directionId: number, directeurId: number): Promise<Direction> {
  const { data } = await client.patch(`/auth/directions/${directionId}/`, { directeur: directeurId })
  return data
}

export async function listerServices(): Promise<Service[]> {
  const { data } = await client.get('/auth/services/')
  return data
}

export async function creerService(nom: string, directionId: number): Promise<Service> {
  const { data } = await client.post('/auth/services/', { nom, direction: directionId })
  return data
}

export async function assignerChefService(serviceId: number, chefServiceId: number): Promise<Service> {
  const { data } = await client.patch(`/auth/services/${serviceId}/`, { chef_service: chefServiceId })
  return data
}
