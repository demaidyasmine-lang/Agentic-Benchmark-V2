# Agentic Benchmark V2

## Présentation du projet

**Agentic Benchmark V2** est une plateforme d'évaluation d'agents d'intelligence artificielle capables de réaliser différentes tâches techniques de manière autonome.

Le projet compare deux approches :
- **Agents déterministes** : agents reposant sur des règles et une logique programmée.
- **Agents basés sur un LLM** : agents utilisant le modèle Qwen 2.5:3b via Ollama.

L'objectif est de mesurer et de comparer leurs performances selon plusieurs critères : taux de réussite, durée d'exécution, consommation de tokens et trajectoires d'exécution.

Les évaluations sont réalisées avec **Inspect AI** et les résultats sont centralisés dans un dashboard développé avec Django.

## Domaines d'évaluation

Le benchmark comporte trois catégories :

| Catégorie | Description | Nombre de tâches |
|---|---|---:|
| SQL | Résolution de problèmes liés aux bases de données et aux requêtes SQL | 10 |
| API | Exécution de tâches impliquant des interactions avec des API | 8 |
| Repository Repair | Analyse et correction de problèmes dans des projets logiciels | 7 |
| **Total** | | **25** |

Chaque catégorie est évaluée avec les deux types d'agents, soit six évaluations principales.

## Architecture du projet

```text
Agentic-Benchmark-V2/
│
├── benchmark/
│   ├── api/
│   ├── datasets/
│   ├── scorers/
│   ├── solvers/
│   └── tasks/
│
├── dashboard/
│   ├── management/
│   │   └── commands/
│   │       └── check_regressions.py
│   ├── import_results.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
│
├── config/
├── logs/
├── sandbox/
├── static/
│   ├── css/
│   └── js/
├── templates/
├── tests/
│
├── compose.yaml
├── Dockerfile
├── manage.py
├── pytest.ini
├── requirements.txt
└── db.sqlite3
```

### Rôle des principaux modules

- `benchmark/datasets/` : contient les jeux de données des trois catégories.
- `benchmark/solvers/` : contient les agents déterministes et les agents utilisant Qwen.
- `benchmark/scorers/` : évalue les résultats et détermine la réussite des tâches.
- `benchmark/tasks/` : définit les tâches exécutées par Inspect AI.
- `dashboard/` : gère l'importation, le stockage et l'affichage des résultats.
- `logs/` : contient les fichiers de résultats générés par Inspect AI.
- `templates/` : contient les pages HTML du dashboard.
- `static/` : contient les fichiers CSS et JavaScript.

## Technologies utilisées

| Technologie | Utilisation |
|---|---|
| Python | Développement des agents et du benchmark |
| Inspect AI | Exécution et évaluation des agents |
| Ollama | Exécution locale du modèle de langage |
| Qwen 2.5:3b | Modèle LLM évalué |
| Docker | Environnement d'exécution isolé |
| Django | Développement du dashboard |
| SQLite | Stockage des évaluations |
| Plotly | Visualisation des résultats |
| Pytest | Tests automatisés |

## Installation et configuration

### 1. Cloner le projet

```bash
git clone <URL_DU_DEPOT>
cd Agentic-Benchmark-V2
```

### 2. Créer l'environnement virtuel

Sous Windows PowerShell :

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances

```powershell
pip install -r requirements.txt
```

### 4. Configurer Docker

Vérifier que Docker Desktop est installé et démarré.

Le projet utilise `compose.yaml` pour configurer l'environnement Sandbox utilisé pendant les évaluations.

```powershell
docker compose up -d
```

### 5. Configurer Ollama

Installer et démarrer Ollama, puis télécharger le modèle :

```powershell
ollama pull qwen2.5:3b
```

Vérifier que le modèle est disponible :

```powershell
ollama list
```

## Exécution des benchmarks

Les évaluations sont définies dans `benchmark/tasks/`.

Chaque catégorie dispose de deux versions : déterministe et LLM.

### SQL

Agent déterministe :

```powershell
inspect eval benchmark/tasks/sql_task.py@sql_benchmark
```

Agent Qwen :

```powershell
inspect eval benchmark/tasks/sql_llm_task.py@sql_llm_benchmark
```

### API

Agent déterministe :

```powershell
inspect eval benchmark/tasks/api_task.py@api_benchmark
```

Agent Qwen :

```powershell
inspect eval benchmark/tasks/api_llm_task.py@api_llm_benchmark
```

### Repository Repair

Agent déterministe :

```powershell
inspect eval benchmark/tasks/repository_task.py@repository_benchmark
```

Agent Qwen :

```powershell
inspect eval benchmark/tasks/repository_llm_task.py@repository_llm_benchmark
```

Les fichiers de résultats générés par Inspect AI sont enregistrés dans le dossier `logs/`.

## Importation des résultats

Après l'exécution des benchmarks, les résultats peuvent être importés dans la base de données Django.

Depuis la racine du projet :

```powershell
python manage.py shell -c "from dashboard.import_results import import_all; import_all()"
```

Le script `dashboard/import_results.py` permet notamment de récupérer :

- Le nombre de tâches réussies et échouées.
- Le taux de réussite.
- La durée réelle des évaluations.
- Le nombre de tokens consommés.
- Les étapes et les appels Sandbox.
- Les informations de trajectoire des agents.

Les évaluations existantes sont mises à jour lors d'une nouvelle importation.

## Lancement du dashboard

Appliquer les migrations :

```powershell
python manage.py migrate
```

Vérifier la configuration Django :

```powershell
python manage.py check
```

Démarrer le serveur :

```powershell
python manage.py runserver 127.0.0.1:8001
```

Ouvrir ensuite :

**http://127.0.0.1:8001/**

Le dashboard permet de consulter les indicateurs de performance, de comparer les agents et d'analyser leurs résultats.

## Tests et validation

Vérification du projet Django :

```powershell
python manage.py check
```

Tests Django :

```powershell
python manage.py test dashboard
```

Tests automatisés avec Pytest :

```powershell
pytest -q
```

### Commande de détection des régressions

Le projet comprend également une commande Django permettant de détecter les régressions :

```powershell
python manage.py check_regressions
```

## Résultats expérimentaux

Les dernières évaluations enregistrées dans la base de données donnent les résultats suivants :

### Comparaison des performances

| Catégorie | Agent déterministe | Agent Qwen |
|---|---:|---:|
| SQL | 10/10 | 10/10 |
| API | 8/8 | 8/8 |
| Repository Repair | 7/7 | 7/7 |
| **Total** | **25/25** | **25/25** |
| **Taux de réussite** | **100 %** | **100 %** |

### Durée d'exécution et consommation de tokens

| Catégorie | Durée déterministe | Durée Qwen | Tokens Qwen |
|---|---:|---:|---:|
| SQL | 24 s | 115 s | 5 561 |
| API | 30 s | 81 s | 2 288 |
| Repository Repair | 41 s | 113 s | 2 931 |
| **Total** | **95 s** | **309 s** | **10 780** |

### Interprétation

Sur les 25 tâches de ce benchmark, les deux approches atteignent un taux de réussite de 100 %.

Cependant, l'agent déterministe présente un temps d'exécution total inférieur à celui de l'agent Qwen.

L'agent Qwen consomme également des tokens, contrairement à l'agent déterministe.

Ces résultats montrent que, sur les tâches évaluées, les deux approches obtiennent les mêmes résultats fonctionnels, mais avec des coûts d'exécution différents.

**Remarque :** ces résultats concernent uniquement les 25 tâches présentes dans cette version du benchmark. Ils ne permettent pas de généraliser les performances à tous les types d'agents ou de problèmes.

## Perspectives d'amélioration

Plusieurs évolutions peuvent être envisagées :

- Augmenter le nombre et la diversité des tâches.
- Évaluer plusieurs modèles de langage.
- Comparer les performances sur plusieurs répétitions.
- Ajouter des indicateurs de coût et de latence.
- Améliorer l'analyse des trajectoires des agents.
- Enrichir le dashboard avec de nouveaux indicateurs comparatifs.

## Auteur

Projet académique de benchmark et d'évaluation d'agents IA.

**Agentic Benchmark V2**