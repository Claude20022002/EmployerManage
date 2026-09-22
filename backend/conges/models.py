import uuid

from django.conf import settings
from django.db import models


class TypeConge(models.Model):
    """Paramétrage d'un type de congé — voir CLAUDE.md, ne jamais coder les règles en dur."""

    code = models.SlugField(max_length=30, unique=True)
    libelle = models.CharField(max_length=100)
    duree_min_jours = models.PositiveIntegerField(
        help_text="Durée minimale en jours calendaires (ex. 90 pour la maternité)."
    )
    duree_max_jours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Durée maximale, si plafonnée. Vide si la durée dépend uniquement de la décision du directeur.",
    )
    jours_ouvrables_uniquement = models.BooleanField(
        default=False, help_text="Coché pour le congé normal (30 jours ouvrables)."
    )
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.libelle


class TypeJustificatif(models.Model):
    code = models.SlugField(max_length=40, unique=True)
    libelle = models.CharField(max_length=150)

    def __str__(self):
        return self.libelle


class TypeCongeJustificatifRequis(models.Model):
    """Table de jonction : quels justificatifs sont exigés pour quel type de congé."""

    type_conge = models.ForeignKey(TypeConge, on_delete=models.CASCADE, related_name="justificatifs_requis")
    type_justificatif = models.ForeignKey(TypeJustificatif, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("type_conge", "type_justificatif")

    def __str__(self):
        return f"{self.type_conge} → {self.type_justificatif}"


class StatutDemande(models.TextChoices):
    BROUILLON = "BROUILLON", "Brouillon"
    EN_COURS = "EN_COURS", "En cours de validation"
    APPROUVEE = "APPROUVEE", "Approuvée"
    REJETEE = "REJETEE", "Rejetée"
    ANNULEE = "ANNULEE", "Annulée par l'agent"


class DemandeConge(models.Model):
    """Une demande de congé et son cycle de vie complet."""

    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="demandes_conge")
    type_conge = models.ForeignKey(TypeConge, on_delete=models.PROTECT, related_name="demandes")
    date_debut = models.DateField()
    date_fin_demandee = models.DateField()
    date_fin_validee = models.DateField(
        null=True,
        blank=True,
        help_text="Peut différer de date_fin_demandee si le directeur valide pour une durée différente.",
    )
    motif = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=StatutDemande.choices, default=StatutDemande.BROUILLON)
    cree_le = models.DateTimeField(auto_now_add=True)
    soumise_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["agent", "statut"])]

    def __str__(self):
        return f"{self.agent} — {self.type_conge} ({self.date_debut} → {self.date_fin_demandee})"


class DecisionEtape(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE", "En attente"
    APPROUVEE = "APPROUVEE", "Approuvée"
    REJETEE = "REJETEE", "Rejetée"


class EtapeValidation(models.Model):
    """
    Une étape du circuit hiérarchique d'une demande (chef de service, directeur, chef de cabinet).
    La liste des étapes est calculée à la soumission selon le rôle du demandeur
    (voir conges.services.construire_circuit_validation) — un directeur qui demande un congé
    saute l'étape "chef de service", par exemple.
    """

    demande = models.ForeignKey(DemandeConge, on_delete=models.CASCADE, related_name="etapes")
    ordre = models.PositiveSmallIntegerField()
    validateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="etapes_a_valider"
    )
    role_attendu = models.CharField(max_length=20, help_text="Rôle du validateur au moment de la génération.")
    decision = models.CharField(max_length=20, choices=DecisionEtape.choices, default=DecisionEtape.EN_ATTENTE)
    duree_accordee_jours = models.PositiveIntegerField(
        null=True, blank=True, help_text="Renseigné par le directeur si la durée validée diffère de la demande."
    )
    commentaire = models.TextField(blank=True)
    decide_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["demande", "ordre"]
        unique_together = ("demande", "ordre")

    def __str__(self):
        return f"Étape {self.ordre} — {self.demande} — {self.validateur}"


def chemin_justificatif(instance, filename):
    return f"justificatifs/{instance.demande.agent.matricule}/{instance.demande_id}/{filename}"


class JustificatifDemande(models.Model):
    demande = models.ForeignKey(DemandeConge, on_delete=models.CASCADE, related_name="justificatifs")
    type_justificatif = models.ForeignKey(TypeJustificatif, on_delete=models.PROTECT)
    fichier = models.FileField(upload_to=chemin_justificatif)
    depose_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type_justificatif} — {self.demande}"


class Attestation(models.Model):
    """
    Générée à l'approbation finale d'une demande. L'authenticité repose sur numero_serie
    (unique, communicable) + hash_verification (calculé côté serveur, jamais transmis en clair
    sans le numéro de série) — permet une vérification publique sans exposer le contenu du PDF.
    """

    demande = models.OneToOneField(DemandeConge, on_delete=models.PROTECT, related_name="attestation")
    numero_serie = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    hash_verification = models.CharField(max_length=64, editable=False)
    fichier_pdf = models.FileField(upload_to="attestations/%Y/%m/")
    generee_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attestation {self.numero_serie} — {self.demande}"
