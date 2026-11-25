# ✅ TaskFlow — API de tâches cloud-native (Kubernetes & GitOps)

API REST de gestion de tâches construite avec **FastAPI** et **PostgreSQL**, sécurisée par **JWT**, observable avec **Prometheus**, conteneurisée avec **Docker** et déployée sur **Kubernetes** en **GitOps** avec **Argo CD**. Le pipeline **Jenkins** teste, scanne, publie l'image puis met à jour le dépôt : Argo CD déploie automatiquement.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Kustomize-326CE5?logo=kubernetes&logoColor=white)
![Argo CD](https://img.shields.io/badge/GitOps-Argo%20CD-EF7B4D?logo=argo&logoColor=white)
![Jenkins](https://img.shields.io/badge/Jenkins-pipeline-D24939?logo=jenkins&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue)

## Fonctionnalités

- **Authentification** : inscription, connexion OAuth2 (jeton JWT), mots de passe hachés avec PBKDF2-SHA256 et sel aléatoire
- **Tâches** : création, lecture, mise à jour partielle, suppression ; statut (`todo` / `doing` / `done`), priorité, échéance
- **Recherche** : filtres par statut et priorité, recherche dans le titre, pagination
- **Statistiques** : répartition par statut, tâches en retard, taux de complétion
- **Isolation des données** : un utilisateur ne peut ni voir ni modifier les tâches d'un autre (testé)
- **Observabilité** : métriques Prometheus (`/metrics`), sondes Kubernetes `/health/live` et `/health/ready`
- **Documentation interactive** générée automatiquement : `/docs` (Swagger)

## Architecture

```mermaid
flowchart LR
    Dev[Développeur] -->|git push| GH[GitHub]
    GH --> J[Jenkins]
    J -->|tests, Trivy, build| DH[(Docker Hub)]
    J -->|met à jour le tag| GH
    GH -->|surveillé par| A[Argo CD]
    A -->|synchronise| K[Cluster Kubernetes]
    K --> API[Pods TaskFlow API]
    API --> DB[(PostgreSQL)]
    P[Prometheus] -->|/metrics| API
```

```
app/
├── main.py            # Application, sondes, middleware de métriques
├── config.py          # Configuration par variables d'environnement
├── database.py        # SQLAlchemy 2 (PostgreSQL / SQLite)
├── models.py          # Tables User et Task
├── schemas.py         # Validation Pydantic
├── security.py        # Hachage PBKDF2 et JWT
└── routers/           # auth.py, tasks.py
tests/                 # 16 tests (pytest)
k8s/
├── base/              # Deployment, Service, HPA, Ingress, ConfigMap, PostgreSQL
└── overlays/          # dev (1 pod) et prod (3 à 10 pods)
argocd/application.yaml
Jenkinsfile
```

## API

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Créer un compte |
| `POST` | `/api/v1/auth/login` | Obtenir un jeton JWT |
| `GET` | `/api/v1/auth/me` | Profil de l'utilisateur connecté |
| `GET` | `/api/v1/tasks?status=&priority=&q=&limit=&offset=` | Lister et filtrer ses tâches |
| `POST` | `/api/v1/tasks` | Créer une tâche |
| `GET` / `PATCH` / `DELETE` | `/api/v1/tasks/{id}` | Lire, modifier, supprimer |
| `GET` | `/api/v1/tasks/stats` | Statistiques |
| `GET` | `/health/live`, `/health/ready` | Sondes Kubernetes |
| `GET` | `/metrics` | Métriques Prometheus |

## Lancer le projet

**Avec Docker Compose (API + PostgreSQL)**

```bash
docker compose up -d --build
# Swagger : http://localhost:8000/docs
```

**En local**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest
```

**Sur Kubernetes (minikube, kind ou OpenShift)**

```bash
kubectl apply -k k8s/overlays/dev
kubectl -n taskflow-dev get pods
```

En production, le Secret est créé à part et n'est jamais versionné :

```bash
kubectl -n taskflow create secret generic taskflow-secrets \
  --from-literal=POSTGRES_USER=taskflow \
  --from-literal=POSTGRES_PASSWORD='...' \
  --from-literal=DATABASE_URL='postgresql+psycopg://taskflow:...@taskflow-db:5432/taskflow' \
  --from-literal=JWT_SECRET='...'
kubectl apply -f argocd/application.yaml
```

## Pipeline CI/CD

```
Lint & tests → Validation K8s → Build image → Trivy → Smoke test → Push Docker Hub → Mise à jour GitOps
```

- **Jenkins** : ruff + pytest dans un conteneur Python, validation des manifestes (kustomize + kubeconform), scan Trivy bloquant, test du conteneur, push de l'image versionnée, puis commit du nouveau tag dans `k8s/overlays/prod`. Argo CD détecte le commit et déploie.
- **GitHub Actions** : mêmes contrôles, avec en plus un démarrage de l'API sur un vrai PostgreSQL.

## Sécurité

- Conteneur exécuté sans root, système de fichiers en lecture seule, capacités Linux retirées
- Secrets injectés par Kubernetes, jamais dans le code ni dans le dépôt (sauf valeurs de démonstration en dev)
- Comparaison des mots de passe à temps constant, messages d'erreur qui ne révèlent pas les comptes existants
- Image scannée par Trivy à chaque build

## Pistes d'amélioration

- Migrations de base de données avec Alembic
- Tableau de bord Grafana et alertes Prometheus
- Gestion des secrets avec Sealed Secrets ou HashiCorp Vault
- Rafraîchissement des jetons (refresh token)

---

Réalisé avec l'aide d'un assistant IA.

## Auteure

**Mayssa Dhahri** — élève-ingénieure en Génie Logiciel, École Polytechnique de Sousse
[LinkedIn](https://www.linkedin.com/in/mayssa-dhahri/) · [GitHub](https://github.com/mayssadhahri1)
