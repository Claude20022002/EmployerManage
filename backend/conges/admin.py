from django.contrib import admin

from .models import (
    Attestation,
    DemandeConge,
    EtapeValidation,
    JourFerie,
    JustificatifDemande,
    TypeConge,
    TypeCongeJustificatifRequis,
    TypeJustificatif,
)


@admin.register(JourFerie)
class JourFerieAdmin(admin.ModelAdmin):
    list_display = ("date", "libelle")
    ordering = ("date",)


class JustificatifRequisInline(admin.TabularInline):
    model = TypeCongeJustificatifRequis
    extra = 1


@admin.register(TypeConge)
class TypeCongeAdmin(admin.ModelAdmin):
    list_display = ("libelle", "code", "duree_min_jours", "duree_max_jours", "jours_ouvrables_uniquement", "actif")
    inlines = [JustificatifRequisInline]


@admin.register(TypeJustificatif)
class TypeJustificatifAdmin(admin.ModelAdmin):
    list_display = ("libelle", "code")


class EtapeValidationInline(admin.TabularInline):
    model = EtapeValidation
    extra = 0
    readonly_fields = ("ordre", "validateur", "role_attendu", "decision", "decide_le")
    can_delete = False


class JustificatifInline(admin.TabularInline):
    model = JustificatifDemande
    extra = 0


@admin.register(DemandeConge)
class DemandeCongeAdmin(admin.ModelAdmin):
    list_display = ("agent", "type_conge", "date_debut", "date_fin_demandee", "statut", "cree_le")
    list_filter = ("statut", "type_conge")
    search_fields = ("agent__matricule", "agent__first_name", "agent__last_name")
    inlines = [EtapeValidationInline, JustificatifInline]


@admin.register(Attestation)
class AttestationAdmin(admin.ModelAdmin):
    list_display = ("numero_serie", "demande", "generee_le")
    readonly_fields = ("numero_serie", "hash_verification")
