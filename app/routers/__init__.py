"""Módulos de roteamento FastAPI separados por responsabilidade (SRP)."""
from app.routers.configs_router import router as configs_router
from app.routers.historico_router import router as historico_router
from app.routers.logs_router import router as logs_router
from app.routers.settings_router import router as settings_router

__all__ = [
    "configs_router",
    "historico_router",
    "logs_router",
    "settings_router",
]
