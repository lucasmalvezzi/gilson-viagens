from pathlib import Path
import sys
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.gateways.os_scheduler_gateway import (
    OsSchedulerGatewayProtocol,
    TASK_NAME_PREFIX,
    WindowsTaskSchedulerGateway,
)
from app.models import ConfigBusca
from app.schemas import WindowsSchedulerStatusResponse

BASE_DIR = Path(__file__).resolve().parent.parent
RUNNER_SCRIPT_PATH = BASE_DIR / "run_scheduled_search.py"


def get_os_scheduler_gateway() -> OsSchedulerGatewayProtocol:
    """
    Provedor de injeção de dependência FastAPI para o agendador do sistema operacional.
    Exemplo: `os_gateway: OsSchedulerGatewayProtocol = Depends(get_os_scheduler_gateway)`
    """
    return WindowsTaskSchedulerGateway()


def parse_horario_hh_mm(horario_hh_mm: str) -> Tuple[int, int]:
    """
    Valida e separa uma string 'HH:MM' em tupla (hora, minuto).
    Exemplo: `parse_horario_hh_mm("09:30")` -> `(9, 30)`
    """
    partes = (horario_hh_mm or "").strip().split(":")
    if len(partes) != 2 or not partes[0].isdigit() or not partes[1].isdigit():
        raise ValueError(
            f"Invalid horario_hh_mm={horario_hh_mm!r}; expected 'HH:MM' (00:00..23:59)."
        )
    hora, minuto = int(partes[0]), int(partes[1])
    if not (0 <= hora <= 23 and 0 <= minuto <= 59):
        raise ValueError(
            f"Invalid horario_hh_mm={horario_hh_mm!r}; expected hour 0..23 and minute 0..59."
        )
    return hora, minuto


def extrair_lista_horarios_validos(horarios_str: Optional[str]) -> List[Tuple[int, int]]:
    """
    Extrai um ou mais horários 'HH:MM' separados por vírgula sem duplicatas.
    Exemplo: `extrair_lista_horarios_validos("08:00, 18:30")` -> `[(8, 0), (18, 30)]`
    """
    bruto = (horarios_str or "09:00").strip()
    if not bruto:
        return [(9, 0)]
    partes = [p.strip() for p in bruto.split(",") if p.strip()]
    vistos: List[Tuple[int, int]] = []
    for item in partes:
        par = parse_horario_hh_mm(item)
        if par not in vistos:
            vistos.append(par)
    return vistos if vistos else [(9, 0)]


def normalizar_horarios_csv(horarios_str: Optional[str]) -> str:
    """
    Normaliza string de horários separados por vírgula para formato canônico 'HH:MM, HH:MM'.
    Exemplo: `normalizar_horarios_csv("8:00, 20:00")` -> `"08:00, 20:00"`
    """
    pares = extrair_lista_horarios_validos(horarios_str)
    return ", ".join(f"{h:02d}:{m:02d}" for h, m in pares)


def _resolver_executavel_python_background() -> Path:
    """Prefere pythonw.exe no venv do Windows para rodar em 2º plano sem abrir janela."""
    venv_scripts = BASE_DIR / "venv" / "Scripts"
    pythonw = venv_scripts / "pythonw.exe"
    if pythonw.exists():
        return pythonw
    python_exe = venv_scripts / "python.exe"
    if python_exe.exists():
        return python_exe
    return Path(sys.executable)


def construir_comando_standalone_busca(config_id: Optional[int] = None) -> str:
    """
    Monta a linha de comando standalone que roda sem precisar do servidor FastAPI ativo.
    Exemplo: `construir_comando_standalone_busca(1)`
    """
    python_bin = _resolver_executavel_python_background()
    alvo_arg = f"--config-id {config_id}" if config_id is not None else "--all"
    return f'"{python_bin}" "{RUNNER_SCRIPT_PATH}" {alvo_arg}'


def remover_todas_tarefas_windows(
    gateway: Optional[OsSchedulerGatewayProtocol] = None,
) -> int:
    """
    Remove todas as tarefas `GilsonViagens_Busca_*` registradas no Windows Task Scheduler.
    Exemplo: `removidas = remover_todas_tarefas_windows()`
    """
    adaptador = gateway or WindowsTaskSchedulerGateway()
    existentes = adaptador.list_project_tasks(TASK_NAME_PREFIX)
    removidas = 0
    for item in existentes:
        if adaptador.delete_task(item["task_name"]):
            removidas += 1
    return removidas


def _registrar_horarios_da_config_no_windows(
    cfg: ConfigBusca, adaptador: OsSchedulerGatewayProtocol
) -> int:
    """Registra no Windows uma tarefa diária para cada horário configurado na busca."""
    horarios = extrair_lista_horarios_validos(cfg.horarios_execucao)
    cmd = construir_comando_standalone_busca(cfg.id)
    criadas = 0
    for hora, minuto in horarios:
        nome_tarefa = f"{TASK_NAME_PREFIX}{cfg.id}_{hora:02d}{minuto:02d}"
        horario_fmt = f"{hora:02d}:{minuto:02d}"
        if adaptador.register_daily_task(nome_tarefa, horario_fmt, cmd):
            criadas += 1
    return criadas


def sincronizar_tarefas_windows_banco(
    db: Session,
    gateway: Optional[OsSchedulerGatewayProtocol] = None,
) -> WindowsSchedulerStatusResponse:
    """
    Sincroniza todas as buscas ativas (`agendar_no_windows=True`) com o Agendador do Windows.
    Exemplo: `status = sincronizar_tarefas_windows_banco(db)`
    """
    adaptador = gateway or WindowsTaskSchedulerGateway()
    remover_todas_tarefas_windows(adaptador)
    ativas = (
        db.query(ConfigBusca)
        .filter(ConfigBusca.ativa == True, ConfigBusca.agendar_no_windows == True)
        .all()
    )
    for cfg in ativas:
        _registrar_horarios_da_config_no_windows(cfg, adaptador)
    return consultar_status_agendador_windows(adaptador)


def consultar_status_agendador_windows(
    gateway: Optional[OsSchedulerGatewayProtocol] = None,
) -> WindowsSchedulerStatusResponse:
    """
    Retorna as tarefas ativas no Windows Task Scheduler e o comando standalone de execução.
    Exemplo: `status = consultar_status_agendador_windows()`
    """
    adaptador = gateway or WindowsTaskSchedulerGateway()
    tarefas = adaptador.list_project_tasks(TASK_NAME_PREFIX)
    cmd_exemplo = construir_comando_standalone_busca(None)
    return WindowsSchedulerStatusResponse(
        suportado=True,
        total_tarefas=len(tarefas),
        comando_standalone=cmd_exemplo,
        tarefas=tarefas,
        mensagem=(
            f"{len(tarefas)} agendamento(s) ativo(s) no Windows (rodam sem o servidor aberto)."
        ),
    )
