import secrets

from rest_framework import serializers

from .models import Direction, Service, User


class DirectionSerializer(serializers.ModelSerializer):
    directeur_nom = serializers.SerializerMethodField()

    class Meta:
        model = Direction
        fields = ["id", "nom", "directeur", "directeur_nom"]

    def get_directeur_nom(self, obj):
        return f"{obj.directeur.first_name} {obj.directeur.last_name}" if obj.directeur else None


class ServiceSerializer(serializers.ModelSerializer):
    direction_nom = serializers.CharField(source="direction.nom", read_only=True)
    chef_service_nom = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ["id", "nom", "direction", "direction_nom", "chef_service", "chef_service_nom"]

    def get_chef_service_nom(self, obj):
        return f"{obj.chef_service.first_name} {obj.chef_service.last_name}" if obj.chef_service else None


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "matricule",
            "first_name",
            "last_name",
            "email",
            "role_hierarchique",
            "service",
            "must_change_password",
            "is_staff",
        ]
        read_only_fields = fields


def generer_mot_de_passe_temporaire() -> str:
    return secrets.token_urlsafe(9)  # ex. "kQ3f9xLg2ZP1nA" — assez fort, lisible pour être retranscrit


class CreerAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["matricule", "first_name", "last_name", "email", "role_hierarchique", "service"]

    def create(self, validated_data):
        mot_de_passe = generer_mot_de_passe_temporaire()
        user = User(**validated_data, must_change_password=True)
        user.set_password(mot_de_passe)
        user.save()
        user.mot_de_passe_temporaire = mot_de_passe  # attaché pour la réponse, jamais stocké en base
        return user


class ChangerMotDePasseSerializer(serializers.Serializer):
    ancien_mot_de_passe = serializers.CharField(write_only=True)
    nouveau_mot_de_passe = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["ancien_mot_de_passe"]):
            raise serializers.ValidationError({"ancien_mot_de_passe": "Mot de passe incorrect."})
        return attrs
