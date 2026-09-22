import type { EtapeValidation } from '../types'

const ROLE_LIBELLE: Record<string, string> = {
  CHEF_SERVICE: 'Chef de service',
  DIRECTEUR: 'Directeur',
  CHEF_CABINET: 'Chef de cabinet',
}

export function EtapesTimeline({ etapes }: { etapes: EtapeValidation[] }) {
  return (
    <ul className="timeline">
      {etapes.map((etape) => (
        <li key={etape.id}>
          <span className={`puce ${etape.decision === 'APPROUVEE' ? 'approuvee' : etape.decision === 'REJETEE' ? 'rejetee' : ''}`} />
          <div>
            <strong>{ROLE_LIBELLE[etape.role_attendu] ?? etape.role_attendu}</strong>
            {' — '}
            {etape.validateur.first_name} {etape.validateur.last_name}
            <div className="aide">
              {etape.decision === 'EN_ATTENTE' && 'En attente de décision'}
              {etape.decision === 'APPROUVEE' &&
                `Approuvée le ${etape.decide_le ? new Date(etape.decide_le).toLocaleDateString('fr-FR') : ''}` +
                  (etape.duree_accordee_jours ? ` — durée accordée : ${etape.duree_accordee_jours} j` : '')}
              {etape.decision === 'REJETEE' &&
                `Rejetée le ${etape.decide_le ? new Date(etape.decide_le).toLocaleDateString('fr-FR') : ''}`}
              {etape.commentaire && ` — « ${etape.commentaire} »`}
            </div>
          </div>
        </li>
      ))}
    </ul>
  )
}
