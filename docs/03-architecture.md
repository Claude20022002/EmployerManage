# Architecture

État au 2026-09-22, après implémentation de l'API, de l'attestation, des écrans React et de l'écran d'administration des comptes. Décrit ce qui existe réellement dans le dépôt, pas une cible théorique.

## Vue d'ensemble

```
┌──────────────────┐      HTTP (session + CSRF)      ┌───────────────────┐      SQL       ┌────────────┐
│  React (Vite)     │ ───────────────────────────────▶│  Django + DRF      │ ─────────────▶│ PostgreSQL │
│  localhost:5173    │◀─────────────────────────────── │  localhost:8001    │◀───────────────│            │
└──────────────────┘         JSON / fichiers           └───────────────────┘                └────────────┘
```

- **Backend** : `backend/` — projet Django (`config/`) + deux apps : `accounts` (identité, hiérarchie, administration RH) et `conges` (le métier congés). API REST exposée par Django REST Framework.
- **Frontend** : `frontend/` — SPA React 19 + TypeScript, routée par `react-router-dom`, bundlée par Vite.
- **Base de données** : PostgreSQL 16, via Docker (`docker-compose.yml` à la racine, port hôte **5433** pour éviter un conflit avec un autre projet local qui occupe le 5432).
- Le port backend est **8001** (et non 8000, occupé par un autre projet Docker sur cette machine) — voir `backend/.env`.

## Backend

### Découpage en apps

- **`accounts`** : `User` (étend `AbstractUser` avec `matricule`, `role_hierarchique`, `service`, `must_change_password`), `Direction`, `Service`. Vues d'authentification par session (`/api/auth/connexion/`, `/deconnexion/`, `/moi/`, `/changer-mot-de-passe/`) et d'administration RH (`/api/auth/agents/`, `/api/auth/services/`, réservées à `is_staff`).
- **`conges`** : tout le métier congés — `TypeConge`, `TypeJustificatif`, `DemandeConge`, `EtapeValidation`, `JustificatifDemande`, `Attestation`, plus la logique de workflow dans `conges/services.py` et la génération d'attestation dans `conges/attestation.py`.

### Pourquoi une app `accounts` séparée de `conges`

`Direction`/`Service`/`User` décrivent l'organisation du ministère, indépendamment des congés (ils serviraient à d'autres modules RH futurs). `conges` ne fait que consommer cette structure pour router les demandes — voir `conges/services.py::construire_circuit_validation`.

### Authentification et sécurité des requêtes

- Authentification par **session Django** (cookie), pas de JWT — plus simple à sécuriser pour une app interne avec un seul frontend de confiance, et bénéficie nativement du système de permissions Django.
- Connexion par **matricule** (pas par `username` Django au sens strict, même si `username` est techniquement le champ utilisé par le backend d'authentification — `accounts/views.py::connexion` fait la traduction matricule → username).
- **CSRF** : le frontend et l'API tournent sur deux ports différents (5173 / 8001), donc deux origines distinctes du point de vue du navigateur. `axios` n'envoie pas l'en-tête CSRF cross-origin par défaut depuis la 1.6 (voir GHSA-wf5p-g6vw-rhxx) — corrigé avec `withXSRFToken: true` dans `frontend/src/api/client.ts`. C'est un bug réel trouvé par le test Playwright du parcours critique, pas une anticipation théorique.
- Permissions par endpoint (DRF `permission_classes`), pas de rôle générique "admin" : `IsAuthenticated` par défaut, `IsAdminUser` (`is_staff`) pour l'administration RH, vérifications d'objet ad hoc (`conges/permissions.py::est_implique`) pour qu'un agent ne voie que ses propres demandes ou celles où il est validateur.

### Modèle du workflow de validation

Le point le plus important de l'architecture métier : **le circuit d'approbation n'est pas un champ statut unique, c'est une séquence d'objets `EtapeValidation`** générée dynamiquement à la soumission (`conges/services.py::construire_circuit_validation`), selon le rôle hiérarchique du demandeur :

| Rôle du demandeur | Étapes générées |
|---|---|
| Agent | Chef de service → Directeur → Chef de cabinet |
| Chef de service | Directeur → Chef de cabinet |
| Directeur | Chef de cabinet |
| Chef de cabinet | non couvert (erreur explicite — cas non spécifié par le cahier des charges) |

À tout instant, l'« étape courante » est la première `EtapeValidation` non tranchée (`etape_courante()`), et seul son validateur assigné peut agir (`approuver_etape()` / `rejeter_etape()`). Un rejet à n'importe quel niveau interrompt immédiatement le circuit (`DemandeConge.statut = REJETEE`) sans annuler les étapes suivantes (elles restent simplement inatteignables).

### Attestation et vérification d'authenticité

Voir `conges/attestation.py`. Trois éléments, générés uniquement quand la dernière étape est approuvée :

1. **`numero_serie`** (UUID) — identifiant public de l'attestation.
2. **`hash_verification`** — HMAC-SHA256 (clé serveur `ATTESTATION_SECRET_KEY`, jamais exposée par l'API) sur un message canonique (numéro de série + matricule + type de congé + dates). Stocké en base, jamais renvoyé en entier par l'API (`AttestationSerializer` ne l'expose pas).
3. **PDF** (reportlab) avec un QR code pointant vers `{FRONTEND_URL}/verification/{numero_serie}?code={12 premiers caractères du hash}`.

L'endpoint public `GET /api/verification/{numero_serie}/?code=...` (accessible sans authentification) ne révèle les informations de la demande que si le fragment fourni correspond au hash recalculé côté serveur — empêche de deviner un numéro de série valide par énumération, sans nécessiter d'infrastructure de signature numérique (PKI) externe.

### Paramétrage métier (pas de règles codées en dur)

`TypeConge` porte `duree_min_jours`/`duree_max_jours`/`jours_ouvrables_uniquement`, et `TypeCongeJustificatifRequis` relie chaque type à ses justificatifs obligatoires. Modifiable sans déploiement de code (admin Django). Données actuelles (`conges/management/commands/seed_demo.py`), y compris la distinction maladie courte/longue durée confirmée avec l'utilisateur le 2026-09-22 :

| Type | Durée | Justificatifs |
|---|---|---|
| Congé normal | 30 jours ouvrables (fixe) | — |
| Congé de maternité | 90 jours (fixe) | Certificat de grossesse |
| Congé de maladie (courte durée) | 1 à 90 jours | Bulletin de paie, rapport médical |
| Congé de maladie (longue durée) | 91 jours et plus | Bulletin de paie, rapport médical, **avis du conseil de santé** |
| Congé de formation | 90 jours et plus | Arrêté d'engagement, acte d'affectation, copie de l'attestation du BAC |
| Congé exceptionnel | 1 à 10 jours | — |

### Limite connue : calcul des jours ouvrables

`conges/services.py::nombre_jours` exclut uniquement les week-ends, pas les jours fériés guinéens — aucun calendrier de jours fériés n'est modélisé. À faire si le cadrage métier l'exige.

### Fichiers sensibles (justificatifs, attestations)

Servis en développement via `django.conf.urls.static` (aucun contrôle d'accès), documenté comme écart de sécurité à ne pas déployer tel quel dans `CLAUDE.md`. En production, il faudrait une vue authentifiée qui réutilise `est_implique()` avant de streamer le fichier.

## Frontend

### Structure (`frontend/src/`)

```
api/            client axios (gestion CSRF), fonctions par domaine (auth, conges, administration)
context/        AuthContext — utilisateur courant, connexion/déconnexion, chargement initial
components/     Layout (bandeau + nav conditionnelle par rôle), ProtectedRoute, StatutBadge, EtapesTimeline
pages/          un composant par écran (voir routes ci-dessous)
types.ts        types TypeScript alignés sur les serializers DRF
```

### Routage (`App.tsx`)

| Route | Accès | Écran |
|---|---|---|
| `/connexion` | public | Connexion par matricule |
| `/verification/:numeroSerie` | public | Vérification d'attestation |
| `/changer-mot-de-passe` | authentifié | Changement de mot de passe (forcé si `must_change_password`) |
| `/nouvelle-demande` | authentifié | Création + soumission d'une demande |
| `/mes-demandes` | authentifié | Historique personnel |
| `/a-valider` | authentifié, non-agent | Inbox de validation |
| `/demandes/:id` | authentifié + impliqué | Détail, décision, attestation |
| `/administration/agents` | authentifié + `is_staff` | Création de comptes agents (RH) |

`ProtectedRoute` gère l'authentification générale ; l'accès `is_staff` à `/administration/agents` est vérifié dans la page elle-même (un seul écran concerné pour l'instant, pas de garde générique créée pour éviter la sur-ingénierie).

### Design

Système de design propre (`index.css` + `App.css`), pas de librairie de composants tierce. Palette institutionnelle sobre avec un bandeau reprenant les trois couleurs du drapeau guinéen en filet discret, typographie sérif pour les titres (registre officiel) / sans-serif pour l'interface. Décision volontaire pour éviter l'esthétique générique (gradients violets, ombres par défaut) que produisent souvent les outils de génération d'UI — objectif explicitement demandé par l'utilisateur (skills `taste-skill`/`impeccable`/`ui-ux-pro-max` installés mais pas encore exécutés via leurs commandes dédiées, voir docs/06 à venir).

## Tests

- **Backend** (`backend/*/tests.py`, `test_api.py`) : 11 tests Django/DRF — construction du circuit de validation (agent/chef de service/directeur, erreurs si hiérarchie mal configurée), parcours API complet (soumission → 3 approbations → attestation → vérification publique), rejet qui interrompt le circuit, création de compte RH, contrôle d'accès.
- **End-to-end** (`frontend/e2e/`) : 4 tests Playwright contre les serveurs de développement réels (pas de mocks) — parcours critique complet dans un vrai navigateur, blocage de soumission sans justificatif, écran RH. Ont déjà trouvé un bug réel (CSRF cross-origin) avant qu'il n'atteigne la production.

## Configuration / environnements

Variables d'environnement (`.env`, jamais commité — voir `.env.example` dans `backend/` et `frontend/`) : `DATABASE_URL`, `DJANGO_SECRET_KEY`, `ATTESTATION_SECRET_KEY`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `FRONTEND_URL`, `VITE_API_URL`. Aucun profil de configuration production n'existe encore (`DEBUG=True` par défaut, clés par défaut non sécurisées) — voir docs/02 (besoins non fonctionnels, à rédiger) pour le cadrage du déploiement.

## Ce qui n'existe pas encore

Pour ne pas laisser croire que l'architecture est complète : pas de conteneurisation du backend/frontend eux-mêmes (seul PostgreSQL est dockerisé), pas de CI, pas d'annulation de demande par l'agent, pas d'envoi d'email/notification, pas de gestion des directions/services depuis l'interface (admin Django uniquement), pas de calendrier des jours fériés.
