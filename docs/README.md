# Documentation du projet

Rapport construit progressivement, versionné avec le code. Chaque section est rédigée quand la phase correspondante du projet est réellement faite — pas avant, pour éviter le contenu fabriqué.

| # | Document | Statut | Contenu |
|---|---|---|---|
| 00 | [État des lieux — référence frappe/hrms](00-etat-des-lieux-reference-frappe-hrms.md) | ✅ Fait (2026-09-22) | Analyse du projet open source utilisé comme référence fonctionnelle : module congés, workflow d'approbation, authentification, limites identifiées, ce qui est réutilisable comme idée vs. ce qui doit être reconçu. |
| 01 | [Besoins fonctionnels](01-besoins-fonctionnels.md) | ✅ Fait (2026-09-22) | Cas d'usage détaillés par rôle (agent, chef de service, directeur, chef de cabinet, RH), règles de gestion par type de congé, spécification de l'attestation. |
| 02 | [Besoins non fonctionnels](02-besoins-non-fonctionnels.md) | ✅ Fait (2026-09-22) | Sécurité, confidentialité, disponibilité, performance, accessibilité, contexte guinéen — ce qui est fait vs. ce qui reste à valider. |
| 03 | [Architecture](03-architecture.md) | ✅ Fait (2026-09-22) | Backend Django/DRF, frontend React, PostgreSQL, modèle de workflow, attestation/vérification, tests, durcissement production, ce qui manque encore. |
| 04 | [Diagrammes UML](04-diagrammes-uml.md) | ✅ Fait (2026-09-22) | Cas d'utilisation, classes, séquence (parcours critique), états (`DemandeConge`, `EtapeValidation`) — en Mermaid. |
| 05 | [État de l'art](05-etat-de-lart.md) | ✅ Fait (2026-09-22) | Comparaison plateforme généraliste (frappe/hrms) vs. sur mesure, justification des choix techniques. |
| 06 | [Problèmes rencontrés et solutions](06-problemes-solutions.md) | ✅ Fait (2026-09-22) | Journal de bord technique — 4 incidents réels documentés (CSRF, Docker, throttle de test, conflit de port). |
| 07 | [Perspectives](07-perspectives.md) | ✅ Fait (2026-09-22) | Évolutions possibles, classées entre complément du périmètre actuel et extensions à confirmer. |

## Règles de rédaction

- Un document n'est créé/complété que lorsque le travail qu'il décrit a réellement été fait (voir [CLAUDE.md](../CLAUDE.md), section « Ce qu'il ne faut pas faire »).
- Français, terminologie de l'administration guinéenne.
- Toute référence à `frappe/hrms` renvoie au document 00, qui reste la seule source d'analyse de ce dépôt externe.
