from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ConfiguracaoSistema
from app.os_schedule_sync import (
    consultar_status_agendador_windows,
    remover_todas_tarefas_windows,
    sincronizar_tarefas_windows_banco,
)
from app.scheduler import (
    _obter_ou_criar_config_sistema,
    reconfigurar_agendador,
    rotina_diaria_de_buscas,
)
from app.schemas import (
    ActionMessageResponse,
    SettingsBase,
    SettingsResponse,
    TelegramTestResult,
    TestTelegramRequest,
    WindowsSchedulerStatusResponse,
)
from app.telegram_service import testar_conexao_telegram

router = APIRouter(tags=["settings"])


def _atualizar_campos_sistema(
    config_sis: ConfiguracaoSistema, payload: SettingsBase
) -> None:
    """Atualiza token, chat_id e horário de execução no registro de sistema."""
    if payload.telegram_bot_token is not None:
        config_sis.telegram_bot_token = payload.telegram_bot_token.strip()
    if payload.telegram_chat_id is not None:
        config_sis.telegram_chat_id = payload.telegram_chat_id.strip()
    if payload.horario_execucao is not None:
        config_sis.horario_execucao = payload.horario_execucao.strip()
        reconfigurar_agendador(config_sis.horario_execucao)


def _resolver_credenciais_telegram(
    payload: TestTelegramRequest, db: Session
) -> tuple[Optional[str], Optional[str]]:
    """Obtém token e chat_id do payload ou faz fallback para o salvo no banco."""
    if payload.token and payload.chat_id:
        return payload.token, payload.chat_id
    config_sis = db.query(ConfiguracaoSistema).first()
    if not config_sis:
        return payload.token, payload.chat_id
    return (
        payload.token or config_sis.telegram_bot_token,
        payload.chat_id or config_sis.telegram_chat_id,
    )


@router.get("/api/settings", response_model=SettingsResponse)
def obter_configuracoes(db: Session = Depends(get_db)) -> SettingsResponse:
    """
    Retorna as configurações globais do sistema (Telegram e horário do agendador).
    Exemplo: `GET /api/settings`
    """
    config_sis = _obter_ou_criar_config_sistema(db)
    return SettingsResponse.model_validate(config_sis)


@router.post("/api/settings", response_model=SettingsResponse)
def salvar_configuracoes(
    payload: SettingsBase, db: Session = Depends(get_db)
) -> SettingsResponse:
    """
    Salva as configurações globais e reconfigura o cronjob diário.
    Exemplo: `POST /api/settings {"horario_execucao": "08:30"}`
    """
    config_sis = _obter_ou_criar_config_sistema(db)
    _atualizar_campos_sistema(config_sis, payload)
    db.commit()
    db.refresh(config_sis)
    return SettingsResponse.model_validate(config_sis)


@router.post("/api/settings/test-telegram", response_model=TelegramTestResult)
async def testar_telegram(
    payload: TestTelegramRequest, db: Session = Depends(get_db)
) -> TelegramTestResult:
    """
    Envia uma mensagem de teste para validar o Bot Token e o Chat ID do Telegram.
    Exemplo: `POST /api/settings/test-telegram {"token": "...", "chat_id": "..."}`
    """
    token, chat_id = _resolver_credenciais_telegram(payload, db)
    return await testar_conexao_telegram(token, chat_id)


@router.get(
    "/api/settings/windows-scheduler",
    response_model=WindowsSchedulerStatusResponse,
)
def obter_status_agendador_windows() -> WindowsSchedulerStatusResponse:
    """
    Consulta as tarefas do GilsonViagens registradas no Agendador do Windows.
    Exemplo: `GET /api/settings/windows-scheduler`
    """
    return consultar_status_agendador_windows()


@router.post(
    "/api/settings/windows-scheduler/sync",
    response_model=WindowsSchedulerStatusResponse,
)
def sincronizar_agendador_windows(
    db: Session = Depends(get_db),
) -> WindowsSchedulerStatusResponse:
    """
    Sincroniza todas as buscas ativas com o Agendador de Tarefas do Windows (`schtasks`).
    Exemplo: `POST /api/settings/windows-scheduler/sync`
    """
    return sincronizar_tarefas_windows_banco(db)


@router.delete(
    "/api/settings/windows-scheduler",
    response_model=ActionMessageResponse,
)
def limpar_agendador_windows() -> ActionMessageResponse:
    """
    Remove todas as tarefas do GilsonViagens do Agendador de Tarefas do Windows.
    Exemplo: `DELETE /api/settings/windows-scheduler`
    """
    removidas = remover_todas_tarefas_windows()
    return ActionMessageResponse(
        mensagem=f"{removidas} tarefa(s) removida(s) do Agendador do Windows."
    )


@router.post("/api/executar-tudo", response_model=ActionMessageResponse)
async def executar_todas_as_buscas(
    background_tasks: BackgroundTasks,
) -> ActionMessageResponse:
    """
    Dispara a rotina completa de buscas ativas em segundo plano.
    Exemplo: `POST /api/executar-tudo`
    """
    background_tasks.add_task(rotina_diaria_de_buscas)
    return ActionMessageResponse(
        mensagem="Rotina diária de buscas disparada em segundo plano!"
    )
