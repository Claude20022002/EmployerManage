from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("agents", views.AgentAdminViewSet, basename="agent")

urlpatterns = [
    path("csrf/", views.csrf, name="csrf"),
    path("connexion/", views.connexion, name="connexion"),
    path("deconnexion/", views.deconnexion, name="deconnexion"),
    path("moi/", views.MoiView.as_view(), name="moi"),
    path("changer-mot-de-passe/", views.ChangerMotDePasseView.as_view(), name="changer-mot-de-passe"),
    path("services/", views.ServiceListView.as_view(), name="services"),
] + router.urls
