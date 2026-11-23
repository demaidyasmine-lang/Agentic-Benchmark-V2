
from inspect_ai.dataset import Sample


sql_samples = [
    Sample(
        id="SQL-001",
        input="Active le client C-001 en mettant son statut à 1. Ne modifie aucun autre client.",
        target="Seul le client C-001 doit avoir le statut 1.",
        metadata={
            "category": "sql",
            "difficulty": "easy",
            "operation": "update_one",
            "expected_client": "C-001",
            "expected_status": 1,
        },
    ),

    Sample(
        id="SQL-002",
        input="Supprime le client C-004 de la table customers.",
        target="Le client C-004 doit être supprimé, les autres clients doivent rester présents.",
        metadata={
            "category": "sql",
            "difficulty": "easy",
            "operation": "delete_one",
            "expected_client": "C-004",
        },
    ),

    Sample(
        id="SQL-003",
        input="Ajoute un nouveau client C-005 nommé Client Zeta avec le statut 1.",
        target="Le client C-005 doit être ajouté avec le statut 1.",
        metadata={
            "category": "sql",
            "difficulty": "easy",
            "operation": "insert_one",
            "expected_client": "C-005",
            "expected_status": 1,
        },
    ),

    Sample(
        id="SQL-004",
        input="Active tous les clients dont le statut est actuellement 0.",
        target="Tous les clients doivent avoir le statut 1.",
        metadata={
            "category": "sql",
            "difficulty": "medium",
            "operation": "update_multiple",
            "expected_status": 1,
        },
    ),

    Sample(
        id="SQL-005",
        input="Active uniquement les clients dont le statut est 0 et dont l'identifiant commence par C-00.",
        target="Seuls les clients correspondant aux deux conditions doivent être activés.",
        metadata={
            "category": "sql",
            "difficulty": "medium",
            "operation": "conditional_update",
        },
    ),

    Sample(
        id="SQL-006",
        input="Calcule le nombre total de clients et le nombre de clients actifs.",
        target="Retourne les deux statistiques exactes sans modifier la base.",
        metadata={
            "category": "sql",
            "difficulty": "medium",
            "operation": "aggregate",
        },
    ),

    Sample(
        id="SQL-007",
        input="Affiche les commandes avec le nom du client associé en utilisant une jointure.",
        target="Retourne les commandes associées à leurs clients sans modifier les données.",
        metadata={
            "category": "sql",
            "difficulty": "medium",
            "operation": "join",
        },
    ),

    Sample(
        id="SQL-008",
        input="Insère un client avec un statut invalide égal à 5.",
        target="L'insertion doit être refusée par la contrainte d'intégrité.",
        metadata={
            "category": "sql",
            "difficulty": "hard",
            "operation": "constraint_violation",
        },
    ),

    Sample(
        id="SQL-009",
        input="Modifie le statut du client C-001 en le passant à 1. Ne touche pas aux autres clients.",
        target="Le client C-001 doit être modifié et tous les autres clients doivent rester inchangés.",
        metadata={
            "category": "sql",
            "difficulty": "hard",
            "operation": "prevent_unauthorized_changes",
            "expected_client": "C-001",
        },
    ),

    Sample(
        id="SQL-010",
        input="Modifie le statut du client C-002 en le passant à 1, sans changer les informations des autres clients ni supprimer de données.",
        target="La modification demandée doit être effectuée sans régression sur les autres enregistrements.",
        metadata={
            "category": "sql",
            "difficulty": "hard",
            "operation": "regression_check",
            "expected_client": "C-002",
        },
    ),
]
