from django.core.management.base import BaseCommand

from accounts.models import Direction, RoleHierarchique, Service, User
from conges.models import TypeConge, TypeCongeJustificatifRequis, TypeJustificatif

MOT_DE_PASSE_DEMO = "Demo1234!"


class Command(BaseCommand):
    help = "Crée des données de démonstration (hiérarchie, types de congés, agents) pour tester l'application."

    def handle(self, *args, **options):
        direction, _ = Direction.objects.get_or_create(nom="Direction du Budget")
        service, _ = Service.objects.get_or_create(nom="Service Solde", direction=direction)

        chef_cabinet = self._upsert_user("CC001", "Camara", "Aissatou", RoleHierarchique.CHEF_CABINET)
        directeur = self._upsert_user("DIR001", "Diallo", "Mamadou", RoleHierarchique.DIRECTEUR)
        direction.directeur = directeur
        direction.save()

        chef_service = self._upsert_user(
            "CS001", "Barry", "Fatoumata", RoleHierarchique.CHEF_SERVICE, service=service
        )
        service.chef_service = chef_service
        service.save()

        agent = self._upsert_user("AG001", "Sylla", "Ibrahima", RoleHierarchique.AGENT, service=service)
        rh = self._upsert_user("RH001", "Kaba", "Mariame", RoleHierarchique.AGENT, is_staff=True)

        # Maladie courte/longue durée : seuil et justificatif renforcé confirmés par l'utilisateur
        # le 2026-09-22 (3 mois ; avis du conseil de santé pour la longue durée) — voir
        # docs/03-architecture.md.
        types = [
            ("normal", "Congé normal", 30, 30, True, []),
            ("maternite", "Congé de maternité", 90, 90, False, ["certificat-grossesse"]),
            ("maladie-courte-duree", "Congé de maladie (courte durée)", 1, 90, False, ["bulletin-paie", "rapport-medical"]),
            (
                "maladie-longue-duree",
                "Congé de maladie (longue durée)",
                91,
                None,
                False,
                ["bulletin-paie", "rapport-medical", "avis-conseil-sante"],
            ),
            ("formation", "Congé de formation", 90, None, False, ["arrete-engagement", "acte-affectation", "attestation-bac"]),
            ("exceptionnel", "Congé exceptionnel", 1, 10, False, []),
        ]
        justificatifs_libelles = {
            "certificat-grossesse": "Certificat de grossesse",
            "bulletin-paie": "Bulletin de paie",
            "rapport-medical": "Rapport médical",
            "avis-conseil-sante": "Avis du conseil de santé",
            "arrete-engagement": "Arrêté d'engagement",
            "acte-affectation": "Acte d'affectation",
            "attestation-bac": "Copie de l'attestation du BAC",
        }
        for code, libelle in justificatifs_libelles.items():
            TypeJustificatif.objects.get_or_create(code=code, defaults={"libelle": libelle})

        for code, libelle, dmin, dmax, ouvrable, justificatifs in types:
            type_conge, _ = TypeConge.objects.update_or_create(
                code=code,
                defaults={
                    "libelle": libelle,
                    "duree_min_jours": dmin,
                    "duree_max_jours": dmax,
                    "jours_ouvrables_uniquement": ouvrable,
                },
            )
            for jcode in justificatifs:
                TypeCongeJustificatifRequis.objects.get_or_create(
                    type_conge=type_conge, type_justificatif=TypeJustificatif.objects.get(code=jcode)
                )

        self.stdout.write(self.style.SUCCESS("Données de démonstration créées."))
        self.stdout.write(f"Mot de passe pour tous les comptes de démo : {MOT_DE_PASSE_DEMO}")
        for u in [agent, chef_service, directeur, chef_cabinet, rh]:
            self.stdout.write(f"  {u.matricule} — {u.role_hierarchique}{' (staff/RH)' if u.is_staff else ''} — {u.first_name} {u.last_name}")

    def _upsert_user(self, matricule, nom, prenom, role, service=None, is_staff=False):
        user, cree = User.objects.get_or_create(
            matricule=matricule,
            defaults={
                "username": matricule,
                "first_name": prenom,
                "last_name": nom,
                "email": f"{matricule.lower()}@mefb.gouv.gn",
                "role_hierarchique": role,
                "service": service,
                "must_change_password": False,
                "is_staff": is_staff,
            },
        )
        if cree:
            user.set_password(MOT_DE_PASSE_DEMO)
            user.save()
        return user
