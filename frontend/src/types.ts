export type RoleHierarchique = 'AGENT' | 'CHEF_SERVICE' | 'DIRECTEUR' | 'CHEF_CABINET'

export type StatutDemande = 'BROUILLON' | 'EN_COURS' | 'APPROUVEE' | 'REJETEE' | 'ANNULEE'

export type DecisionEtape = 'EN_ATTENTE' | 'APPROUVEE' | 'REJETEE'

export interface Utilisateur {
  id: number
  username: string
  matricule: string
  first_name: string
  last_name: string
  email: string
  role_hierarchique: RoleHierarchique
  service: number | null
  must_change_password: boolean
  is_staff: boolean
}

export interface Service {
  id: number
  nom: string
  direction: number
  direction_nom: string
}

export interface TypeJustificatif {
  id: number
  code: string
  libelle: string
}

export interface TypeConge {
  id: number
  code: string
  libelle: string
  duree_min_jours: number
  duree_max_jours: number | null
  jours_ouvrables_uniquement: boolean
  justificatifs_requis: TypeJustificatif[]
}

export interface JustificatifDemande {
  id: number
  type_justificatif: number
  type_justificatif_libelle: string
  fichier: string
  depose_le: string
}

export interface EtapeValidation {
  id: number
  ordre: number
  validateur: Utilisateur
  role_attendu: RoleHierarchique
  decision: DecisionEtape
  duree_accordee_jours: number | null
  commentaire: string
  decide_le: string | null
}

export interface Attestation {
  numero_serie: string
  fichier_pdf: string
  generee_le: string
}

export interface DemandeCongeListe {
  id: number
  agent: Utilisateur
  type_conge: TypeConge
  date_debut: string
  date_fin_demandee: string
  date_fin_validee: string | null
  statut: StatutDemande
  cree_le: string
  soumise_le: string | null
}

export interface DemandeCongeDetail extends DemandeCongeListe {
  motif: string
  etapes: EtapeValidation[]
  justificatifs: JustificatifDemande[]
  attestation: Attestation | null
}
