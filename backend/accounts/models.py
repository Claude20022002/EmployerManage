from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Agent du ministère. Le matricule est l'identifiant métier stable (voir CLAUDE.md)."""

    matricule = models.CharField(max_length=20, unique=True)
    must_change_password = models.BooleanField(
        default=True,
        help_text="Force le changement du mot de passe temporaire à la première connexion.",
    )

    REQUIRED_FIELDS = ["email", "first_name", "last_name", "matricule"]

    def __str__(self):
        return f"{self.matricule} — {self.first_name} {self.last_name}"
