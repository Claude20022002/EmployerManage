from rest_framework.permissions import BasePermission


def est_implique(user, demande) -> bool:
    if demande.agent_id == user.id:
        return True
    if user.is_staff:
        return True
    return demande.etapes.filter(validateur=user).exists()


class PeutVoirDemande(BasePermission):
    """Le demandeur, un validateur (à n'importe quelle étape) ou un membre du staff."""

    def has_object_permission(self, request, view, obj):
        return est_implique(request.user, obj)


class EstProprietaireDemande(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.agent_id == request.user.id
