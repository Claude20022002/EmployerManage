from django.contrib import admin
from django.urls import include, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("conges.urls")),
]

# Les justificatifs/attestations (MEDIA_ROOT) ne sont volontairement PAS servis en statique ici,
# même en dev : ce sont des documents sensibles (rapports médicaux…). Ils passent uniquement par
# les vues authentifiées de conges/views.py (fichier_justificatif, fichier_attestation), qui
# vérifient est_implique() avant de streamer le fichier.
