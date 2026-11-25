"""Point d'entrée de l'API : routes, sondes Kubernetes et métriques Prometheus."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.routers import auth, tasks

REQUESTS = Counter("http_requests_total", "Nombre de requêtes HTTP", ["method", "route", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Durée des requêtes HTTP", ["method", "route"])


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Crée les tables au démarrage (un outil de migration comme Alembic serait l'étape suivante)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="TaskFlow API",
    version=settings.app_version,
    description="API de gestion de tâches, conteneurisée et déployée sur Kubernetes en GitOps.",
    lifespan=lifespan,
)
app.include_router(auth.router)
app.include_router(tasks.router)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    # On utilise le modèle de route (/api/v1/tasks/{task_id}) et pas l'URL réelle,
    # sinon chaque identifiant créerait une nouvelle série de métriques
    route = request.scope.get("route")
    path = route.path if route else "inconnue"
    LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    return response


@app.get("/health/live", tags=["sondes"])
def liveness() -> dict:
    """Le processus répond : Kubernetes le redémarre sinon."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["sondes"])
def readiness(response: Response) -> dict:
    """La base est joignable : sinon Kubernetes n'envoie pas de trafic à ce pod."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception:
        response.status_code = 503
        return {"status": "not ready", "database": "indisponible"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
