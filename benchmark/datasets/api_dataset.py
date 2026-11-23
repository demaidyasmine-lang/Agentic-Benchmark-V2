from inspect_ai.dataset import Sample


api_samples = [
    Sample(
        id="API-001",
        input="Envoie une requête GET sur /users/1 pour récupérer les informations de l'utilisateur.",
        target="L'API doit retourner l'utilisateur 1 avec un code HTTP 200.",
        metadata={
            "category": "api",
            "difficulty": "easy",
            "operation": "get_user",
        },
    ),
    Sample(
        id="API-002",
        input="Crée un utilisateur nommé Charlie avec l'adresse charlie@example.com et le rôle user.",
        target="L'utilisateur doit être créé avec un code HTTP 201.",
        metadata={
            "category": "api",
            "difficulty": "easy",
            "operation": "create_user",
        },
    ),
    Sample(
        id="API-003",
        input="Modifie le nom de l'utilisateur 1 en Alice Johnson avec une requête PUT.",
        target="Le nom de l'utilisateur 1 doit être Alice Johnson. Code HTTP 200.",
        metadata={
            "category": "api",
            "difficulty": "easy",
            "operation": "update_user",
        },
    ),
    Sample(
        id="API-004",
        input="Supprime l'utilisateur 2 avec une requête DELETE.",
        target="L'utilisateur 2 doit être supprimé. Code HTTP 200.",
        metadata={
            "category": "api",
            "difficulty": "medium",
            "operation": "delete_user",
        },
    ),
    Sample(
        id="API-005",
        input="Récupère tous les utilisateurs ayant le rôle admin avec un filtre GET.",
        target="Seuls les utilisateurs ayant le rôle admin doivent être retournés. Code HTTP 200.",
        metadata={
            "category": "api",
            "difficulty": "medium",
            "operation": "filter_users",
        },
    ),
    Sample(
        id="API-006",
        input="Essaie de créer un utilisateur sans fournir son adresse email.",
        target="L'API doit refuser la création avec le code HTTP 400.",
        metadata={
            "category": "api",
            "difficulty": "medium",
            "operation": "validate_missing_email",
        },
    ),
    Sample(
        id="API-007",
        input="Récupère les informations de l'utilisateur inexistant ayant l'identifiant 999.",
        target="L'API doit retourner le code HTTP 404.",
        metadata={
            "category": "api",
            "difficulty": "hard",
            "operation": "not_found",
        },
    ),
    Sample(
        id="API-008",
        input="Essaie de modifier l'utilisateur 1 avec une adresse email invalide. Aucune donnée ne doit être modifiée.",
        target="L'API doit refuser la modification et conserver intégralement les données initiales. Code HTTP 400.",
        metadata={
            "category": "api",
            "difficulty": "hard",
            "operation": "prevent_invalid_update",
        },
    ),
]
