# Perspectives

Évolutions possibles après cette première version. Classées par ce qui comble un manque du périmètre actuel vs. ce qui étendrait le projet au-delà de sa portée initiale — distinction utile pour prioriser avec le client métier plutôt que de tout traiter comme équivalent.

## Compléter le périmètre actuel

- **Compléter le calendrier des jours fériés** : `JourFerie` existe et est déjà pris en compte dans `nombre_jours`, mais seules les fêtes civiles à date fixe sont pré-remplies (voir docs/03) — les fêtes mobiles (Tabaski, Maouloud, fin du Ramadan...) doivent être ajoutées chaque année.
- **Fournisseur SMTP réel** : les notifications email existent et sont testées (`conges/notifications.py`), mais tournent en mode console (rien n'est réellement envoyé) faute de fournisseur SMTP choisi.
- **Gestion complète de l'organisation** : suppression/renommage de directions et services depuis l'interface (seules la création et l'assignation d'un directeur/chef de service existent).
- **Historique des décisions RH** : qui a créé quel compte, quand — utile pour l'audit administratif, pas suivi pour l'instant au-delà des logs serveur bruts.
- **Renouvellement automatique du certificat TLS** (Let's Encrypt/certbot) — le reverse proxy existe et fonctionne (voir docs/03), mais le certificat doit être renouvelé manuellement.
- **Sauvegardes vers un stockage distant** : le mécanisme de sauvegarde/restauration PostgreSQL existe et est testé, mais les fichiers restent sur la machine hôte — à copier vers un stockage externe (S3 ou autre) pour survivre à une perte de la machine.
- **Hébergement réel** choisi et testé en conditions réelles (actuellement une démonstration conteneurisée locale, pas une infrastructure de production déployée).

## Extensions plausibles (à confirmer avec le client métier avant de s'engager)

- **Tableau de bord** pour la hiérarchie (vision d'ensemble des congés en cours par service/direction) — utile mais absent du cahier des charges initial.
- **Export** (PDF/Excel) de rapports de congés par période, par service.
- **Solde de congés** si le besoin évolue vers un suivi de droits acquis/consommés (voir docs/05 — délibérément absent aujourd'hui car non demandé).
- **Application mobile ou PWA** pour la soumission/validation en mobilité — frappe/hrms, la référence fonctionnelle initiale, avait cette fonctionnalité (voir docs/00).
- **Vérification d'attestation hors-ligne** (signature numérique/PKI) si la vérification par consultation serveur (choix actuel, voir docs/05) s'avère insuffisante en pratique (ex. besoin de vérifier un document sans connexion internet).

## Ce qui ne devrait probablement pas être ajouté sans une vraie demande

Paie, recrutement, évaluations de performance et les autres modules qu'une plateforme RH généraliste comme frappe/hrms embarque nativement : hors du périmètre exprimé par le client pour ce projet (gestion des congés uniquement). Les ajouter « parce que c'est possible » irait contre la discipline de scope tenue jusqu'ici (voir [CLAUDE.md](../CLAUDE.md)).
