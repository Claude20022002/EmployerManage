import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Direction, RoleHierarchique, Service, User
from conges.models import JourFerie, StatutDemande, TypeConge
from conges.services import construire_circuit_validation, nombre_jours


def _make_user(matricule, role, service=None, **kwargs):
    return User.objects.create_user(
        username=matricule,
        matricule=matricule,
        email=f"{matricule}@mefb.gouv.gn",
        first_name="Prénom",
        last_name="Nom",
        role_hierarchique=role,
        service=service,
        **kwargs,
    )


class CircuitValidationTests(TestCase):
    def setUp(self):
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
            code="normal", libelle="Congé normal", duree_min_jours=30, jours_ouvrables_uniquement=True
        )

    def _demande(self, agent):
        return agent.demandes_conge.create(
            type_conge=self.type_conge,
            date_debut="2027-07-01",
            date_fin_demandee="2027-07-31",
            statut=StatutDemande.EN_COURS,
        )

    def test_agent_remonte_chef_service_puis_directeur_puis_cabinet(self):
        demande = self._demande(self.agent)
        etapes = construire_circuit_validation(demande)
        validateurs = [(e.ordre, e.validateur, e.role_attendu) for e in etapes]
        self.assertEqual(
            validateurs,
            [
                (1, self.chef_service, RoleHierarchique.CHEF_SERVICE),
                (2, self.directeur, RoleHierarchique.DIRECTEUR),
                (3, self.chef_cabinet, RoleHierarchique.CHEF_CABINET),
            ],
        )

    def test_chef_service_saute_sa_propre_etape(self):
        demande = self._demande(self.chef_service)
        etapes = construire_circuit_validation(demande)
        validateurs = [(e.ordre, e.validateur, e.role_attendu) for e in etapes]
        self.assertEqual(
            validateurs,
            [
                (1, self.directeur, RoleHierarchique.DIRECTEUR),
                (2, self.chef_cabinet, RoleHierarchique.CHEF_CABINET),
            ],
        )

    def test_directeur_ne_remonte_qu_au_chef_de_cabinet(self):
        demande = self._demande(self.directeur)
        etapes = construire_circuit_validation(demande)
        self.assertEqual(len(etapes), 1)
        self.assertEqual(etapes[0].validateur, self.chef_cabinet)
        self.assertEqual(etapes[0].role_attendu, RoleHierarchique.CHEF_CABINET)

    def test_agent_sans_chef_service_leve_une_erreur_explicite(self):
        service_orphelin = Service.objects.create(nom="Service Orphelin", direction=self.direction)
        agent_orphelin = _make_user("AG002", RoleHierarchique.AGENT, service=service_orphelin)
        demande = self._demande(agent_orphelin)
        with self.assertRaises(ValidationError):
            construire_circuit_validation(demande)

    def test_chef_cabinet_leve_une_erreur_explicite(self):
        demande = self._demande(self.chef_cabinet)
        with self.assertRaises(ValidationError):
            construire_circuit_validation(demande)


class NombreJoursTests(TestCase):
    def test_jours_ouvrables_exclut_week_ends(self):
        # Lundi 2027-03-01 -> vendredi 2027-03-05 : 5 jours ouvrables, aucun week-end dedans.
        self.assertEqual(nombre_jours(datetime.date(2027, 3, 1), datetime.date(2027, 3, 5), True), 5)

    def test_jours_ouvrables_exclut_un_jour_ferie_declare(self):
        # Même semaine, mais le mercredi est déclaré férié : 4 jours ouvrables au lieu de 5.
        JourFerie.objects.create(date=datetime.date(2027, 3, 3), libelle="Test")
        self.assertEqual(nombre_jours(datetime.date(2027, 3, 1), datetime.date(2027, 3, 5), True), 4)

    def test_jour_ferie_tombant_un_week_end_ne_compte_pas_deux_fois(self):
        # Un jour férié un samedi ne doit pas faire descendre le compte sous le nombre de jours
        # ouvrables réels de la période.
        JourFerie.objects.create(date=datetime.date(2027, 3, 6), libelle="Test (samedi)")  # samedi
        self.assertEqual(nombre_jours(datetime.date(2027, 3, 1), datetime.date(2027, 3, 5), True), 5)

    def test_jours_calendaires_ignore_jours_feries(self):
        JourFerie.objects.create(date=datetime.date(2027, 3, 3), libelle="Test")
        self.assertEqual(nombre_jours(datetime.date(2027, 3, 1), datetime.date(2027, 3, 5), False), 5)
