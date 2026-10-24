import csv
import io
import logging
import subprocess
from typing import List, Protocol

from app.schemas import WindowsScheduledTaskEntry

logger = logging.getLogger(__name__)
TASK_NAME_PREFIX = "GilsonViagens_Busca_"


class OsSchedulerGatewayProtocol(Protocol):
    """Interface enxuta do projeto para gerenciar tarefas no agendador nativo do SO."""

    def register_daily_task(
        self, task_name: str, horario_hh_mm: str, command_line: str
    ) -> bool:
        """Cria ou substitui uma tarefa diária no agendador do sistema operacional."""
        ...

    def delete_task(self, task_name: str) -> bool:
        """Remove uma tarefa agendada pelo nome."""
        ...

    def list_project_tasks(
        self, prefix: str = TASK_NAME_PREFIX
    ) -> List[WindowsScheduledTaskEntry]:
        """Lista todas as tarefas registradas com o prefixo do projeto."""
        ...


def _parse_schtasks_csv_row(
    row: List[str], prefix: str
) -> WindowsScheduledTaskEntry | None:
    """Extrai WindowsScheduledTaskEntry de uma linha CSV do comando schtasks /Query."""
    if len(row) < 3:
        return None
    raw_name = row[0].strip().lstrip("\\")
    if not raw_name.startswith(prefix):
        return None
    return WindowsScheduledTaskEntry(
        task_name=raw_name,
        proximo_disparo=row[1].strip(),
        status=row[2].strip(),
    )


def _executar_comando_schtasks(args: List[str]) -> subprocess.CompletedProcess[str]:
    """Executa schtasks.exe de forma silenciosa sem abrir janela de console extra."""
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        creationflags=creation_flags,
    )


class WindowsTaskSchedulerGateway:
    """
    Adaptador concreto para o Agendador de Tarefas do Windows (`schtasks.exe`).
    Exemplo: `WindowsTaskSchedulerGateway().register_daily_task("GilsonViagens_Busca_1_0900", "09:00", cmd)`
    """

    def register_daily_task(
        self, task_name: str, horario_hh_mm: str, command_line: str
    ) -> bool:
        """
        Registra ou atualiza (`/F`) uma tarefa diária no Windows Task Scheduler.
        Exemplo: `gateway.register_daily_task("GilsonViagens_Busca_1_0900", "09:00", "python ...")`
        """
        if not task_name or not command_line:
            raise ValueError(
                f"Invalid task_name={task_name!r} or command_line={command_line!r}; expected non-empty strings."
            )
        args = [
            "schtasks", "/Create", "/SC", "DAILY",
            "/TN", task_name, "/TR", command_line,
            "/ST", horario_hh_mm, "/F",
        ]
        try:
            proc = _executar_comando_schtasks(args)
            return proc.returncode == 0
        except Exception as exc:
            logger.warning(f"Não foi possível registrar tarefa {task_name} no Windows: {exc}")
            return False

    def delete_task(self, task_name: str) -> bool:
        """
        Remove uma tarefa do Agendador do Windows pelo nome exato.
        Exemplo: `gateway.delete_task("GilsonViagens_Busca_1_0900")`
        """
        if not task_name:
            raise ValueError(f"Invalid task_name={task_name!r}; expected non-empty string.")
        try:
            proc = _executar_comando_schtasks(["schtasks", "/Delete", "/TN", task_name, "/F"])
            return proc.returncode == 0
        except Exception as exc:
            logger.warning(f"Não foi possível remover tarefa {task_name}: {exc}")
            return False

    def list_project_tasks(
        self, prefix: str = TASK_NAME_PREFIX
    ) -> List[WindowsScheduledTaskEntry]:
        """
        Consulta `schtasks /Query /FO CSV /NH` e filtra as tarefas do GilsonViagens.
        Exemplo: `tarefas = gateway.list_project_tasks()`
        """
        try:
            proc = _executar_comando_schtasks(["schtasks", "/Query", "/FO", "CSV", "/NH"])
            if proc.returncode != 0:
                return []
            return self._filtrar_saida_csv(proc.stdout, prefix)
        except Exception:
            return []

    def _filtrar_saida_csv(
        self, csv_stdout: str, prefix: str
    ) -> List[WindowsScheduledTaskEntry]:
        """Converte a saída CSV do schtasks em lista tipada de tarefas do projeto."""
        leitor = csv.reader(io.StringIO(csv_stdout))
        encontradas: List[WindowsScheduledTaskEntry] = []
        for linha in leitor:
            item = _parse_schtasks_csv_row(linha, prefix)
            if item is not None:
                encontradas.append(item)
        return encontradas
