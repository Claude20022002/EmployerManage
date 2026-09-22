from rest_framework import serializers

from .models import Service, User


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "nom", "direction"]


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
        ]
        read_only_fields = fields


class ChangerMotDePasseSerializer(serializers.Serializer):
    ancien_mot_de_passe = serializers.CharField(write_only=True)
    nouveau_mot_de_passe = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["ancien_mot_de_passe"]):
            raise serializers.ValidationError({"ancien_mot_de_passe": "Mot de passe incorrect."})
        return attrs
