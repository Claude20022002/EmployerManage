from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from . import services
from .attestation import code_verification_valide
from .models import Attestation, DemandeConge, JustificatifDemande, StatutDemande, TypeConge
from .permissions import PeutVoirDemande, est_implique
from .serializers import (
    DecisionEtapeSerializer,
    DemandeCongeCreateSerializer,
    DemandeCongeDetailSerializer,
    DemandeCongeListSerializer,
    JustificatifDemandeSerializer,
    TypeCongeSerializer,
)


class TypeCongeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TypeConge.objects.filter(actif=True).prefetch_related("justificatifs_requis__type_justificatif")
    serializer_class = TypeCongeSerializer
    permission_classes = [IsAuthenticated]


class DemandeCongeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return DemandeConge.objects.select_related("agent", "type_conge").prefetch_related(
            "etapes__validateur", "justificatifs__type_justificatif", "attestation"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return DemandeCongeCreateSerializer
        if self.action in ("list", "a_valider"):
            return DemandeCongeListSerializer
        return DemandeCongeDetailSerializer

    def get_object(self):
        obj = super().get_object()
        if not est_implique(self.request.user, obj):
            raise PermissionDenied("Vous n'êtes pas autorisé à consulter cette demande.")
        return obj

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(agent=request.user).order_by("-cree_le")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        demande = serializer.save()
        return Response(DemandeCongeDetailSerializer(demande).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="a-valider")
    def a_valider(self, request):
        candidates = (
            self.get_queryset()
            .filter(statut=StatutDemande.EN_COURS, etapes__validateur=request.user)
            .distinct()
            .order_by("-cree_le")
        )
        resultat = [d for d in candidates if (e := services.etape_courante(d)) and e.validateur_id == request.user.id]
        serializer = self.get_serializer(resultat, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="justificatifs")
    def ajouter_justificatif(self, request, pk=None):
        demande = self.get_object()
        if demande.agent_id != request.user.id:
            raise PermissionDenied("Seul le demandeur peut ajouter un justificatif.")
        if demande.statut != StatutDemande.BROUILLON:
            raise ValidationError("Impossible d'ajouter un justificatif après soumission de la demande.")

        serializer = JustificatifDemandeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        justificatif = JustificatifDemande.objects.create(demande=demande, **serializer.validated_data)
        return Response(JustificatifDemandeSerializer(justificatif).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="soumettre")
    def soumettre(self, request, pk=None):
        demande = self.get_object()
        if demande.agent_id != request.user.id:
            raise PermissionDenied("Seul le demandeur peut soumettre sa demande.")
        try:
            services.soumettre_demande(demande)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages if hasattr(exc, "messages") else str(exc))
        demande.refresh_from_db()
        return Response(DemandeCongeDetailSerializer(demande).data)

    @action(detail=True, methods=["post"], url_path=r"etapes/(?P<etape_id>\d+)/approuver")
    def approuver(self, request, pk=None, etape_id=None):
        return self._decider(request, pk, etape_id, approuver=True)

    @action(detail=True, methods=["post"], url_path=r"etapes/(?P<etape_id>\d+)/rejeter")
    def rejeter(self, request, pk=None, etape_id=None):
        return self._decider(request, pk, etape_id, approuver=False)

    def _decider(self, request, pk, etape_id, approuver: bool):
        demande = self.get_object()
        etape = demande.etapes.filter(id=etape_id).first()
        if etape is None:
            raise ValidationError("Étape introuvable pour cette demande.")
        if etape.validateur_id != request.user.id:
            raise PermissionDenied("Vous n'êtes pas le validateur de cette étape.")

        serializer = DecisionEtapeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            if approuver:
                services.approuver_etape(
                    etape,
                    commentaire=data.get("commentaire", ""),
                    duree_accordee_jours=data.get("duree_accordee_jours"),
                )
            else:
                services.rejeter_etape(etape, commentaire=data.get("commentaire", ""))
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages if hasattr(exc, "messages") else str(exc))

        demande.refresh_from_db()
        return Response(DemandeCongeDetailSerializer(demande).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def verifier_attestation(request, numero_serie):
    code = request.query_params.get("code", "")
    try:
        attestation = Attestation.objects.select_related("demande__agent", "demande__type_conge").get(
            numero_serie=numero_serie
        )
    except (Attestation.DoesNotExist, ValueError):
        return Response({"valide": False}, status=404)

    if not code_verification_valide(attestation.demande, attestation.numero_serie, code):
        return Response({"valide": False}, status=404)

    demande = attestation.demande
    return Response(
        {
            "valide": True,
            "numero_serie": str(attestation.numero_serie),
            "agent": f"{demande.agent.first_name} {demande.agent.last_name}",
            "matricule": demande.agent.matricule,
            "type_conge": demande.type_conge.libelle,
            "date_debut": demande.date_debut,
            "date_fin": demande.date_fin_validee,
            "delivree_le": attestation.generee_le,
        }
    )
