import type { StatutDemande } from '../types'

const LIBELLES: Record<StatutDemande, string> = {
  BROUILLON: 'Brouillon',
  EN_COURS: 'En cours de validation',
  APPROUVEE: 'Approuvée',
  REJETEE: 'Rejetée',
  ANNULEE: 'Annulée',
}

const CLASSES: Record<StatutDemande, string> = {
  BROUILLON: 'badge-brouillon',
  EN_COURS: 'badge-en-cours',
  APPROUVEE: 'badge-approuvee',
  REJETEE: 'badge-rejetee',
  ANNULEE: 'badge-brouillon',
}

export function StatutBadge({ statut }: { statut: StatutDemande }) {
  return <span className={`badge ${CLASSES[statut]}`}>{LIBELLES[statut]}</span>
}
