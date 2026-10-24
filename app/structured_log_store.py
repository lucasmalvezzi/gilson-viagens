from collections import deque
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Deque, List, Optional

from app.schemas import StructuredLogEntry

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOG_FILE_PATH = BASE_DIR / "scraper.log"
IGNORED_LOGGER_PREFIXES = ("uvicorn.access", "httpcore", "httpx")


def _parse_json_log_line(raw_line: str) -> Optional[StructuredLogEntry]:
    """Converte uma linha JSONL do disco em StructuredLogEntry ou None se inválida."""
    cleaned = raw_line.strip()
    if not cleaned:
        return None
    try:
        parsed = json.loads(cleaned)
        return StructuredLogEntry(
            id=int(parsed.get("id", 0)),
            timestamp=str(parsed.get("timestamp", "")),
            level=str(parsed.get("level", "INFO")),
            logger=str(parsed.get("logger", "root")),
            message=str(parsed.get("message", ""))
        )
    except Exception:
        return None


def _matches_search_query(entry: StructuredLogEntry, query: Optional[str]) -> bool:
    """Verifica se a entrada de log contém o termo pesquisado no texto ou no logger."""
    if not query or not query.strip():
        return True
    normalized = query.strip().lower()
    return normalized in entry["message"].lower() or normalized in entry["logger"].lower()


class StructuredLogCollector(logging.Handler):
    """
    Coletor em anel (ring buffer) que grava e consulta logs em JSON estruturado.
    Exemplo: `collector = StructuredLogCollector(max_entries=600)`
    """

    def __init__(
        self,
        max_entries: int = 600,
        log_file_path: Path = DEFAULT_LOG_FILE_PATH
    ) -> None:
        super().__init__()
        self.entries: Deque[StructuredLogEntry] = deque(maxlen=max_entries)
        self.log_file_path: Path = log_file_path
        self._sequence_id: int = 0
        self._restore_recent_entries_from_disk()

    def _restore_recent_entries_from_disk(self) -> None:
        """Carrega até as últimas 300 linhas JSONL persistidas em disco."""
        if not self.log_file_path.exists():
            return
        try:
            lines = self.log_file_path.read_text(encoding="utf-8").splitlines()[-300:]
            self._append_parsed_lines(lines)
        except Exception:
            return

    def _append_parsed_lines(self, lines: List[str]) -> None:
        """Adiciona linhas JSONL válidas na fila em memória atualizando o contador."""
        for raw_line in lines:
            entry = _parse_json_log_line(raw_line)
            if entry is not None:
                self._sequence_id = max(self._sequence_id, entry["id"])
                self.entries.append(entry)

    def _persist_entry_to_disk(self, entry: StructuredLogEntry) -> None:
        """Persiste uma entrada em formato JSON estruturado (JSONL) no arquivo de log."""
        try:
            serialized = json.dumps(entry, ensure_ascii=False) + "\n"
            with open(self.log_file_path, "a", encoding="utf-8") as log_stream:
                log_stream.write(serialized)
        except Exception:
            return

    def emit(self, record: logging.LogRecord) -> None:
        """
        Recebe um LogRecord do Python e registra como JSON estruturado.
        Exemplo: `logger.info("Mensagem de diagnóstico")`
        """
        if record.name.startswith(IGNORED_LOGGER_PREFIXES):
            return
        self._sequence_id += 1
        entry = StructuredLogEntry(
            id=self._sequence_id,
            timestamp=datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage()
        )
        self.entries.append(entry)
        self._persist_entry_to_disk(entry)

    def query_logs(
        self,
        level: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 300
    ) -> List[StructuredLogEntry]:
        """
        Filtra os logs estruturados por nível e texto de busca.
        Exemplo: `collector.query_logs(level="ERROR", search="GRU", limit=50)`
        """
        if limit <= 0:
            raise ValueError(f"Invalid limit={limit}; expected positive integer > 0.")
        items = list(self.entries)
        if level and level.upper() != "ALL":
            target_level = level.upper()
            items = [item for item in items if item["level"] == target_level]
        items = [item for item in items if _matches_search_query(item, search)]
        return items[-limit:]

    def clear_logs(self) -> None:
        """
        Remove todos os registros de log da memória e trunca o arquivo em disco.
        Exemplo: `collector.clear_logs()`
        """
        self.entries.clear()
        if self.log_file_path.exists():
            self.log_file_path.write_text("", encoding="utf-8")


scraper_log_collector = StructuredLogCollector(max_entries=600)


def activar_coletor_estruturado(
    collector: StructuredLogCollector = scraper_log_collector
) -> None:
    """
    Registra o coletor de logs estruturados no root logger da aplicação.
    Exemplo: `activar_coletor_estruturado(scraper_log_collector)`
    """
    root_logger = logging.getLogger()
    if collector not in root_logger.handlers:
        root_logger.addHandler(collector)
    root_logger.setLevel(logging.INFO)
