import logging
from typing import Optional
from fastapi import APIRouter

from app.schemas import ActionMessageResponse, LogListResponse
from app.structured_log_store import scraper_log_collector

logger = logging.getLogger("flight_tracker")
router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=LogListResponse)
def obter_logs_scraper(
    level: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 300,
) -> LogListResponse:
    """
    Retorna os logs estruturados do webscraper filtrados por nível e busca textual.
    Exemplo: `GET /api/logs?level=INFO&limit=100`
    """
    entradas = scraper_log_collector.query_logs(
        level=level, search=search, limit=max(1, min(limit, 600))
    )
    return LogListResponse(total=len(entradas), logs=entradas)


@router.delete("", response_model=ActionMessageResponse)
def limpar_logs_scraper() -> ActionMessageResponse:
    """
    Limpa o buffer em memória e o arquivo de logs estruturados do scraper.
    Exemplo: `DELETE /api/logs`
    """
    scraper_log_collector.clear_logs()
    logger.info("Logs do console limpos pelo usuário.")
    return ActionMessageResponse(mensagem="Logs limpos com sucesso.")
