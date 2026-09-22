from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import (
    Attestation,
    DemandeConge,
    EtapeValidation,
    JustificatifDemande,
    TypeConge,
    TypeJustificatif,
)


class TypeJustificatifSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeJustificatif
        fields = ["id", "code", "libelle"]


class TypeCongeSerializer(serializers.ModelSerializer):
    justificatifs_requis = serializers.SerializerMethodField()

    class Meta:
        model = TypeConge
        fields = [
            "id",
            "code",
            "libelle",
            "duree_min_jours",
            "duree_max_jours",
            "jours_ouvrables_uniquement",
            "justificatifs_requis",
        ]

    def get_justificatifs_requis(self, obj):
        return TypeJustificatifSerializer(
            [j.type_justificatif for j in obj.justificatifs_requis.select_related("type_justificatif")],
            many=True,
        ).data


class JustificatifDemandeSerializer(serializers.ModelSerializer):
    type_justificatif_libelle = serializers.CharField(source="type_justificatif.libelle", read_only=True)
    fichier_url = serializers.SerializerMethodField()

    class Meta:
        model = JustificatifDemande
        fields = ["id", "type_justificatif", "type_justificatif_libelle", "fichier", "fichier_url", "depose_le"]
        read_only_fields = ["depose_le"]
        extra_kwargs = {"fichier": {"write_only": True}}

    def get_fichier_url(self, obj):
        if not obj.demande_id:
            return None
        return f"/api/demandes/{obj.demande_id}/justificatifs/{obj.id}/fichier/"


class EtapeValidationSerializer(serializers.ModelSerializer):
    validateur = UserSerializer(read_only=True)

    class Meta:
        model = EtapeValidation
        fields = [
            "id",
            "ordre",
            "validateur",
            "role_attendu",
            "decision",
            "duree_accordee_jours",
            "commentaire",
            "decide_le",
        ]
        read_only_fields = fields


class AttestationSerializer(serializers.ModelSerializer):
    fichier_url = serializers.SerializerMethodField()

    class Meta:
        model = Attestation
        fields = ["numero_serie", "fichier_url", "generee_le"]
        read_only_fields = fields

    def get_fichier_url(self, obj):
        return f"/api/demandes/{obj.demande_id}/attestation/fichier/"


class DemandeCongeListSerializer(serializers.ModelSerializer):
    agent = UserSerializer(read_only=True)
    type_conge = TypeCongeSerializer(read_only=True)

    class Meta:
        model = DemandeConge
        fields = [
            "id",
            "agent",
            "type_conge",
            "date_debut",
            "date_fin_demandee",
            "date_fin_validee",
            "statut",
            "cree_le",
            "soumise_le",
        ]
        read_only_fields = fields


class DemandeCongeDetailSerializer(DemandeCongeListSerializer):
    etapes = EtapeValidationSerializer(many=True, read_only=True)
    justificatifs = JustificatifDemandeSerializer(many=True, read_only=True)
    attestation = AttestationSerializer(read_only=True)
    motif = serializers.CharField(read_only=True)

    class Meta(DemandeCongeListSerializer.Meta):
        fields = DemandeCongeListSerializer.Meta.fields + ["motif", "etapes", "justificatifs", "attestation"]


class DemandeCongeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeConge
        fields = ["type_conge", "date_debut", "date_fin_demandee", "motif"]

    def create(self, validated_data):
        validated_data["agent"] = self.context["request"].user
        return super().create(validated_data)


class DecisionEtapeSerializer(serializers.Serializer):
    commentaire = serializers.CharField(required=False, allow_blank=True, default="")
    duree_accordee_jours = serializers.IntegerField(required=False, min_value=1)
