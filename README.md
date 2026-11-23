# Agentic Benchmark V2

## 1. Présentation du projet

Agentic Benchmark V2 est une plateforme d'évaluation et de comparaison d'agents IA. Elle permet d'évaluer les performances d'agents déterministes et d'agents basés sur un modèle de langage (LLM) dans trois domaines :

- SQL : résolution de tâches liées aux bases de données.
- API : exécution et résolution de tâches liées aux API.
- Repository Repair : analyse et correction de problèmes dans des projets Python.

Le projet utilise Inspect AI pour l'exécution des évaluations et Django pour la visualisation des résultats.

## 2. Objectifs

- Évaluer les performances des agents sur plusieurs benchmarks.
- Comparer les agents déterministes et les agents IA.
- Mesurer la précision des réponses.
- Analyser les durées d'exécution et la consommation de tokens lorsqu'elle est disponible.
- Enregistrer et exploiter les résultats des évaluations.
- Visualiser les performances dans un tableau de bord.
- Automatiser les vérifications avec GitHub Actions et n8n.

## 3. Technologies utilisées

| Technologie | Utilisation |
|---|---|
| Python 3.12 | Développement |
| Inspect AI | Évaluation des agents |
| Django | Application web et dashboard |
| SQLite | Stockage des données |
| Docker | Environnement sandbox |
| Ollama | Exécution du modèle local |
| Qwen 2.5:3b | Agent basé sur un LLM |
| Plotly | Graphiques interactifs |
| GitHub Actions | Intégration continue |
| n8n | Notification des résultats CI |

## 4. Architecture du projet

```text
Agentic-Benchmark-V2/
├── benchmark/
│   ├── datasets/       # Jeux de données SQL, API et Repository
│   ├── solvers/        # Agents déterministes et LLM
│   ├── scorers/        # Évaluation des résultats
│   ├── tasks/          # Définition des benchmarks Inspect AI
│   ├── repository/     # Projets de réparation et fixtures
│   └── api/            # Serveur API de test
├── dashboard/
│   ├── models.py
│   ├── views.py
│   ├── import_results.py
│   ├── tests.py
│   └── management/
├── templates/
├── static/
├── config/
├── logs/
├── .github/workflows/
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── manage.py
└── README.md
```

## 5. Installation

### Prérequis

- Python 3.12
- Docker Desktop
- Ollama
- Git

### Cloner le projet

```bash
git clone https://github.com/demaidyasmine-lang/Agentic-Benchmark-V2.git
cd Agentic-Benchmark-V2
```

### Créer l'environnement virtuel

Sous Windows :

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Installer les dépendances

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Préparer le modèle local

```powershell
ollama pull qwen2.5:3b
ollama list
```

### Préparer Docker

Démarrer Docker Desktop, puis exécuter :

```powershell
docker compose up -d --build
```

## 6. Exécution des benchmarks

Depuis la racine du projet, définir le chemin Python :

```powershell
$env:PYTHONPATH = (Get-Location).Path
```

Les résultats sont enregistrés dans le dossier `logs/`.

### SQL

Agent déterministe :

```powershell
inspect eval benchmark\tasks\sql_task.py@sql_benchmark --log-dir logs --display plain
```

Agent Qwen :

```powershell
inspect eval benchmark\tasks\sql_llm_task.py@sql_llm_benchmark --model ollama/qwen2.5:3b --log-dir logs --display plain
```

### API

Agent déterministe :

```powershell
inspect eval benchmark\tasks\api_task.py@api_benchmark --log-dir logs --display plain
```

Agent Qwen :

```powershell
inspect eval benchmark\tasks\api_llm_task.py@api_llm_benchmark --model ollama/qwen2.5:3b --log-dir logs --display plain
```

### Repository Repair

Agent déterministe :

```powershell
inspect eval benchmark\tasks\repository_task.py@repository_benchmark --log-dir logs --display plain
```

Agent Qwen :

```powershell
inspect eval benchmark\tasks\repository_llm_task.py@repository_llm_benchmark --model ollama/qwen2.5:3b --log-dir logs --display plain
```

## 7. Importation des résultats

Après l'exécution des benchmarks :

```powershell
python manage.py shell -c "from dashboard.import_results import import_all; import_all()"
```

L'importateur analyse les évaluations disponibles, identifie les tâches prises en charge et enregistre les résultats dans la base de données Django.

## 8. Lancement du dashboard

Vérifier la configuration :

```powershell
python manage.py check
```

Lancer le serveur :

```powershell
python manage.py runserver 8001
```

Ouvrir dans le navigateur :

http://127.0.0.1:8001/

Le tableau de bord présente :

- Les indicateurs globaux des évaluations.
- L'historique des exécutions.
- La comparaison de la précision des agents.
- La comparaison des durées d'exécution.
- La consommation de tokens disponible.
- L'analyse des trajectoires d'exécution.

## 9. Tests et contrôle des régressions

Exécuter les tests Django :

```powershell
python manage.py test dashboard
```

Vérifier les régressions :

```powershell
python manage.py check_regressions
```

## 10. Intégration continue et automatisation

Le projet utilise GitHub Actions pour automatiser les vérifications lors des push et des pull requests vers la branche `main`.

Le workflow :

1. Récupère le dépôt.
2. Installe Python et les dépendances.
3. Exécute les vérifications Django.
4. Lance les tests du dashboard.
5. Transmet le résultat du workflow à un webhook n8n.

La notification nécessite la configuration du secret GitHub `N8N_WEBHOOK_URL`.

## 11. Résultats des dernières évaluations

Les dernières exécutions principales ont donné les résultats suivants :

| Benchmark | Nombre de tâches | Déterministe | Qwen 2.5:3b |
|---|---:|---:|---:|
| SQL | 10 | 100 % | 100 % |
| API | 8 | 100 % | 100 % |
| Repository Repair | 7 | 100 % | 100 % |

Ces résultats correspondent aux dernières exécutions réalisées pendant le développement et ne garantissent pas les performances des exécutions futures.

## 12. Remarques

- Les fichiers `.eval` sont générés par Inspect AI dans le dossier `logs/`.
- Les résultats importés sont conservés dans la base de données Django.
- La consommation de tokens dépend des statistiques fournies par le modèle. Elle peut être indisponible pour les agents déterministes.
- Docker est utilisé pour l'environnement sandbox des évaluations, et non comme configuration de déploiement de production.

## 13. Dépôt GitHub

https://github.com/demaidyasmine-lang/Agentic-Benchmark-V2
