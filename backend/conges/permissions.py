def est_implique(user, demande) -> bool:
    """Le demandeur, un validateur (à n'importe quelle étape) ou un membre du staff.

    Appelée directement depuis DemandeCongeViewSet.get_object() plutôt que via le mécanisme
    has_object_permission de DRF, pour pouvoir lever une erreur cohérente avec les autres
    vérifications métier des actions (soumettre, annuler...).
    """
    if demande.agent_id == user.id:
        return True
    if user.is_staff:
        return True
    return demande.etapes.filter(validateur=user).exists()
