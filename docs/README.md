# Documentation du projet

Rapport construit progressivement, versionné avec le code. Chaque section est rédigée quand la phase correspondante du projet est réellement faite — pas avant, pour éviter le contenu fabriqué.

| # | Document | Statut | Contenu |
|---|---|---|---|
| 00 | [État des lieux — référence frappe/hrms](00-etat-des-lieux-reference-frappe-hrms.md) | ✅ Fait (2026-09-22) | Analyse du projet open source utilisé comme référence fonctionnelle : module congés, workflow d'approbation, authentification, limites identifiées, ce qui est réutilisable comme idée vs. ce qui doit être reconçu. |
| 01 | Besoins fonctionnels | À rédiger | Cas d'usage détaillés par rôle (agent, chef de service, directeur, chef de cabinet), règles de gestion par type de congé, spécification de l'attestation. |
| 02 | Besoins non fonctionnels | À rédiger | Performance, disponibilité, sécurité des données personnelles/médicales, accessibilité, volumétrie attendue, contraintes d'hébergement (Guinée). |
| 03 | [Architecture](03-architecture.md) | ✅ Fait (2026-09-22) | Backend Django/DRF, frontend React, PostgreSQL, modèle de workflow, attestation/vérification, tests, ce qui manque encore. |
| 04 | [Diagrammes UML](04-diagrammes-uml.md) | ✅ Fait (2026-09-22) | Cas d'utilisation, classes, séquence (parcours critique), états (`DemandeConge`, `EtapeValidation`) — en Mermaid. |
| 05 | État de l'art | À rédiger | Comparaison avec d'autres solutions de gestion des congés (dont frappe/hrms), justification des choix techniques. |
| 06 | Problèmes rencontrés et solutions | À rédiger | Journal de bord technique, tenu au fil du développement. |
| 07 | Perspectives | À rédiger | Évolutions possibles après la version initiale. |

## Règles de rédaction

- Un document n'est créé/complété que lorsque le travail qu'il décrit a réellement été fait (voir [CLAUDE.md](../CLAUDE.md), section « Ce qu'il ne faut pas faire »).
- Français, terminologie de l'administration guinéenne.
- Toute référence à `frappe/hrms` renvoie au document 00, qui reste la seule source d'analyse de ce dépôt externe.
