
from inspect_ai.dataset import Sample


repository_samples = [
    Sample(
        id="REPO-001",
        input="Corrige calculate_discount dans app.py. La fonction doit retourner le prix après remise, et non le montant de la remise.",
        target="Tous les tests pytest doivent réussir.",
        metadata={
            "category": "repository",
            "difficulty": "easy",
            "operation": "discount",
        },
    ),
    Sample(
        id="REPO-002",
        input="Corrige is_valid_email dans app.py pour rejeter les adresses email sans domaine valide.",
        target="Tous les tests pytest doivent réussir.",
        metadata={
            "category": "repository",
            "difficulty": "easy",
            "operation": "email_validation",
        },
    ),
    Sample(
        id="REPO-003",
        input="Corrige normalize_name dans app.py. La fonction doit supprimer les espaces au début et à la fin, remplacer toute suite d'espaces entre les mots par un seul tiret (-), et convertir le nom en minuscules. Exemple : '  Alice   Smith  ' doit retourner 'alice-smith'.",
        target="Tous les tests pytest doivent réussir.",
        metadata={
            "category": "repository",
            "difficulty": "easy",
            "operation": "normalize_name",
        },
    ),
    Sample(
        id="REPO-004",
        input="Corrige sort_products pour trier les produits par prix dans l'ordre croissant.",
        target="Tous les tests pytest doivent réussir.",
        metadata={
            "category": "repository",
            "difficulty": "medium",
            "operation": "sort_products",
        },
    ),
    Sample(
        id="REPO-005",
        input="Corrige filter_active_users pour retourner uniquement les utilisateurs actifs.",
        target="Tous les tests pytest doivent réussir.",
        metadata={
            "category": "repository",
            "difficulty": "medium",
            "operation": "filter_active_users",
        },
    ),
    Sample(
        id="REPO-006",
        input="Corrige safe_divide pour gérer les entrées non numériques sans provoquer d'exception.",
        target="Tous les tests pytest doivent réussir.",
        metadata={
            "category": "repository",
            "difficulty": "hard",
            "operation": "safe_divide",
        },
    ),
    Sample(
        id="REPO-007",
        input="Corrige calculate_cart_total pour calculer correctement le sous-total et appliquer la TVA sur l'ensemble du sous-total, sans casser le panier vide.",
        target="Tous les tests pytest doivent réussir.",
        metadata={
            "category": "repository",
            "difficulty": "hard",
            "operation": "cart_total",
        },
    ),
]
