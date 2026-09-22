from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.middleware.csrf import get_token
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Direction, Service, User
from .serializers import (
    ChangerMotDePasseSerializer,
    CreerAgentSerializer,
    DirectionSerializer,
    ServiceSerializer,
    UserSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    """À appeler avant login/, pour récupérer le cookie csrftoken (SPA sur un autre port)."""
    return Response({"csrfToken": get_token(request)})


class ConnexionView(APIView):
    """Classe (pas @api_view) pour pouvoir déclarer throttle_scope — anti-bruteforce, voir settings.py."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "connexion"

    def post(self, request):
        matricule = request.data.get("matricule")
        mot_de_passe = request.data.get("mot_de_passe")
        if not matricule or not mot_de_passe:
            return Response({"detail": "Matricule et mot de passe requis."}, status=400)

        try:
            username = User.objects.get(matricule=matricule).username
        except User.DoesNotExist:
            return Response({"detail": "Identifiants invalides."}, status=401)

        user = authenticate(request, username=username, password=mot_de_passe)
        if user is None:
            return Response({"detail": "Identifiants invalides."}, status=401)

        login(request, user)
        return Response(UserSerializer(user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deconnexion(request):
    logout(request)
    return Response(status=204)


class MoiView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ChangerMotDePasseView(APIView):
    def post(self, request):
        serializer = ChangerMotDePasseSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["nouveau_mot_de_passe"])
        request.user.must_change_password = False
        request.user.save()
        update_session_auth_hash(request, request.user)
        return Response({"detail": "Mot de passe mis à jour."})


class AgentAdminViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Réservé au personnel RH (is_staff) : création de comptes agents. Voir CLAUDE.md."""

    permission_classes = [IsAdminUser]
    queryset = User.objects.select_related("service", "service__direction").order_by("last_name", "first_name")

    def get_serializer_class(self):
        return CreerAgentSerializer if self.action == "create" else UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agent = serializer.save()
        data = UserSerializer(agent).data
        data["mot_de_passe_temporaire"] = agent.mot_de_passe_temporaire
        return Response(data, status=status.HTTP_201_CREATED)


class DirectionViewSet(viewsets.ModelViewSet):
    """Réservé au personnel RH — gestion des directions du ministère."""

    permission_classes = [IsAdminUser]
    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = DirectionSerializer
    queryset = Direction.objects.select_related("directeur").order_by("nom")


class ServiceViewSet(viewsets.ModelViewSet):
    """Réservé au personnel RH — gestion des services rattachés à une direction."""

    permission_classes = [IsAdminUser]
    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = ServiceSerializer
    queryset = Service.objects.select_related("direction", "chef_service").order_by("nom")
