# Besoins fonctionnels

Reflète le périmètre réellement implémenté au 2026-09-22 (voir [03-architecture.md](03-architecture.md) et [04-diagrammes-uml.md](04-diagrammes-uml.md) pour le comment). Les règles ci-dessous viennent soit du cahier des charges initial, soit de clarifications explicitement demandées et obtenues auprès de l'utilisateur au fil du développement — aucune n'est inventée.

## Acteurs

| Rôle | Peut |
|---|---|
| Agent | Soumettre une demande de congé, joindre des justificatifs, suivre ses demandes, l'annuler avant décision finale, télécharger son attestation. Peut aussi être demandeur s'il est chef de service ou directeur (voir circuit). |
| Chef de service | Tout ce que peut un agent, + valider/rejeter les demandes où il est l'étape courante. |
| Directeur | Idem, + peut accorder une durée différente de celle demandée au moment de sa décision. |
| Chef de cabinet | Idem, dernier niveau du circuit. |
| Personnel RH (`is_staff`) | Créer des comptes agents, consulter la liste des agents, gérer les directions et services (création, assignation d'un directeur/chef de service). N'intervient pas dans le circuit de validation des congés sauf s'il a par ailleurs un rôle hiérarchique. |
| Tiers (public) | Vérifier l'authenticité d'une attestation via son numéro de série + code, sans authentification. |

## Cas d'usage détaillés

### Soumettre une demande de congé

1. L'agent s'identifie (matricule + mot de passe).
2. Il choisit un type de congé (voir tableau ci-dessous) ; l'écran affiche la durée attendue et les justificatifs requis pour ce type.
3. Il saisit dates de début/fin (et un motif libre pour le congé exceptionnel).
4. Il joint les justificatifs requis (upload de fichier par type de justificatif).
5. Il soumet : le serveur revalide la durée (bornes du type de congé) et la présence de tous les justificatifs requis avant d'accepter la soumission — jamais sur la seule confiance du frontend.
6. À la soumission, le circuit de validation est calculé selon le rôle hiérarchique du demandeur (voir docs/04, diagramme de séquence) et la demande passe en statut « en cours ».

### Types de congés et règles associées

| Type | Durée | Justificatifs requis |
|---|---|---|
| Normal | 30 jours ouvrables (fixe) | Aucun |
| Maternité | 90 jours (fixe) | Certificat de grossesse |
| Maladie (courte durée) | 1 à 90 jours | Bulletin de paie, rapport médical |
| Maladie (longue durée) | 91 jours et plus | Bulletin de paie, rapport médical, avis du conseil de santé |
| Formation | 90 jours et plus (3/6/9 mois+, non plafonné) | Arrêté d'engagement, acte d'affectation, copie de l'attestation du BAC |
| Exceptionnel | 1 à 10 jours | Aucun |

Le seuil courte/longue durée (3 mois) et le justificatif « avis du conseil de santé » ont été confirmés avec l'utilisateur le 2026-09-22 (voir historique de conversation, pas de source réglementaire externe citée). Tout autre seuil légal non couvert ici (ex. barème précis du Code du travail guinéen) reste à confirmer avant implémentation, conformément à la règle du projet de ne jamais deviner une règle légale.

Le paramétrage est en base (`TypeConge`, `TypeJustificatif`), modifiable sans déploiement — voir admin Django.

### Circuit de validation hiérarchique

- Agent → chef de service → directeur → chef de cabinet.
- Chef de service demandeur → directeur → chef de cabinet (saute sa propre étape).
- Directeur demandeur → chef de cabinet uniquement.
- Chef de cabinet demandeur : cas non couvert, erreur explicite (à spécifier si besoin).
- Un rejet à n'importe quelle étape arrête immédiatement le circuit ; les étapes suivantes ne sont plus atteignables.
- Le directeur peut, au moment de sa décision, accorder une durée différente de celle demandée (`duree_accordee_jours`) ; l'attestation finale reflète la durée réellement accordée.
- Chaque décision (approbation/rejet) est horodatée et peut porter un commentaire ; le rejet exige un commentaire.

### Annulation

L'agent peut annuler sa propre demande tant qu'elle est en brouillon ou en cours de validation (pas après décision finale — approuvée ou rejetée).

### Attestation

- Générée automatiquement à l'approbation de la dernière étape.
- Contient : nom/prénom/matricule de l'agent, type de congé, période validée, numéro de série, QR code de vérification.
- Téléchargeable en PDF par l'agent et par toute personne impliquée dans le circuit (validateurs), via une vue authentifiée — jamais un lien de fichier public brut.
- Vérifiable publiquement (sans authentification) via numéro de série + code, sans exposer d'information si le code est incorrect (pas d'énumération possible).

### Création de compte agent (RH)

Le personnel RH crée un compte avec matricule, nom, prénom, email, rôle hiérarchique et service de rattachement. Un mot de passe temporaire est généré côté serveur et affiché une seule fois à l'écran (jamais par email — pas d'infrastructure d'envoi d'email dans ce projet pour l'instant). L'agent doit le changer à sa première connexion.

### Gestion de l'organisation (RH)

Création de directions (avec directeur assignable) et de services rattachés à une direction (avec chef de service assignable) — nécessaire pour que le circuit de validation puisse router les demandes correctement.

## Hors périmètre actuel (volontairement)

- Notification par email/SMS des changements de statut.
- Historique des soldes de congés / droits acquis (le projet ne suit pas de solde, contrairement à frappe/hrms — non demandé dans le cahier des charges initial).
- Calendrier des jours fériés guinéens dans le calcul des jours ouvrables.
- Suppression de directions/services (seulement création et modification).
