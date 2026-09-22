"""
Construction du circuit de validation hiérarchique et cycle de vie d'une demande de congé.

Règle (cahier des charges) : une demande de congé peut être initiée par un agent, un chef de
service ou un directeur ; elle remonte alors uniquement les niveaux hiérarchiques strictement
supérieurs au demandeur, jusqu'au chef de cabinet inclus.
"""

import datetime

from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import RoleHierarchique, User

from .attestation import generer_attestation
from .models import DecisionEtape, DemandeConge, EtapeValidation, StatutDemande


def _trouver_chef_cabinet() -> User:
    chef_cabinet = User.objects.filter(role_hierarchique=RoleHierarchique.CHEF_CABINET, is_active=True).first()
    if chef_cabinet is None:
        raise ValidationError("Aucun chef de cabinet n'est configuré : impossible de router la demande.")
    return chef_cabinet


def construire_circuit_validation(demande) -> list[EtapeValidation]:
    """
    Calcule et enregistre les étapes de validation pour `demande`, selon le rôle hiérarchique
    de `demande.agent`. Doit être appelé une seule fois, à la soumission de la demande.
    """
    agent = demande.agent
    chaine: list[tuple[User, str]] = []

    if agent.role_hierarchique == RoleHierarchique.CHEF_CABINET:
        raise ValidationError(
            "Le chef de cabinet est le dernier niveau hiérarchique : "
            "la validation de ses propres congés n'est pas couverte par le cahier des charges "
            "actuel, à clarifier avec le client métier."
        )

    if agent.role_hierarchique == RoleHierarchique.AGENT:
        if agent.service is None or agent.service.chef_service is None:
            raise ValidationError(f"{agent} n'a pas de chef de service configuré.")
        chaine.append((agent.service.chef_service, RoleHierarchique.CHEF_SERVICE))
        direction = agent.service.direction
        if direction.directeur is None:
            raise ValidationError(f"La direction « {direction} » n'a pas de directeur configuré.")
        chaine.append((direction.directeur, RoleHierarchique.DIRECTEUR))

    elif agent.role_hierarchique == RoleHierarchique.CHEF_SERVICE:
        direction = agent.service.direction if agent.service else None
        if direction is None or direction.directeur is None:
            raise ValidationError(f"{agent} n'a pas de directeur de rattachement configuré.")
        chaine.append((direction.directeur, RoleHierarchique.DIRECTEUR))

    elif agent.role_hierarchique == RoleHierarchique.DIRECTEUR:
        pass  # ne remonte qu'au chef de cabinet, ajouté ci-dessous

    chaine.append((_trouver_chef_cabinet(), RoleHierarchique.CHEF_CABINET))

    etapes = [
        EtapeValidation.objects.create(
            demande=demande,
            ordre=ordre,
            validateur=validateur,
            role_attendu=role,
        )
        for ordre, (validateur, role) in enumerate(chaine, start=1)
    ]
    return etapes


def nombre_jours(date_debut: datetime.date, date_fin: datetime.date, jours_ouvrables_uniquement: bool) -> int:
    """
    Nombre de jours de la période, bornes incluses. En mode "jours ouvrables", exclut seulement
    les week-ends : aucun calendrier des jours fériés guinéens n'est modélisé pour l'instant
    (voir CLAUDE.md — à confirmer avec le client métier avant d'en coder un).
    """
    if date_fin < date_debut:
        raise ValidationError("La date de fin ne peut pas précéder la date de début.")
    if not jours_ouvrables_uniquement:
        return (date_fin - date_debut).days + 1
    jours = 0
    jour = date_debut
    while jour <= date_fin:
        if jour.weekday() < 5:  # 0=lundi ... 4=vendredi
            jours += 1
        jour += datetime.timedelta(days=1)
    return jours


def valider_duree(type_conge, date_debut: datetime.date, date_fin: datetime.date) -> int:
    jours = nombre_jours(date_debut, date_fin, type_conge.jours_ouvrables_uniquement)
    if jours < type_conge.duree_min_jours:
        raise ValidationError(
            f"{type_conge.libelle} requiert au moins {type_conge.duree_min_jours} jour(s), "
            f"{jours} demandé(s)."
        )
    if type_conge.duree_max_jours and jours > type_conge.duree_max_jours:
        raise ValidationError(
            f"{type_conge.libelle} ne peut excéder {type_conge.duree_max_jours} jour(s), "
            f"{jours} demandé(s)."
        )
    return jours


def justificatifs_manquants(demande) -> list:
    requis = {j.type_justificatif_id for j in demande.type_conge.justificatifs_requis.all()}
    fournis = set(demande.justificatifs.values_list("type_justificatif_id", flat=True))
    manquants = requis - fournis
    if not manquants:
        return []
    from .models import TypeJustificatif

    return list(TypeJustificatif.objects.filter(id__in=manquants))


def soumettre_demande(demande) -> DemandeConge:
    if demande.statut != StatutDemande.BROUILLON:
        raise ValidationError("Seule une demande en brouillon peut être soumise.")

    valider_duree(demande.type_conge, demande.date_debut, demande.date_fin_demandee)

    manquants = justificatifs_manquants(demande)
    if manquants:
        libelles = ", ".join(j.libelle for j in manquants)
        raise ValidationError(f"Justificatif(s) manquant(s) : {libelles}.")

    demande.date_fin_validee = demande.date_fin_demandee
    demande.statut = StatutDemande.EN_COURS
    demande.soumise_le = timezone.now()
    demande.save()
    construire_circuit_validation(demande)
    return demande


def etape_courante(demande) -> EtapeValidation | None:
    if demande.statut != StatutDemande.EN_COURS:
        return None
    return demande.etapes.filter(decision=DecisionEtape.EN_ATTENTE).order_by("ordre").first()


def approuver_etape(etape: EtapeValidation, commentaire: str = "", duree_accordee_jours: int | None = None):
    demande = etape.demande
    if etape_courante(demande) != etape:
        raise ValidationError("Cette étape n'est pas (ou plus) actionnable.")

    etape.decision = DecisionEtape.APPROUVEE
    etape.commentaire = commentaire
    etape.decide_le = timezone.now()
    if duree_accordee_jours is not None:
        etape.duree_accordee_jours = duree_accordee_jours
        demande.date_fin_validee = demande.date_debut + datetime.timedelta(days=duree_accordee_jours - 1)
        demande.save()
    etape.save()

    if etape_courante(demande) is None:
        demande.statut = StatutDemande.APPROUVEE
        demande.save()
        generer_attestation(demande)

    return etape


def rejeter_etape(etape: EtapeValidation, commentaire: str):
    demande = etape.demande
    if etape_courante(demande) != etape:
        raise ValidationError("Cette étape n'est pas (ou plus) actionnable.")
    if not commentaire:
        raise ValidationError("Un commentaire justifiant le rejet est requis.")

    etape.decision = DecisionEtape.REJETEE
    etape.commentaire = commentaire
    etape.decide_le = timezone.now()
    etape.save()

    demande.statut = StatutDemande.REJETEE
    demande.save()
    return etape


def annuler_demande(demande: DemandeConge):
    """L'agent retire sa propre demande avant qu'elle ne soit tranchée définitivement."""
    if demande.statut not in (StatutDemande.BROUILLON, StatutDemande.EN_COURS):
        raise ValidationError("Seule une demande en brouillon ou en cours peut être annulée.")
    demande.statut = StatutDemande.ANNULEE
    demande.save()
    return demande
