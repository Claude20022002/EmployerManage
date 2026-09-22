# État des lieux — `frappe/hrms` comme référence fonctionnelle

Analyse effectuée le 2026-09-22 sur le dépôt cloné localement dans `../hrms` (commit `develop` au moment de l'analyse : `33cb1d124`). Ce document ne décrit **que** l'existant du projet open source ; il ne préjuge pas des choix faits pour ce projet-ci (voir [CLAUDE.md](../CLAUDE.md) pour les décisions actées).

## 1. Pourquoi ce n'est pas une base de code réutilisable

`frappe/hrms` est un module métier construit sur le **Frappe Framework**, pas sur Django :

| Couche | frappe/hrms | Ce projet |
|---|---|---|
| Backend | Frappe Framework (Python, ORM et routing propriétaires, "DocTypes" JSON + contrôleurs Python) | Django + DRF |
| Frontend | Vue 3 + Ionic Vue + `frappe-ui`, bundlé Vite | React |
| Base de données | MariaDB 10.8 | PostgreSQL |

Décision actée avec l'utilisateur : réécriture complète. `frappe/hrms` sert de **référence fonctionnelle et UX uniquement** — jamais de code à copier (voir CLAUDE.md).

## 2. Module congés existant — ce qu'il fait

Dépôt : DocTypes sous `hrms/hr/doctype/` (chemins relatifs à `../hrms`).

### 2.1 Objets métier identifiés

| Concept | Équivalent probable côté Django (à concevoir) |
|---|---|
| `Leave Application` | Modèle `DemandeConge` — la demande elle-même |
| `Leave Type` | Modèle `TypeConge` (paramétrage : maternité, maladie, formation, normal, exceptionnel) |
| `Leave Allocation` | Solde alloué à un agent pour une période |
| `Leave Policy` / `Leave Policy Assignment` | Règles d'attribution automatique de solde (probablement hors périmètre v1 si les soldes sont saisis manuellement) |
| `Leave Ledger Entry` | Grand livre des mouvements de solde (source de vérité pour le calcul du solde restant) |
| `Leave Period` | Période de référence (ex. année civile) |
| `Leave Block List` | Périodes où la prise de congé est bloquée (ex. clôture budgétaire) |
| `Department Approver` | Table des approbateurs par service |

### 2.2 Circuit d'approbation — analyse détaillée

**Constat clé : approbation à un seul niveau par défaut.**

- Chaque agent a un champ `leave_approver` (un seul utilisateur désigné), avec repli sur le premier approbateur déclaré pour son département (`Department Approver`).
- L'état de la demande est un simple champ `status` (`Open` / `Approved` / `Rejected` / `Cancelled`), modifiable uniquement par l'approbateur (contrôle d'accès par rôle + `permlevel`), sans notion de chaîne d'approbation séquentielle.
- Un moteur de workflow générique existe dans Frappe Framework (le "Workflow" doctype) mais **n'est pas configuré par défaut** pour les congés — l'approbation à plusieurs niveaux n'est possible qu'en le configurant manuellement, ce qui n'est pas fourni « prêt à l'emploi ».
- Notification par email à chaque changement d'état, via un template configurable.

**Conséquence pour ce projet** : le circuit à 3 niveaux (chef de service → directeur → chef de cabinet), avec possibilité pour le directeur de valider « pour une durée donnée » différente de la demande initiale, n'a pas d'équivalent tout fait à copier. Il faut le concevoir dès la modélisation des données (ex. table `EtapeValidation` liée à `DemandeConge`, avec ordre, rôle attendu, décision, date, commentaire, durée validée).

### 2.3 Calcul de solde

Le solde n'est jamais recalculé « à la volée » à partir de zéro : chaque mouvement (allocation, demande approuvée, ajustement manuel, rachat de congé) est journalisé dans un grand livre append-only, et le solde est la somme des mouvements. Ce principe (grand livre plutôt que compteur mutable) est une bonne pratique directement réutilisable pour la fiabilité et la traçabilité — recommandé pour la conception du modèle Django.

### 2.4 Attestation de congé

Aucune attestation de congé n'existe dans `frappe/hrms` (seulement des modèles d'impression pour l'offre d'emploi et la lettre de nomination). Aucun mécanisme d'authenticité (QR code, signature, hash de vérification) n'est présent nulle part dans le dépôt. **Ce sont des éléments à concevoir intégralement pour ce projet.**

### 2.5 Authentification et matricule

- Séparation classique entre l'identité de connexion (`User`, email + mot de passe) et la fiche métier (`Employee`), reliées 1:1.
- Un mécanisme de matricule existe (paramètre « Employee Number » comme méthode de nommage) — confirme que matricule + email + nom/prénom comme identifiants d'un agent est un schéma standard et robuste pour ce type d'application.

### 2.6 Localisation

- Traduction française déjà quasi complète en amont (`hrms/locale/fr.po`, ~98 % traduit) — signe que le projet amont est déjà largement utilisé dans des contextes francophones, bon indicateur de couverture fonctionnelle pour un usage en Guinée.
- Aucune logique régionale codée en dur ne concerne les congés (seule la paie/fiscalité indienne a du code spécifique pays) — rien ne bloque une adaptation à un contexte ouest-africain francophone au niveau du domaine « congés ».
- La devise n'est jamais codée en dur ; elle est toujours une référence vers un paramétrage — confirme qu'ajouter le Franc guinéen (GNF) est une question de configuration, pas de code.

## 3. Enseignements à retenir pour la conception

1. **Modéliser le workflow comme une séquence d'étapes explicites**, pas comme un simple champ statut — c'est le point sur lequel frappe/hrms est le plus faible par rapport au besoin exprimé.
2. **Utiliser un grand livre de mouvements** pour le solde de congés plutôt qu'un compteur mutable, pour la traçabilité et l'auditabilité.
3. **Paramétrer les types de congés et leurs justificatifs requis** dans une table de configuration, pas en dur dans le code (le besoin a 5 types avec des règles de durée et de justificatifs différentes, et cela évoluera probablement).
4. **Concevoir l'authenticité de l'attestation dès le départ** : aucun équivalent à copier, c'est un vrai sujet de conception (signature numérique du PDF, ou QR code + endpoint de vérification publique par numéro de dossier).
5. Le référentiel matricule + email + nom/prénom comme identité d'un agent est un schéma éprouvé, à reprendre.
