from unittest import mock

from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle

from .models import Direction, RoleHierarchique, Service, User


class CreationAgentTests(APITestCase):
    def setUp(self):
        cache.clear()  # le throttle de connexion (settings.py) partage un cache entre les tests
        self.direction = Direction.objects.create(nom="Direction du Budget")
        self.service = Service.objects.create(nom="Service Solde", direction=self.direction)
        self.rh = User.objects.create_user(
            username="RH001",
            matricule="RH001",
            email="rh001@mefb.gouv.gn",
            first_name="Mariame",
            last_name="Kaba",
            password="motdepasse123",
            is_staff=True,
        )
        self.agent = User.objects.create_user(
            username="AG001",
            matricule="AG001",
            email="ag001@mefb.gouv.gn",
            first_name="Ibrahima",
            last_name="Sylla",
            password="motdepasse123",
            role_hierarchique=RoleHierarchique.AGENT,
        )

    def _connecter(self, matricule):
        response = self.client.post("/api/auth/connexion/", {"matricule": matricule, "mot_de_passe": "motdepasse123"})
        self.assertEqual(response.status_code, 200, response.data)

    def test_un_agent_non_staff_ne_peut_pas_creer_de_compte(self):
        self._connecter("AG001")
        response = self.client.post(
            "/api/auth/agents/",
            {
                "matricule": "AG002",
                "first_name": "Test",
                "last_name": "Test",
                "email": "ag002@mefb.gouv.gn",
                "role_hierarchique": RoleHierarchique.AGENT,
                "service": self.service.id,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_le_personnel_rh_peut_creer_un_compte_avec_mot_de_passe_temporaire(self):
        self._connecter("RH001")
        response = self.client.post(
            "/api/auth/agents/",
            {
                "matricule": "AG002",
                "first_name": "Aissatou",
                "last_name": "Bah",
                "email": "ag002@mefb.gouv.gn",
                "role_hierarchique": RoleHierarchique.AGENT,
                "service": self.service.id,
            },
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIn("mot_de_passe_temporaire", response.data)
        self.assertTrue(len(response.data["mot_de_passe_temporaire"]) >= 8)

        nouvel_agent = User.objects.get(matricule="AG002")
        self.assertTrue(nouvel_agent.must_change_password)
        self.assertTrue(nouvel_agent.check_password(response.data["mot_de_passe_temporaire"]))

        # Le mot de passe temporaire permet de se connecter immédiatement
        self.client.logout()
        response = self.client.post(
            "/api/auth/connexion/",
            {"matricule": "AG002", "mot_de_passe": response.data["mot_de_passe_temporaire"]},
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["must_change_password"])

    def test_matricule_deja_utilise_est_rejete(self):
        self._connecter("RH001")
        response = self.client.post(
            "/api/auth/agents/",
            {
                "matricule": "AG001",
                "first_name": "Doublon",
                "last_name": "Doublon",
                "email": "doublon@mefb.gouv.gn",
                "role_hierarchique": RoleHierarchique.AGENT,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_liste_des_agents_reservee_au_staff(self):
        self._connecter("RH001")
        response = self.client.get("/api/auth/agents/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)


class GestionOrganisationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.rh = User.objects.create_user(
            username="RH001", matricule="RH001", email="rh001@mefb.gouv.gn",
            first_name="Mariame", last_name="Kaba", password="motdepasse123", is_staff=True,
        )
        self.agent = User.objects.create_user(
            username="AG001", matricule="AG001", email="ag001@mefb.gouv.gn",
            first_name="Ibrahima", last_name="Sylla", password="motdepasse123",
        )

    def _connecter(self, matricule):
        response = self.client.post("/api/auth/connexion/", {"matricule": matricule, "mot_de_passe": "motdepasse123"})
        self.assertEqual(response.status_code, 200, response.data)

    def test_rh_peut_creer_une_direction_puis_un_service(self):
        self._connecter("RH001")

        response = self.client.post("/api/auth/directions/", {"nom": "Direction du Budget"})
        self.assertEqual(response.status_code, 201, response.data)
        direction_id = response.data["id"]

        response = self.client.post(
            "/api/auth/services/", {"nom": "Service Solde", "direction": direction_id}
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["direction_nom"], "Direction du Budget")

        response = self.client.patch(f"/api/auth/directions/{direction_id}/", {"directeur": self.agent.id})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["directeur"], self.agent.id)

    def test_un_agent_non_staff_ne_peut_pas_gerer_lorganisation(self):
        self._connecter("AG001")
        response = self.client.post("/api/auth/directions/", {"nom": "Direction Test"})
        self.assertEqual(response.status_code, 403)
        response = self.client.get("/api/auth/directions/")
        self.assertEqual(response.status_code, 403)


class ThrottlingConnexionTests(APITestCase):
    """Anti-bruteforce sur /api/auth/connexion/ — voir settings.py DEFAULT_THROTTLE_RATES."""

    def setUp(self):
        cache.clear()
        User.objects.create_user(
            username="AG001", matricule="AG001", email="ag001@mefb.gouv.gn",
            first_name="Ibrahima", last_name="Sylla", password="motdepasse123",
        )

    def test_trop_de_tentatives_declenche_le_throttle(self):
        # ScopedRateThrottle.THROTTLE_RATES est un attribut de classe figé au chargement du module
        # (ScopedRateThrottle.__init__ est un no-op) : @override_settings(REST_FRAMEWORK=...) ne le
        # rafraîchit pas. On monkey-patch directement l'attribut pour tester le seuil sans dépendre
        # du THROTTLE_CONNEXION réel de l'environnement (permissif en dev, voir .env).
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"connexion": "3/min"}):
            for _ in range(3):
                response = self.client.post(
                    "/api/auth/connexion/", {"matricule": "AG001", "mot_de_passe": "mauvais-mot-de-passe"}
                )
                self.assertEqual(response.status_code, 401)

            response = self.client.post(
                "/api/auth/connexion/", {"matricule": "AG001", "mot_de_passe": "motdepasse123"}
            )
            self.assertEqual(response.status_code, 429)
