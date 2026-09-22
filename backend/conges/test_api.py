from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from accounts.models import Direction, RoleHierarchique, Service, User
from conges.models import Attestation, StatutDemande, TypeConge, TypeJustificatif
from conges.models import TypeCongeJustificatifRequis as Requis


def _make_user(matricule, role, service=None, mot_de_passe="motdepasse123"):
    user = User.objects.create_user(
        username=matricule,
        matricule=matricule,
        email=f"{matricule}@mefb.gouv.gn",
        first_name="Prénom",
        last_name="Nom",
        role_hierarchique=role,
        service=service,
        password=mot_de_passe,
    )
    return user


class ParcoursCompletDemandeCongeTests(APITestCase):
    """Parcours critique : connexion -> soumission -> 3 niveaux d'approbation -> attestation."""

    def setUp(self):
        cache.clear()
        self.direction = Direction.objects.create(nom="Direction du Budget")
        self.service = Service.objects.create(nom="Service Solde", direction=self.direction)

        self.chef_cabinet = _make_user("CC001", RoleHierarchique.CHEF_CABINET)
        self.directeur = _make_user("DIR001", RoleHierarchique.DIRECTEUR)
        self.direction.directeur = self.directeur
        self.direction.save()

        self.chef_service = _make_user("CS001", RoleHierarchique.CHEF_SERVICE, service=self.service)
        self.service.chef_service = self.chef_service
        self.service.save()

        self.agent = _make_user("AG001", RoleHierarchique.AGENT, service=self.service)

        self.type_conge = TypeConge.objects.create(
            code="maladie", libelle="Congé de maladie", duree_min_jours=1, duree_max_jours=30
        )
        self.rapport_medical = TypeJustificatif.objects.create(code="rapport-medical", libelle="Rapport médical")
        Requis.objects.create(type_conge=self.type_conge, type_justificatif=self.rapport_medical)

    def _connecter(self, matricule, mot_de_passe="motdepasse123"):
        response = self.client.post("/api/auth/connexion/", {"matricule": matricule, "mot_de_passe": mot_de_passe})
        self.assertEqual(response.status_code, 200, response.data)

    def test_parcours_complet(self):
        # 1. L'agent se connecte et soumet sa demande
        self._connecter("AG001")

        response = self.client.post(
            "/api/demandes/",
            {"type_conge": self.type_conge.id, "date_debut": "2027-03-01", "date_fin_demandee": "2027-03-05"},
        )
        self.assertEqual(response.status_code, 201, response.data)
        demande_id = response.data["id"]
        self.assertEqual(response.data["statut"], StatutDemande.BROUILLON)

        # Sans justificatif, la soumission doit être refusée
        response = self.client.post(f"/api/demandes/{demande_id}/soumettre/")
        self.assertEqual(response.status_code, 400)

        fichier = SimpleUploadedFile("rapport.pdf", b"contenu-pdf", content_type="application/pdf")
        response = self.client.post(
            f"/api/demandes/{demande_id}/justificatifs/",
            {"type_justificatif": self.rapport_medical.id, "fichier": fichier},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)

        response = self.client.post(f"/api/demandes/{demande_id}/soumettre/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["statut"], StatutDemande.EN_COURS)
        etapes = response.data["etapes"]
        self.assertEqual([e["role_attendu"] for e in etapes], ["CHEF_SERVICE", "DIRECTEUR", "CHEF_CABINET"])

        # Un tiers ne peut pas voir la demande
        outsider = _make_user("XX001", RoleHierarchique.AGENT)
        self.client.logout()
        self._connecter("XX001")
        response = self.client.get(f"/api/demandes/{demande_id}/")
        self.assertEqual(response.status_code, 403)

        # 2. Le chef de service approuve
        self.client.logout()
        self._connecter("CS001")
        response = self.client.get("/api/demandes/a-valider/")
        self.assertEqual(len(response.data), 1)
        etape_cs = etapes[0]["id"]
        response = self.client.post(
            f"/api/demandes/{demande_id}/etapes/{etape_cs}/approuver/", {"commentaire": "OK pour moi"}
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["statut"], StatutDemande.EN_COURS)

        # 3. Le directeur approuve pour une durée différente (4 jours au lieu de 5)
        self.client.logout()
        self._connecter("DIR001")
        etape_dir = response.data["etapes"][1]["id"]
        response = self.client.post(
            f"/api/demandes/{demande_id}/etapes/{etape_dir}/approuver/",
            {"commentaire": "Validé pour 4 jours", "duree_accordee_jours": 4},
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["date_fin_validee"], "2027-03-04")
        self.assertEqual(response.data["statut"], StatutDemande.EN_COURS)

        # 4. Le chef de cabinet approuve -> attestation générée
        self.client.logout()
        self._connecter("CC001")
        etape_cab = response.data["etapes"][2]["id"]
        response = self.client.post(
            f"/api/demandes/{demande_id}/etapes/{etape_cab}/approuver/", {"commentaire": "Validé"}
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["statut"], StatutDemande.APPROUVEE)
        self.assertIsNotNone(response.data["attestation"])

        attestation = Attestation.objects.get(demande_id=demande_id)
        self.assertTrue(attestation.fichier_pdf.name.endswith(".pdf"))
        self.assertTrue(attestation.hash_verification)

        # 5. Vérification publique (sans authentification)
        self.client.logout()
        fragment = attestation.hash_verification[:12]
        response = self.client.get(f"/api/verification/{attestation.numero_serie}/?code={fragment}")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["valide"])
        self.assertEqual(response.data["matricule"], "AG001")

        # Mauvais code -> échec, sans révéler d'information
        response = self.client.get(f"/api/verification/{attestation.numero_serie}/?code=000000000000")
        self.assertEqual(response.status_code, 404)

    def test_rejet_arrete_le_circuit(self):
        self._connecter("AG001")
        response = self.client.post(
            "/api/demandes/",
            {"type_conge": self.type_conge.id, "date_debut": "2027-03-01", "date_fin_demandee": "2027-03-05"},
        )
        demande_id = response.data["id"]
        fichier = SimpleUploadedFile("rapport.pdf", b"contenu-pdf", content_type="application/pdf")
        self.client.post(
            f"/api/demandes/{demande_id}/justificatifs/",
            {"type_justificatif": self.rapport_medical.id, "fichier": fichier},
            format="multipart",
        )
        response = self.client.post(f"/api/demandes/{demande_id}/soumettre/")
        etape_cs = response.data["etapes"][0]["id"]

        self.client.logout()
        self._connecter("CS001")
        response = self.client.post(
            f"/api/demandes/{demande_id}/etapes/{etape_cs}/rejeter/", {"commentaire": "Effectif insuffisant"}
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["statut"], StatutDemande.REJETEE)

        # Le directeur ne peut plus agir : l'étape n'est plus actionnable
        self.client.logout()
        self._connecter("DIR001")
        etape_dir = response.data["etapes"][1]["id"]
        response = self.client.post(
            f"/api/demandes/{demande_id}/etapes/{etape_dir}/approuver/", {"commentaire": "trop tard"}
        )
        self.assertEqual(response.status_code, 400)

    def test_annulation_par_le_demandeur(self):
        self._connecter("AG001")
        response = self.client.post(
            "/api/demandes/",
            {"type_conge": self.type_conge.id, "date_debut": "2027-04-01", "date_fin_demandee": "2027-04-05"},
        )
        demande_id = response.data["id"]

        response = self.client.post(f"/api/demandes/{demande_id}/annuler/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["statut"], StatutDemande.ANNULEE)

        # Une demande annulée ne peut plus être annulée à nouveau
        response = self.client.post(f"/api/demandes/{demande_id}/annuler/")
        self.assertEqual(response.status_code, 400)

    def test_un_tiers_ne_peut_pas_annuler_la_demande_dautrui(self):
        self._connecter("AG001")
        response = self.client.post(
            "/api/demandes/",
            {"type_conge": self.type_conge.id, "date_debut": "2027-04-01", "date_fin_demandee": "2027-04-05"},
        )
        demande_id = response.data["id"]

        self.client.logout()
        self._connecter("CS001")
        response = self.client.post(f"/api/demandes/{demande_id}/annuler/")
        self.assertEqual(response.status_code, 403)
