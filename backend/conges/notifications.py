"""
Notifications email — envoyées au fil du circuit de validation. Best-effort : une erreur d'envoi
(SMTP indisponible, etc.) est loguée mais ne doit jamais faire échouer l'action métier qui l'a
déclenchée (une approbation reste valable même si l'email de notification échoue).
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

ROLE_LIBELLE = {
    "CHEF_SERVICE": "chef de service",
    "DIRECTEUR": "directeur",
    "CHEF_CABINET": "chef de cabinet",
}


def _envoyer(destinataire, sujet, message):
    if not destinataire:
        return
    try:
        send_mail(sujet, message, settings.DEFAULT_FROM_EMAIL, [destinataire], fail_silently=False)
    except Exception:
        logger.exception("Échec d'envoi d'email à %s (sujet : %s)", destinataire, sujet)


def notifier_nouvelle_etape(etape):
    """Le validateur de l'étape qui vient de devenir actionnable est informé."""
    demande = etape.demande
    _envoyer(
        etape.validateur.email,
        "Congé à valider — MEFB",
        (
            f"Bonjour {etape.validateur.first_name},\n\n"
            f"Une demande de congé de {demande.agent.first_name} {demande.agent.last_name} "
            f"({demande.agent.matricule}) — {demande.type_conge.libelle}, du "
            f"{demande.date_debut} au {demande.date_fin_demandee} — attend votre décision en "
            f"tant que {ROLE_LIBELLE.get(etape.role_attendu, etape.role_attendu)}.\n\n"
            f"Connectez-vous à l'application pour la traiter : {settings.FRONTEND_URL}/a-valider"
        ),
    )


def notifier_rejet(etape):
    demande = etape.demande
    _envoyer(
        demande.agent.email,
        "Votre demande de congé a été rejetée — MEFB",
        (
            f"Bonjour {demande.agent.first_name},\n\n"
            f"Votre demande de congé ({demande.type_conge.libelle}, du {demande.date_debut} au "
            f"{demande.date_fin_demandee}) a été rejetée par le {ROLE_LIBELLE.get(etape.role_attendu, etape.role_attendu)}.\n"
            f"Motif indiqué : {etape.commentaire}\n\n"
            f"Détails : {settings.FRONTEND_URL}/demandes/{demande.id}"
        ),
    )


def notifier_approbation_finale(demande):
    _envoyer(
        demande.agent.email,
        "Votre demande de congé est approuvée — attestation disponible — MEFB",
        (
            f"Bonjour {demande.agent.first_name},\n\n"
            f"Votre demande de congé ({demande.type_conge.libelle}) a été approuvée jusqu'au "
            f"{demande.date_fin_validee}. Votre attestation est disponible dans l'application.\n\n"
            f"Détails : {settings.FRONTEND_URL}/demandes/{demande.id}"
        ),
    )
