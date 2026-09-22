# Problèmes rencontrés et solutions

Journal de bord technique, tenu au fil du développement. Chaque entrée est un incident réellement rencontré (pas une anticipation théorique), avec sa cause et sa correction. Objectif : que la prochaine personne qui touche ce projet ne retombe pas dans le même piège.

## CSRF bloquait toute soumission de formulaire (cross-origin)

**Symptôme** : le premier test Playwright du parcours critique échouait dès la création d'une demande — la page affichait littéralement « CSRF Failed: CSRF token missing. » à l'écran.

**Cause** : frontend (`localhost:5173`) et backend (`localhost:8001`) sont deux origines distinctes du point de vue du navigateur. Depuis axios 1.6 (GHSA-wf5p-g6vw-rhxx), l'en-tête CSRF n'est plus attaché automatiquement aux requêtes cross-origin par défaut, même avec `xsrfCookieName`/`xsrfHeaderName` configurés.

**Correction** : ajout de `withXSRFToken: true` dans `frontend/src/api/client.ts`.

**Enseignement** : ce genre de bug ne se voit qu'en testant réellement le formulaire dans un navigateur — un test unitaire qui mocke l'appel API ne l'aurait jamais détecté. Confirme l'intérêt des tests Playwright contre les vrais serveurs de dev plutôt que des mocks.

## `docker-compose.prod.yml` a recréé le conteneur PostgreSQL de développement

**Symptôme** : en testant `docker compose -f docker-compose.prod.yml up`, Docker Compose a affiché « Container employermanage-postgres-1 Recreate » — le conteneur PostgreSQL utilisé par l'environnement de dev natif (venv + npm) a été remplacé par celui défini dans le fichier prod.

**Cause** : sans `name:` explicite, Docker Compose dérive le nom de projet du nom du dossier courant. `docker-compose.yml` (dev) et `docker-compose.prod.yml`, lancés depuis le même dossier, partageaient donc le même espace de noms — le service `postgres` du fichier prod a été traité comme *le même service* que celui du fichier dev, avec un nom de conteneur identique.

**Conséquence évitée de justesse** : le conteneur a été recréé avec un **nouveau volume** (`postgres-data-prod` au lieu de `postgres-data`), donc l'ancien volume contenant les données de dev n'a *pas* été supprimé — juste détaché. `docker compose -f docker-compose.prod.yml down` puis `docker compose up` (fichier dev) ont suffi à restaurer l'environnement, données intactes, vérifié par requête directe (`User.objects.values_list('matricule', ...)`).

**Correction** : ajout de `name: employermanage-prod` en tête de `docker-compose.prod.yml`, avec un commentaire expliquant pourquoi.

**Enseignement** : toujours nommer explicitement les projets Docker Compose dès qu'un dépôt a plusieurs fichiers compose destinés à des environnements différents. Et : avant de lancer une commande Compose inconnue sur un environnement qui contient des données utiles, vérifier `docker ps -a` avant/après plutôt que de supposer que « up » est sans risque.

## `@override_settings(REST_FRAMEWORK=...)` ne change pas le taux de throttle DRF en test

**Symptôme** : un test censé déclencher un `429 Too Many Requests` après N tentatives recevait `200`.

**Cause** : `ScopedRateThrottle.THROTTLE_RATES` est un attribut de **classe**, figé une seule fois au chargement du module `rest_framework.throttling` (`ScopedRateThrottle.__init__` est un no-op qui ne le réévalue jamais par instance). Le signal `setting_changed` que Django déclenche pour `@override_settings` réinitialise bien le cache interne de DRF (`api_settings`), mais `SimpleRateThrottle.THROTTLE_RATES` ayant déjà capturé sa valeur au moment de l'import du module, il ne se remet pas à jour automatiquement.

**Correction** : `unittest.mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", {...})` dans le test, qui modifie directement l'attribut de classe pour la durée du test — voir `accounts/tests.py::ThrottlingConnexionTests`.

**Enseignement** : `@override_settings` ne suffit pas toujours pour des bibliothèques tierces qui mettent en cache une valeur de configuration à l'import plutôt que de la relire dynamiquement. Vérifier le code source de la bibliothèque avant de supposer que le mécanisme standard de Django s'applique.

## `pg_dump` sans `--clean` produisait des sauvegardes impossibles à restaurer telles quelles

**Symptôme** : en testant réellement le cycle sauvegarde → restauration (`backup/sauvegarder.sh` puis `backup/restaurer.sh`), la restauration échouait avec des dizaines d'erreurs `relation "..." already exists` / `duplicate key value`.

**Cause** : `pg_dump` sans option produit un script qui *crée* les tables — il suppose une base cible vide. Restaurer ce dump sur une base déjà peuplée (le cas réaliste d'un test de restauration, ou d'une restauration partielle) échoue immédiatement.

**Correction** : ajout de `--clean --if-exists` à `pg_dump` dans `backup/sauvegarder.sh` — le dump inclut alors les `DROP ... IF EXISTS` nécessaires pour pouvoir être rejoué sur une base déjà peuplée sans erreur. Revérifié : cycle complet sauvegarde → restauration sans aucune erreur après correction.

**Enseignement** : une sauvegarde qui n'a jamais été restaurée n'est pas vérifiée. Le test de restauration (pas seulement de sauvegarde) a immédiatement révélé un problème qu'une simple vérification "le fichier .sql.gz existe" aurait manqué.

## Port 8000 déjà occupé par un autre projet Docker sur la machine de développement

**Symptôme** : `curl http://127.0.0.1:8000/api/health/` renvoyait `{"detail":"Not Found"}` — une réponse JSON qui ressemblait à celle de l'API mais n'en était pas une.

**Cause** : un autre projet local (`finadmintech-backend`, un service FastAPI) republie aussi le port `8000` de son conteneur Docker vers l'hôte. `{"detail":"Not Found"}` est le format 404 par défaut de FastAPI — quasiment identique à celui de DRF, d'où la confusion initiale.

**Correction** : backend de ce projet déplacé sur le port `8001` (`.env`, `.env.example`, `frontend/.env`, `docker-compose.prod.yml`). De même, PostgreSQL de dev a été mis sur le port hôte `5433` dès le départ pour éviter un conflit avec un autre projet déjà sur `5432`.

**Enseignement** : sur une machine de développement partagée entre plusieurs projets, ne jamais supposer qu'un port standard (8000, 5432...) est libre — vérifier `docker ps` avant de fixer un port dans la configuration.
