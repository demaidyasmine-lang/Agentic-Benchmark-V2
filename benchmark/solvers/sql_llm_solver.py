
import json
import re

from inspect_ai.model import ChatMessageUser, ModelOutput
from inspect_ai.solver import solver, TaskState, Generate
from inspect_ai.util import sandbox


@solver
def ollama_sql_solver():

    async def solve(state: TaskState, generate: Generate) -> TaskState:

        sample_id = str(state.sample_id)
        operation = state.metadata.get("operation")

        # 1. Initialiser une base de donnees propre
        init_script = r'''
import sqlite3
import json

sample_id = __SAMPLE_ID__
db_path = f"/workspace/benchmark/datasets/data/{sample_id}.db"

with sqlite3.connect(db_path) as connection:
    connection.execute("PRAGMA foreign_keys = ON")

    connection.execute("DROP TABLE IF EXISTS orders")
    connection.execute("DROP TABLE IF EXISTS customers")

    connection.execute("""
        CREATE TABLE customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status INTEGER NOT NULL CHECK (status IN (0, 1))
        )
    """)

    connection.execute("""
        CREATE TABLE orders (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    connection.executemany(
        "INSERT INTO customers VALUES (?, ?, ?)",
        [
            ("C-001", "Client Alpha", 0),
            ("C-002", "Client Beta", 0),
            ("C-003", "Client Gamma", 1),
            ("C-004", "Client Delta", 0),
            ("C-100", "Client Epsilon", 0),
        ],
    )

    connection.executemany(
        "INSERT INTO orders VALUES (?, ?, ?)",
        [
            ("O-001", "C-001", 125.0),
            ("O-002", "C-002", 75.0),
            ("O-003", "C-003", 200.0),
        ],
    )

    connection.commit()

print(json.dumps({"initialized": True}))
'''

        init_script = init_script.replace(
            "__SAMPLE_ID__",
            json.dumps(sample_id),
        )

        try:
            initialization = await sandbox().exec(
                ["python", "-c", init_script],
                timeout=30,
            )

            if (
                not initialization.success
                or initialization.returncode != 0
            ):
                raise RuntimeError(
                    f"Database initialization failed: "
                    f"{initialization.stderr}"
                )

        except Exception as error:
            state.output = ModelOutput.from_content(
                model="ollama/qwen2.5:3b",
                content=json.dumps({
                    "success": False,
                    "error": str(error),
                }),
            )
            return state

        # 2. Preparer la consigne destinee au modele
        task_instruction = str(state.input)

        operation_guidance = {
            "aggregate": """
OPERATION : AGGREGATE

Objectif obligatoire :
Calculer le nombre total de clients et le nombre de clients actifs.

REGLES STRICTES :

1. Utiliser UNIQUEMENT la table customers.
2. Utiliser obligatoirement l'alias c pour customers.
3. Ne faire AUCUNE jointure.
4. Ne jamais utiliser JOIN, LEFT JOIN, INNER JOIN ou RIGHT JOIN.
5. Ne jamais utiliser WHERE.
6. Ne jamais filtrer les clients selon leurs commandes.
7. Ne jamais utiliser la table orders.
8. Compter tous les clients avec :
   COUNT(DISTINCT c.id) AS total_clients
9. Compter les clients actifs avec :
   COUNT(DISTINCT CASE
       WHEN c.status = 1 THEN c.id
   END) AS active_clients

La requete doit retourner exactement deux colonnes,
dans cet ordre :
- total_clients
- active_clients

UTILISER EXACTEMENT CETTE STRUCTURE SQL :

SELECT
    COUNT(DISTINCT c.id) AS total_clients,
    COUNT(DISTINCT CASE
        WHEN c.status = 1 THEN c.id
    END) AS active_clients
FROM customers c;

IMPORTANT :
- Ne rien ajouter avant SELECT.
- Ne rien ajouter apres FROM customers c.
- Ne modifier aucune partie de cette requete.
- Ne pas ajouter de jointure.
- Ne pas ajouter de condition WHERE.
""",

            "update_multiple": """
OPERATION : UPDATE MULTIPLE

Objectif obligatoire :
- Modifier le statut de TOUS les clients.
- Chaque client doit avoir status = 1.
- Cela concerne C-001, C-002, C-003, C-004 et C-100.
- Ne laisse aucun client avec status = 0.
- Utilise une seule requete UPDATE sur la table customers.
- Ne supprime et n'ajoute aucun client.
""",

            "conditional_update": """
OPERATION : CONDITIONAL UPDATE

Objectif obligatoire :
- Mettre status = 1 pour les clients C-001, C-002,
  C-003 et C-004.
- Ne pas modifier C-100 (Client Epsilon).
- Utilise une clause WHERE qui cible uniquement
  C-001, C-002, C-003 et C-004.
- Ne modifie pas les noms des clients.
- Ne supprime aucun client.
""",

            "join": """
OPERATION : JOIN

Objectif obligatoire :
- Effectuer une jointure entre orders et customers.
- Relier orders.customer_id a customers.id.
- Retourner exactement trois colonnes dans cet ordre :

  1. orders.id AS order_id
  2. customers.name AS customer_name
  3. orders.amount AS order_amount

- Utiliser cet ordre de colonnes sans le modifier.
- Trier les resultats par orders.id en ordre croissant.
- Ne retourner aucune autre colonne.

La requete attendue doit suivre cette structure :

SELECT
    orders.id AS order_id,
    customers.name AS customer_name,
    orders.amount AS order_amount
FROM orders
JOIN customers
    ON orders.customer_id = customers.id
ORDER BY orders.id ASC;
"""
        }

        specific_guidance = operation_guidance.get(
            operation,
            "Respecte precisement la consigne demandee."
        )

        prompt = f"""
Tu es un agent specialise en SQL et SQLite.

Ta mission est de generer UNE SEULE requete SQL
qui repond exactement a la consigne.

CONSIGNE :
{task_instruction}

INSTRUCTIONS SPECIFIQUES A CETTE OPERATION :
{specific_guidance}

STRUCTURE DE LA BASE :

Table customers :
- id TEXT PRIMARY KEY
- name TEXT NOT NULL
- status INTEGER NOT NULL CHECK (status IN (0, 1))

Table orders :
- id TEXT PRIMARY KEY
- customer_id TEXT NOT NULL
- amount REAL NOT NULL
- customer_id reference customers(id)

DONNEES INITIALES :

customers :
- C-001, Client Alpha, 0
- C-002, Client Beta, 0
- C-003, Client Gamma, 1
- C-004, Client Delta, 0
- C-100, Client Epsilon, 0

orders :
- O-001, C-001, 125.0
- O-002, C-002, 75.0
- O-003, C-003, 200.0

REGLES IMPORTANTES :
- Genere une requete SQLite valide.
- Respecte exactement les instructions.
- Ne modifie pas les donnees non concernees.
- N'effectue aucune operation supplementaire.
- Pour une lecture, utilise SELECT.
- Pour une modification, utilise UPDATE, INSERT ou DELETE.
- Pour une insertion invalide, laisse SQLite appliquer ses contraintes.
- Retourne uniquement la requete SQL.
- N'ajoute aucune explication.
- N'utilise pas plusieurs requetes SQL.
- Verifie mentalement les conditions WHERE avant de repondre.

REPONSE :
"""

        state.messages.append(
            ChatMessageUser(content=prompt)
        )

        # 3. Demander au modele Ollama de generer le SQL
        try:
            state = await generate(state)

            if state.output is None:
                raise ValueError(
                    "Le modele n'a retourne aucune reponse."
                )

            model_response = state.output.completion.strip()

            # Extraire la requete SQL
            fenced = re.search(
                r"```(?:sql)?\s*(.*?)```",
                model_response,
                re.IGNORECASE | re.DOTALL,
            )

            if fenced:
                sql_query = fenced.group(1).strip()
            else:
                match = re.search(
                    r"\b(?:SELECT|INSERT|UPDATE|DELETE)\b.*",
                    model_response,
                    re.IGNORECASE | re.DOTALL,
                )

                if not match:
                    raise ValueError(
                        f"Aucune requete SQL detectee : "
                        f"{model_response}"
                    )

                sql_query = match.group(0).strip()

            sql_query = sql_query.rstrip(";").strip() + ";"

        except Exception as error:
            state.output = ModelOutput.from_content(
                model="ollama/qwen2.5:3b",
                content=json.dumps({
                    "success": False,
                    "error": str(error),
                }),
            )
            return state

        # 4. Executer la requete SQL dans Docker
        execution_script = r'''
import sqlite3
import json

sample_id = __SAMPLE_ID__
operation = __OPERATION__
sql_query = __SQL_QUERY__

db_path = f"/workspace/benchmark/datasets/data/{sample_id}.db"

try:
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        cursor = connection.execute(sql_query)

        if operation == "aggregate":
            row = cursor.fetchone()

            result = {
                "total_clients": row[0] if row else None,
                "active_clients": row[1] if row else None,
            }

        elif operation == "join":
            rows = cursor.fetchall()

            result = {
                "orders": [list(row) for row in rows]
            }

        elif operation == "constraint_violation":
            result = {
                "rejected": False
            }

        else:
            result = {
                "success": True,
                "rows_affected": cursor.rowcount,
            }

        connection.commit()

except sqlite3.IntegrityError as error:
    if operation == "constraint_violation":
        result = {
            "rejected": True
        }
    else:
        result = {
            "success": False,
            "error": str(error),
        }

except Exception as error:
    result = {
        "success": False,
        "error": str(error),
    }

print(json.dumps(result))
'''

        execution_script = (
            execution_script
            .replace("__SAMPLE_ID__", json.dumps(sample_id))
            .replace("__OPERATION__", json.dumps(operation))
            .replace("__SQL_QUERY__", json.dumps(sql_query))
        )

        try:
            execution = await sandbox().exec(
                ["python", "-c", execution_script],
                timeout=30,
            )

            if (
                not execution.success
                or execution.returncode != 0
            ):
                result = {
                    "success": False,
                    "error": execution.stderr.strip(),
                    "sql_query": sql_query,
                }
            else:
                result = json.loads(
                    execution.stdout.strip()
                )
                result["sql_query"] = sql_query

        except Exception as error:
            result = {
                "success": False,
                "error": str(error),
                "sql_query": sql_query,
            }

        # 5. Retourner le resultat au scorer independant
        state.output = ModelOutput.from_content(
            model="ollama/qwen2.5:3b",
            content=json.dumps(result),
        )

        return state

    return solve
