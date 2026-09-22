from django.contrib.auth.models import AbstractUser
from django.db import models


class RoleHierarchique(models.TextChoices):
    AGENT = "AGENT", "Agent"
    CHEF_SERVICE = "CHEF_SERVICE", "Chef de service"
    DIRECTEUR = "DIRECTEUR", "Directeur"
    CHEF_CABINET = "CHEF_CABINET", "Chef de cabinet"


class Direction(models.Model):
    """Une direction du ministère, dirigée par un directeur."""

    nom = models.CharField(max_length=150, unique=True)
    directeur = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direction_dirigee",
    )

    def __str__(self):
        return self.nom


class Service(models.Model):
    """Un service, rattaché à une direction, dirigé par un chef de service."""

    nom = models.CharField(max_length=150)
    direction = models.ForeignKey(Direction, on_delete=models.PROTECT, related_name="services")
    chef_service = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_dirige",
    )

    class Meta:
        unique_together = ("nom", "direction")

    def __str__(self):
        return f"{self.nom} ({self.direction.nom})"


class User(AbstractUser):
    """Agent du ministère. Le matricule est l'identifiant métier stable (voir CLAUDE.md)."""

    matricule = models.CharField(max_length=20, unique=True)
    must_change_password = models.BooleanField(
        default=True,
        help_text="Force le changement du mot de passe temporaire à la première connexion.",
    )
    role_hierarchique = models.CharField(
        max_length=20, choices=RoleHierarchique.choices, default=RoleHierarchique.AGENT
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agents",
        help_text="Service de rattachement de l'agent (vide pour un directeur ou le chef de cabinet).",
    )

    REQUIRED_FIELDS = ["email", "first_name", "last_name", "matricule"]

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.matricule
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.matricule} — {self.first_name} {self.last_name}"
