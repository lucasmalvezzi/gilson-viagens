import logging
from pathlib import Path
import tempfile
import unittest

from app.structured_log_store import StructuredLogCollector


class StructuredLogStoreTestSuite(unittest.TestCase):
    """Testes unitários F.I.R.S.T para o coletor de logs estruturados JSONL."""

    def setUp(self) -> None:
        """Cria um diretório temporário isolado para o arquivo JSONL de teste."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "test_scraper.log"
        self.collector = StructuredLogCollector(
            max_entries=50, log_file_path=self.log_path
        )

    def tearDown(self) -> None:
        """Remove o diretório temporário após cada teste."""
        self.temp_dir.cleanup()

    def _emit_sample_record(self, level: int, logger_name: str, msg: str) -> None:
        """Cria e emite um LogRecord sintético para o coletor sob teste."""
        record = logging.LogRecord(
            name=logger_name,
            level=level,
            pathname=__file__,
            lineno=10,
            msg=msg,
            args=(),
            exc_info=None,
        )
        self.collector.emit(record)

    def test_emite_e_consulta_logs_filtrados_por_nivel_e_busca(self) -> None:
        """Armazena entradas JSON e filtra por severidade e substring."""
        self._emit_sample_record(logging.INFO, "app.scraper", "Consultando GRU -> JPA")
        self._emit_sample_record(logging.ERROR, "app.scraper", "Falha ao ler REC")
        todos = self.collector.query_logs(level="ALL", limit=10)
        erros = self.collector.query_logs(level="ERROR", search="REC", limit=10)
        self.assertEqual(len(todos), 2)
        self.assertEqual(len(erros), 1)
        self.assertIn("REC", erros[0]["message"])

    def test_ignora_loggers_ruidosos_do_uvicorn_e_httpx(self) -> None:
        """Descarta logs internos do uvicorn.access e httpx."""
        self._emit_sample_record(logging.INFO, "uvicorn.access", "GET /api/logs 200")
        self._emit_sample_record(logging.INFO, "httpx", "HTTP Request POST")
        self.assertEqual(len(self.collector.query_logs()), 0)

    def test_restaura_historico_jsonl_do_disco_e_limpa(self) -> None:
        """Recarrega entradas persistidas em JSONL ao instanciar novo coletor e limpa."""
        self._emit_sample_record(logging.WARNING, "app.scraper", "Aviso persistido")
        novo_coletor = StructuredLogCollector(
            max_entries=50, log_file_path=self.log_path
        )
        self.assertEqual(len(novo_coletor.query_logs()), 1)
        novo_coletor.clear_logs()
        self.assertEqual(len(novo_coletor.query_logs()), 0)

    def test_rejeita_limit_invalido_com_valor_ofensivo(self) -> None:
        """Levanta ValueError descritivo quando limit <= 0."""
        with self.assertRaises(ValueError) as ctx:
            self.collector.query_logs(limit=0)
        self.assertIn("limit=0", str(ctx.exception))
