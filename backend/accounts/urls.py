from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.csrf, name="csrf"),
    path("connexion/", views.connexion, name="connexion"),
    path("deconnexion/", views.deconnexion, name="deconnexion"),
    path("moi/", views.MoiView.as_view(), name="moi"),
    path("changer-mot-de-passe/", views.ChangerMotDePasseView.as_view(), name="changer-mot-de-passe"),
]
