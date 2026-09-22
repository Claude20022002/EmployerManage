# Perspectives

Évolutions possibles après cette première version. Classées par ce qui comble un manque du périmètre actuel vs. ce qui étendrait le projet au-delà de sa portée initiale — distinction utile pour prioriser avec le client métier plutôt que de tout traiter comme équivalent.

## Compléter le périmètre actuel

- **Calendrier des jours fériés guinéens** dans le calcul des jours ouvrables (`conges/services.py::nombre_jours` n'exclut que les week-ends aujourd'hui).
- **Notifications** (email a minima) lors d'un changement de statut de demande et lors de la création d'un compte agent — actuellement tout est consulté en se connectant à l'application, rien n'est poussé.
- **Gestion complète de l'organisation** : suppression/renommage de directions et services depuis l'interface (seules la création et l'assignation d'un directeur/chef de service existent).
- **Historique des décisions RH** : qui a créé quel compte, quand — utile pour l'audit administratif, pas suivi pour l'instant au-delà des logs serveur bruts.
- **Durcissement production réel** : reverse proxy/TLS devant `docker-compose.prod.yml`, sauvegarde PostgreSQL automatisée, hébergement choisi et testé en conditions réelles (actuellement une démonstration conteneurisée, pas une infrastructure de production).

## Extensions plausibles (à confirmer avec le client métier avant de s'engager)

- **Tableau de bord** pour la hiérarchie (vision d'ensemble des congés en cours par service/direction) — utile mais absent du cahier des charges initial.
- **Export** (PDF/Excel) de rapports de congés par période, par service.
- **Solde de congés** si le besoin évolue vers un suivi de droits acquis/consommés (voir docs/05 — délibérément absent aujourd'hui car non demandé).
- **Application mobile ou PWA** pour la soumission/validation en mobilité — frappe/hrms, la référence fonctionnelle initiale, avait cette fonctionnalité (voir docs/00).
- **Vérification d'attestation hors-ligne** (signature numérique/PKI) si la vérification par consultation serveur (choix actuel, voir docs/05) s'avère insuffisante en pratique (ex. besoin de vérifier un document sans connexion internet).

## Ce qui ne devrait probablement pas être ajouté sans une vraie demande

Paie, recrutement, évaluations de performance et les autres modules qu'une plateforme RH généraliste comme frappe/hrms embarque nativement : hors du périmètre exprimé par le client pour ce projet (gestion des congés uniquement). Les ajouter « parce que c'est possible » irait contre la discipline de scope tenue jusqu'ici (voir [CLAUDE.md](../CLAUDE.md)).
