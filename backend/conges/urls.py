from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("demandes", views.DemandeCongeViewSet, basename="demande")
router.register("types-conge", views.TypeCongeViewSet, basename="type-conge")
router.register("jours-feries", views.JourFerieViewSet, basename="jour-ferie")

urlpatterns = [
    path("verification/<uuid:numero_serie>/", views.verifier_attestation, name="verifier-attestation"),
] + router.urls
