# Besoins non fonctionnels

État réel au 2026-09-22 : ce qui est fait, vérifié, et ce qui reste à valider ou à cadrer. Pas de chiffres inventés (temps de réponse, charge supportée…) — rien de ce type n'a été mesuré.

## Sécurité

- **Authentification** : par session Django (cookie), mot de passe changé obligatoirement à la première connexion pour tout compte créé par RH.
- **Anti-bruteforce** : limitation de débit sur `/api/auth/connexion/` (`ScopedRateThrottle`, taux configurable, voir `THROTTLE_CONNEXION`). Testé (`accounts/tests.py::ThrottlingConnexionTests`).
- **Autorisations** : vérifiées côté serveur à chaque endpoint (jamais seulement côté frontend) — un agent ne voit que ses propres demandes ou celles où il est validateur (`conges/permissions.py::est_implique`) ; l'administration RH est réservée à `is_staff`.
- **Fichiers sensibles** (justificatifs médicaux, attestations) : servis exclusivement via des vues authentifiées avec contrôle d'accès, jamais en statique public.
- **CSRF/CORS** : protection CSRF Django active, origines autorisées restreintes par configuration (`CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`).
- **En production** (`DEBUG=False`) : redirection HTTPS forcée, cookies `Secure`, HSTS, refus de démarrer si `DJANGO_SECRET_KEY` a la valeur par défaut de développement.
- **Authenticité des attestations** : HMAC-SHA256 côté serveur, clé jamais exposée par l'API — voir docs/03.
- **Non fait / à cadrer** : pas d'audit de sécurité externe, pas de politique de rotation des secrets, pas de 2FA, pas de journal d'audit centralisé au-delà de l'historique des `EtapeValidation` (qui, quand, quelle décision — mais pas un log générique de toutes les actions).

## Confidentialité des données

L'application manipule des données médicales (rapports médicaux, certificats de grossesse) — traitées avec le même niveau de contrôle d'accès que le reste des justificatifs (voir ci-dessus). Aucune anonymisation ni politique de rétention/suppression n'est définie à ce stade — à cadrer avec le client métier (durée de conservation légale des dossiers RH en Guinée, notamment).

## Disponibilité et hébergement

- Aucune cible d'hébergement n'est fixée (Guinée, aucun fournisseur cloud choisi). `docker-compose.prod.yml` fournit une stack conteneurisée de démonstration, pas une infrastructure de production (pas de TLS/reverse proxy, pas de sauvegarde automatisée, pas de plan de reprise après sinistre).
- Aucun objectif de disponibilité (SLA) n'a été fixé par le client métier.

## Performance et volumétrie

Aucun test de charge n'a été effectué. L'architecture (PostgreSQL, requêtes indexées sur `agent`+`statut`, pas de pagination sur les listes) est dimensionnée pour un usage interne à un ministère (dizaines à quelques centaines d'utilisateurs simultanés vraisemblablement), pas vérifiée pour un volume plus grand. Pas de pagination sur `/api/demandes/` ni `/api/auth/agents/` — à ajouter si le nombre d'enregistrements devient important.

## Accessibilité

Aucun audit d'accessibilité (contraste, navigation clavier, lecteurs d'écran) n'a été réalisé. Le design system (voir docs/03) vise une lisibilité correcte (contrastes marqués, hiérarchie typographique) mais ça n'a pas été vérifié avec des outils dédiés (axe, Lighthouse) ni testé avec un lecteur d'écran réel.

## Internationalisation / contexte guinéen

- Interface en français.
- Fuseau horaire `Africa/Conakry` configuré côté backend.
- Devise (GNF) non utilisée pour l'instant — aucun montant financier dans le périmètre actuel de l'application.
- Calendrier des jours fériés guinéens non modélisé (voir docs/03, limite connue).

## Qualité / maintenabilité

- 16 tests backend (Django/DRF), 6 tests end-to-end (Playwright) contre les vrais serveurs de dev — couvrent le parcours critique complet, les permissions, le rejet, l'annulation, la gestion RH/organisation. Pas de couverture formelle mesurée (pas d'outil de coverage branché).
- CI définie (`.github/workflows/ci.yml`) mais pas encore exécutée sur GitHub Actions au moment de la rédaction — à vérifier au prochain push.
- TypeScript strict côté frontend (`tsc -b`), pas d'erreur de type à la date de rédaction.
