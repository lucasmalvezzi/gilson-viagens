from contextlib import asynccontextmanager
import logging
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.database import init_db
from app.routers import (
    configs_router,
    historico_router,
    logs_router,
    settings_router,
)
from app.scheduler import iniciar_scheduler, scheduler
from app.structured_log_store import activar_coletor_estruturado

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
activar_coletor_estruturado()
logger = logging.getLogger("flight_tracker")

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "frontend" / "dist" / "frontend" / "browser"


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """
    Inicializa o banco SQLite e o agendador no startup e encerra no shutdown.
    Exemplo: `FastAPI(lifespan=lifespan)`
    """
    init_db()
    iniciar_scheduler()
    yield
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(
    title="GilsonViagens - Flight Price Tracker API",
    description="Monitoramento automatizado de preços no Google Flights com alertas no Telegram",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(configs_router)
app.include_router(historico_router)
app.include_router(settings_router)
app.include_router(logs_router)


@app.exception_handler(RequestValidationError)
async def interceptar_erro_validacao(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Retorna detalhe estruturado de falhas de validação Pydantic (HTTP 422).
    Exemplo: acionado automaticamente pelo FastAPI em payloads inválidos.
    """
    logger.error(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )


def _resolver_arquivo_estatico_angular(full_path: str) -> Path:
    """Resolve o caminho do arquivo estático ou faz fallback para index.html (SPA)."""
    if full_path.startswith("api/"):
        raise HTTPException(
            status_code=404,
            detail=f"Invalid API route={full_path!r}; endpoint not registered.",
        )
    candidate = DIST_DIR / full_path
    if full_path and candidate.is_file():
        return candidate
    index_file = DIST_DIR / "index.html"
    if index_file.is_file():
        return index_file
    raise HTTPException(
        status_code=404,
        detail=f"Static bundle missing at {DIST_DIR}; run 'npm run build' in frontend/.",
    )


@app.get("/{full_path:path}")
async def servir_spa_angular(full_path: str) -> FileResponse:
    """
    Serve os artefatos estáticos compilados do Angular (monólito local).
    Exemplo: `GET /` -> `frontend/dist/frontend/browser/index.html`
    """
    target_file = _resolver_arquivo_estatico_angular(full_path)
    return FileResponse(target_file)
