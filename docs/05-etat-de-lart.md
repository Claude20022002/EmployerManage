# État de l'art

Ce document compare les approches possibles pour une application de gestion des congés et justifie les choix faits pour ce projet. Il s'appuie sur l'analyse réelle de `frappe/hrms` faite pour ce projet ([00-etat-des-lieux-reference-frappe-hrms.md](00-etat-des-lieux-reference-frappe-hrms.md)) — la seule solution concrète qui ait été inspectée en détail. Il ne prétend pas comparer chiffre à chiffre d'autres produits du marché (Odoo HR, BambooHR, Workday, etc.) qui n'ont pas été installés ni testés dans le cadre de ce projet ; les mentionner sans les avoir vérifiés serait fabriquer du contenu, ce que les règles du projet interdisent.

## Deux familles d'approches

### 1. Plateforme HR/RH généraliste bas-code (ex. Frappe HRMS, Odoo)

Avantages généraux (bien établis, indépendamment du produit précis) : très large couverture fonctionnelle out-of-the-box (paie, recrutement, évaluations…), rapide à déployer pour un besoin standard, communauté et documentation existantes.

Limites constatées concrètement sur frappe/hrms pour *ce* besoin précis : approbation à un seul niveau par défaut (pas de circuit à 3 niveaux prêt à l'emploi), aucune notion d'attestation authentifiable, stack imposée (Frappe Framework, Vue, MariaDB) différente de celle demandée par le client (Django, React, PostgreSQL). Adopter cette famille aurait donc demandé soit d'abandonner la stack demandée, soit de développer par-dessus une plateforme dont on n'utiliserait finalement qu'une fraction des fonctionnalités (paie, recrutement… hors périmètre ici).

### 2. Application métier sur mesure (Django + React + PostgreSQL) — approche retenue

Avantages pour ce projet précis : correspond exactement à la stack demandée par le client ; le circuit de validation à 3 niveaux dynamique (agent/chef de service/directeur/chef de cabinet selon le rôle du demandeur) et le mécanisme d'authenticité d'attestation (HMAC + QR code) sont des besoins spécifiques qui n'existaient dans aucune plateforme généraliste inspectée — les construire sur mesure évite de contourner les limites d'un framework bas-code.

Inconvénient assumé : tout ce qu'une plateforme généraliste offre gratuitement (paie, recrutement, tableaux de bord RH avancés…) devrait être développé si le périmètre s'élargit un jour — voir [07-perspectives.md](07-perspectives.md).

## Pourquoi Django + DRF plutôt qu'un autre framework Python

Choix imposé par le cahier des charges initial, pas un arbitrage technique fait pendant le projet. Django REST Framework a été retenu comme couche API pour sa maturité, son système de permissions extensible (utilisé massivement dans ce projet — `IsAuthenticated`, `IsAdminUser`, permissions d'objet ad hoc) et son intégration native avec l'authentification par session.

## Pourquoi une architecture SPA React + API REST plutôt qu'un rendu serveur

Découplage complet frontend/backend demandé par le client (React explicitement spécifié). Ce choix a un coût concret rencontré pendant le développement : la gestion CSRF entre deux origines différentes (frontend:5173, backend:8001) a provoqué un bug réel (voir [06-problemes-solutions.md](06-problemes-solutions.md)) qu'une architecture monolithique (Django + templates server-side) n'aurait pas eu à gérer. Assumé comme contrepartie du découplage demandé.

## Pourquoi un grand livre de mouvements n'a pas été repris de frappe/hrms

frappe/hrms modélise le solde de congés comme un grand livre append-only (`Leave Ledger Entry`) plutôt qu'un compteur mutable — bonne pratique généralement reconnue pour la traçabilité. Ce projet ne suit cependant **aucun solde de congés** (non demandé dans le cahier des charges initial : les durées sont fixes ou bornées par type, pas décomptées d'un capital annuel). Le principe du grand livre a néanmoins été repris ailleurs, dans la modélisation du circuit de validation : chaque `EtapeValidation` est un enregistrement immuable une fois décidé (date, décision, commentaire), plutôt qu'un unique champ statut réécrit — pour les mêmes raisons de traçabilité et d'auditabilité, pertinentes pour une attestation officielle.

## Mécanisme d'authenticité de l'attestation

Deux approches courantes existent pour authentifier un document officiel : signature numérique (PKI, certificat) ou vérification par consultation d'une source de vérité centrale (numéro de dossier + secret côté serveur). La première demande une infrastructure de clés et un tiers de confiance (autorité de certification) hors de portée du périmètre actuel ; la seconde (retenue ici — HMAC-SHA256 + endpoint de vérification publique) est plus simple à opérer pour un premier déploiement, au prix de dépendre de la disponibilité du serveur pour toute vérification (pas de vérification hors-ligne possible). Assumé comme choix de premier déploiement, à revisiter si une vérification hors-ligne devient un besoin exprimé.
