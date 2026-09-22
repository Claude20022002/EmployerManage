# CLAUDE.md

Règles de travail pour ce dépôt. Lis ce fichier avant toute tâche de développement.

## Projet

Application de gestion des congés du **Ministère de l'Économie, des Finances et du Budget** (République de Guinée). Permet à un agent de faire une demande de congé en ligne, de la faire suivre un circuit de validation hiérarchique, et de produire une attestation authentifiable en fin de processus.

## Stack technique imposée

- **Backend** : Django + Django REST Framework
- **Frontend** : React
- **Base de données** : PostgreSQL
- **Tests** : pytest / pytest-django côté backend, Playwright pour les tests end-to-end (voir plugin `playwright` installé dans cette session Claude Code)

Ne pas introduire d'autre framework backend ou frontend sans validation explicite de l'utilisateur.

## Rôle du dépôt `frappe/hrms` (référence, pas du code à réutiliser)

Le projet part d'une analyse du dépôt open source [frappe/hrms](https://github.com/frappe/hrms), cloné localement en dehors de ce dépôt (`../hrms`). Décision actée avec l'utilisateur (2026-09-22) : **réécriture complète en Django/React/PostgreSQL** — frappe/hrms sert uniquement de **référence fonctionnelle et UX**, jamais de source de code.

Règles :
- Ne jamais copier-coller du code Python/Vue depuis `../hrms` dans ce dépôt (licences GPL-3.0 différentes, stack incompatible : Frappe Framework ≠ Django, Vue ≠ React, MariaDB ≠ PostgreSQL).
- On peut s'en inspirer pour : la liste des champs d'un DocType, la logique métier (calcul de solde de congés, cycle de vie d'une demande), les libellés déjà traduits en français (`hrms/locale/fr.po`), les pièges déjà rencontrés par un projet mature.
- Voir [docs/00-etat-des-lieux-reference-frappe-hrms.md](docs/00-etat-des-lieux-reference-frappe-hrms.md) pour l'analyse détaillée déjà faite (modules congés, workflow d'approbation, authentification, limites identifiées).

## Règles métier (issues du cahier des charges)

### Types de congés
- **Maternité** : 3 mois
- **Maladie** : courte durée ou longue durée (deux régimes distincts à modéliser)
- **Formation** : durée variable (3, 6, 9 mois ou plus) — doit être paramétrable, pas codée en dur
- **Normal** : 30 jours ouvrables par an
- **Exceptionnel**

Chaque type de congé a ses propres règles de justificatifs et éventuellement de durée — modéliser via une table de paramétrage (type de congé → durée par défaut/plage, justificatifs requis), pas via `if/elif` en dur dans le code métier.

### Justificatifs par type de congé
- Congé de formation → arrêté d'engagement, acte d'affectation, copie de l'attestation du BAC
- Congé de maladie → bulletin de paie, rapport médical
- Congé de maternité → certificat de grossesse

Le upload de justificatifs doit être obligatoire et bloquant selon le type de congé sélectionné (validation côté back ET front).

### Circuit de validation (workflow hiérarchique)
1. L'agent s'identifie et remplit le formulaire de demande.
2. Le **chef de service** valide ou rejette.
3. Si validé → transmission au **directeur**, qui valide (pour une durée donnée, potentiellement différente de la demande initiale) ou rejette.
4. Si validé par le directeur → transmission au **chef de cabinet**, qui valide ou rejette.

Points d'attention issus de l'analyse de frappe/hrms : ce framework ne propose par défaut qu'une approbation à **un seul niveau** (`leave_approver`) — le circuit à 3 niveaux demandé ici doit être modélisé explicitement dès la conception (machine à états / statuts par étape, table d'historique des décisions, notification à chaque transition). Ne pas sous-estimer cette partie : c'est le cœur métier de l'application.

La demande de congé peut être initiée « à tous les niveaux, de l'agent au directeur » — donc un directeur ou chef de service peut lui-même être demandeur, et son propre circuit de validation remonte au niveau supérieur (ne pas coder une hiérarchie figée à un seul rôle "Agent").

### Attestation de congé
- Générée à l'issue d'une validation complète.
- Doit être **authentique et vérifiable** (aucun mécanisme de ce type n'existe dans frappe/hrms — à concevoir : ex. QR code renvoyant vers une page de vérification publique par numéro de dossier + hash, signature numérique du PDF, ou numéro de série + empreinte cryptographique stockée en base).
- Format PDF, générée côté backend (pas de génération PDF côté client à des fins d'intégrité).

### Authentification
- Champs d'inscription/compte : nom, prénom, **matricule**, email, mot de passe temporaire généré.
- L'agent doit pouvoir changer son mot de passe après la première connexion et le personnaliser.
- Le matricule est l'identifiant métier stable (distinct de l'email, qui peut changer) — prévoir un champ unique indexé.

## Adaptation au contexte guinéen

- Langue d'interface : **français** (langue officielle administrative en Guinée).
- Devise : **GNF (Franc guinéen)** partout où un montant est affiché (ex. indemnités liées à un congé, si applicable).
- Jours fériés / calendrier : utiliser le calendrier officiel guinéen, pas un calendrier générique — à faire valider par le client métier plutôt que supposé.
- Les durées légales de congé (30 jours ouvrables, 3 mois maternité, etc.) sont celles fournies par le cahier des charges ; toute règle légale non couverte explicitement par le cahier des charges (ex. détail du Code du travail guinéen ou du Statut général de la fonction publique) doit être **confirmée avec l'utilisateur avant implémentation**, jamais supposée.
- Numéros de téléphone, formats d'adresse, noms de services (chef de service, direction, cabinet) : utiliser la terminologie de l'administration guinéenne telle que fournie par l'utilisateur, ne pas généraliser avec du vocabulaire d'un autre pays.

## Conventions d'ingénierie

- Structure attendue : `backend/` (projet Django) et `frontend/` (application React) à la racine, une fois le scaffolding initial fait.
- Ne pas ajouter de fonctionnalité, d'abstraction ou de champ non demandé « au cas où » — le périmètre métier est déjà large (5 types de congés × 3 niveaux d'approbation), rester strict sur le scope de chaque tâche.
- Toute demande de congé passe par une validation serveur des règles métier (durée, justificatifs, chevauchement de dates) — ne jamais faire confiance à la seule validation frontend.
- Traçabilité : chaque changement de statut d'une demande de congé doit être journalisé (qui, quand, quel statut avant/après) — nécessaire pour la fiabilité de l'attestation et pour un audit administratif.
- Sécurité : application gouvernementale manipulant des données personnelles et médicales (rapports médicaux, certificats de grossesse) — traiter les fichiers uploadés et les champs médicaux avec le même niveau de rigueur que des données sensibles (contrôle d'accès strict par rôle, pas d'exposition dans des logs, stockage des fichiers hors webroot public).
  - Justificatifs et attestations sont servis via des vues authentifiées (`conges/views.py::fichier_justificatif`, `fichier_attestation`) qui vérifient `est_implique()` — jamais via un serveur de fichiers statique brut sur `MEDIA_ROOT`. Ne pas réintroduire `django.conf.urls.static` pour ces chemins.
  - En production, remplacer le `FileResponse` Django par un `X-Accel-Redirect`/`X-Sendfile` derrière le reverse proxy pour ne pas faire transiter les gros fichiers par le worker Python — non fait pour l'instant (volumétrie faible en l'état).

## Documentation

Le rapport complet du projet (besoins fonctionnels/non fonctionnels, architecture, diagrammes UML, état de l'art, problèmes/solutions, perspectives) est construit **progressivement** dans `docs/`, versionné avec le code, au fur et à mesure de l'avancement — pas généré en un bloc à l'avance. Voir [docs/README.md](docs/README.md) pour le sommaire et l'état d'avancement de chaque section.

## Outils disponibles pour ce projet (frontend)

- Skill `frontend-design` — guidance de design UI/UX pour les écrans React.
- Plugin `chrome-devtools-mcp` — debug/inspection navigateur.
- Plugin `playwright` — tests end-to-end automatisés (à utiliser pour valider le circuit de validation à 3 niveaux, qui est le parcours critique de l'application).
- Plugin `taste-skill` (Leonxlnx/taste-skill) — skills de style frontend (brutalist, minimalist, soft, redesign, image-to-code…) pour éviter un rendu générique.
- Plugin `impeccable` (pbakaus/impeccable) — détection d'anti-patterns "AI slop" et 24 commandes de polish design (`/impeccable polish`, `/impeccable audit`, `/impeccable critique`, etc.).
- Plugin `ui-ux-pro-max` (nextlevelbuilder/ui-ux-pro-max-skill) — bases de styles UI, palettes, typographies et guidelines UX consultables pendant le développement des écrans React.

Ces trois plugins sont des projets communautaires tiers (vérifiés le 2026-09-22 : licences MIT/Apache-2.0, code inspecté avant installation, pas de hook suspect), pas des skills officiels Anthropic. "Magic mcp" et "awesome design" restent introuvables comme plugins réels — ne pas tenter de les installer.

## Ce qu'il ne faut pas faire

- Ne pas modifier le dépôt `../hrms` (frappe/hrms) : il reste une référence externe en lecture seule.
- Ne pas commit/push sans demande explicite de l'utilisateur.
- Ne pas inventer de règles légales guinéennes (fiscalité, droit du travail) non fournies par l'utilisateur — poser la question plutôt que supposer.
- Ne pas fabriquer de contenu pour les sections du rapport (UML, état de l'art) avant que la conception correspondante existe réellement.
