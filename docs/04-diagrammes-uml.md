# Diagrammes UML

Diagrammes en Mermaid (rendus nativement par GitHub). Mis à jour le 2026-09-22 pour refléter l'annulation, le calendrier des jours fériés, les notifications et la gestion de l'organisation — la première version de ce document datait d'avant ces fonctionnalités et avait dérivé du code (le diagramme d'état `DemandeConge` affirmait à tort que l'annulation n'était pas atteignable). À maintenir à jour si le modèle change ; un diagramme qui ment est pire que pas de diagramme.

## Cas d'utilisation

```mermaid
flowchart LR
    Agent(["Agent"])
    ChefService(["Chef de service"])
    Directeur(["Directeur"])
    ChefCabinet(["Chef de cabinet"])
    RH(["Personnel RH (is_staff)"])
    Public(["Tiers (vérificateur externe)"])

    subgraph Demande de congé
        UC1["Soumettre une demande"]
        UC2["Joindre des justificatifs"]
        UC3["Consulter ses demandes"]
        UC4["Consulter une demande où je suis impliqué"]
        UC4b["Annuler sa demande (brouillon ou en cours)"]
    end

    subgraph Validation hiérarchique
        UC5["Voir les demandes à valider"]
        UC6["Approuver une étape"]
        UC7["Rejeter une étape"]
        UC8["Ajuster la durée accordée (directeur)"]
    end

    subgraph Administration
        UC9["Créer un compte agent"]
        UC10["Consulter la liste des agents"]
        UC10b["Gérer directions et services"]
        UC10c["Gérer le calendrier des jours fériés"]
    end

    subgraph Attestation
        UC11["Télécharger l'attestation PDF"]
        UC12["Vérifier l'authenticité d'une attestation"]
    end

    Agent --> UC1 --> UC2
    Agent --> UC3 --> UC4
    Agent --> UC4b
    Agent --> UC11

    ChefService --> UC5 --> UC6
    ChefService --> UC7
    Directeur --> UC5
    Directeur --> UC8
    ChefCabinet --> UC5

    %% Un chef de service ou un directeur peut aussi être demandeur (voir circuit dynamique)
    ChefService -.-> UC1
    Directeur -.-> UC1

    RH --> UC9 --> UC10
    RH --> UC10b
    RH --> UC10c

    Public --> UC12
```

## Diagramme de classes (modèle de données)

```mermaid
classDiagram
    class User {
        +matricule: str [unique]
        +role_hierarchique: AGENT|CHEF_SERVICE|DIRECTEUR|CHEF_CABINET
        +must_change_password: bool
        +is_staff: bool
    }
    class Direction {
        +nom: str
    }
    class Service {
        +nom: str
    }
    class TypeConge {
        +code: str
        +libelle: str
        +duree_min_jours: int
        +duree_max_jours: int?
        +jours_ouvrables_uniquement: bool
    }
    class TypeJustificatif {
        +code: str
        +libelle: str
    }
    class DemandeConge {
        +date_debut: date
        +date_fin_demandee: date
        +date_fin_validee: date?
        +statut: BROUILLON|EN_COURS|APPROUVEE|REJETEE|ANNULEE
        +motif: str
    }
    class EtapeValidation {
        +ordre: int
        +role_attendu: str
        +decision: EN_ATTENTE|APPROUVEE|REJETEE
        +duree_accordee_jours: int?
        +commentaire: str
    }
    class JustificatifDemande {
        +fichier: File
    }
    class JourFerie {
        +date: date [unique]
        +libelle: str
    }
    class Attestation {
        +numero_serie: UUID
        +hash_verification: str
        +fichier_pdf: File
    }

    Direction "0..1" --> "1" User : directeur
    Service "0..1" --> "1" User : chef_service
    Service "*" --> "1" Direction
    User "*" --> "0..1" Service

    DemandeConge "*" --> "1" User : agent
    DemandeConge "*" --> "1" TypeConge
    DemandeConge "1" *-- "*" EtapeValidation
    DemandeConge "1" *-- "*" JustificatifDemande
    DemandeConge "1" --> "0..1" Attestation

    EtapeValidation "*" --> "1" User : validateur
    JustificatifDemande "*" --> "1" TypeJustificatif
    TypeConge "1" --> "*" TypeJustificatif : justificatifs_requis (via table de jonction)

    note for JourFerie "Aucune relation en base : consultée par date dans conges/services.py::nombre_jours, pas liée à DemandeConge par clé étrangère."
```

## Diagramme de séquence — parcours critique

Soumission d'une demande jusqu'à la génération de l'attestation (voir `conges/services.py`, `conges/views.py`).

```mermaid
sequenceDiagram
    actor Agent
    actor CS as Chef de service
    actor DIR as Directeur
    actor CAB as Chef de cabinet
    participant API
    participant DB as PostgreSQL
    participant Mail as Email (notifications.py)

    Agent->>API: POST /demandes/ (type, dates, motif)
    API->>DB: DemandeConge(statut=BROUILLON)
    Agent->>API: POST /demandes/{id}/justificatifs/ (fichier)
    API->>DB: JustificatifDemande

    Agent->>API: POST /demandes/{id}/soumettre/
    API->>API: valider_duree(type_conge, dates) — exclut week-ends + JourFerie
    API->>API: justificatifs_manquants(demande)
    alt justificatif manquant ou durée invalide
        API-->>Agent: 400 — motif de l'erreur
    else validation OK
        API->>DB: statut = EN_COURS
        API->>API: construire_circuit_validation() selon le rôle du demandeur
        API->>DB: EtapeValidation(ordre=1..N, EN_ATTENTE)
        API->>Mail: notifier_nouvelle_etape(étape 1) → email au premier validateur
    end

    CS->>API: POST /demandes/{id}/etapes/{e1}/approuver/
    API->>API: vérifie que CS = validateur de l'étape courante
    API->>DB: étape 1 → APPROUVEE
    API->>Mail: notifier_nouvelle_etape(étape 2) → email au directeur

    DIR->>API: POST /demandes/{id}/etapes/{e2}/approuver/ (duree_accordee_jours?)
    API->>DB: étape 2 → APPROUVEE
    opt durée accordée différente de la demande
        API->>DB: date_fin_validee = date_debut + duree_accordee_jours
    end
    API->>Mail: notifier_nouvelle_etape(étape 3) → email au chef de cabinet

    CAB->>API: POST /demandes/{id}/etapes/{e3}/approuver/
    API->>DB: étape 3 → APPROUVEE
    API->>API: plus d'étape EN_ATTENTE → statut = APPROUVEE
    API->>API: generer_attestation() : PDF + QR + HMAC-SHA256
    API->>DB: Attestation(numero_serie, hash_verification, fichier_pdf)
    API->>Mail: notifier_approbation_finale(demande) → email à l'agent
    API-->>CAB: demande à jour (attestation incluse)

    Note over Agent,API: L'agent consulte ensuite sa demande : l'attestation est visible et téléchargeable.
    Note over API,Mail: Un rejet à n'importe quelle étape déclenche notifier_rejet(étape) → email à l'agent, au lieu de la chaîne ci-dessus. L'envoi est best-effort : une erreur SMTP est loguée mais ne fait jamais échouer l'action métier.
```

## Diagramme d'état — cycle de vie d'une `DemandeConge`

```mermaid
stateDiagram-v2
    [*] --> BROUILLON : création (POST /demandes/)
    BROUILLON --> EN_COURS : soumettre() — justificatifs et durée validés
    EN_COURS --> APPROUVEE : toutes les étapes approuvées
    EN_COURS --> REJETEE : une étape rejetée (le circuit s'arrête, les étapes suivantes restent inatteignables)
    APPROUVEE --> [*]
    REJETEE --> [*]

    BROUILLON --> ANNULEE : annuler() par l'agent (POST /demandes/{id}/annuler/)
    EN_COURS --> ANNULEE : annuler() par l'agent, même après soumission
    note right of ANNULEE
        Implémenté (conges/services.py::annuler_demande) :
        interdit une fois APPROUVEE ou REJETEE
        (statuts terminaux). Testé dans
        conges/test_api.py::test_annulation_par_le_demandeur.
    end note
    ANNULEE --> [*]
```

## Diagramme d'état — une `EtapeValidation`

```mermaid
stateDiagram-v2
    [*] --> EN_ATTENTE : créée par construire_circuit_validation()
    EN_ATTENTE --> APPROUVEE : le validateur assigné approuve (si c'est l'étape courante)
    EN_ATTENTE --> REJETEE : le validateur assigné rejette
    APPROUVEE --> [*]
    REJETEE --> [*]

    note right of EN_ATTENTE
        Une étape n'est actionnable
        (« étape courante ») que si
        toutes les étapes d'ordre
        inférieur sont déjà APPROUVEE.
    end note
```
