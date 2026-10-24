import unittest

from app.models import ConfigBusca
from app.os_schedule_sync import (
    construir_comando_standalone_busca,
    extrair_lista_horarios_validos,
    normalizar_horarios_csv,
    remover_todas_tarefas_windows,
    sincronizar_tarefas_windows_banco,
)
from tests.fakes import FakeOsSchedulerGateway, InMemorySqliteDatabase


class OsScheduleSyncTestSuite(unittest.TestCase):
    """Testes unitários F.I.R.S.T para horários por busca e agendador do Windows."""

    def setUp(self) -> None:
        """Cria banco SQLite em memória e fake do agendador do Windows."""
        self.mem_db = InMemorySqliteDatabase()
        self.fake_os = FakeOsSchedulerGateway()

    def tearDown(self) -> None:
        """Fecha conexões do banco em memória."""
        self.mem_db.dispose()

    def test_extrair_e_normalizar_multiplos_horarios_por_busca(self) -> None:
        """Extrai múltiplos horários HH:MM sem duplicatas e normaliza string CSV."""
        pares = extrair_lista_horarios_validos("8:05, 19:30, 08:05")
        self.assertEqual(pares, [(8, 5), (19, 30)])
        normalizado = normalizar_horarios_csv("8:05, 19:30")
        self.assertEqual(normalizado, "08:05, 19:30")

    def test_construir_comando_standalone_inclui_script_e_argumento(self) -> None:
        """Gera comando CLI apontando para run_scheduled_search.py com --config-id."""
        cmd_individual = construir_comando_standalone_busca(7)
        cmd_todas = construir_comando_standalone_busca(None)
        self.assertIn("run_scheduled_search.py", cmd_individual)
        self.assertIn("--config-id 7", cmd_individual)
        self.assertIn("--all", cmd_todas)

    def test_sincronizar_e_remover_tarefas_windows_por_busca_ativa(self) -> None:
        """Registra uma tarefa por horário de cada busca ativa e limpa sob demanda."""
        db = self.mem_db.create_session()
        try:
            db.add(
                ConfigBusca(
                    origem="GRU",
                    destino="JPA",
                    mes_foco=11,
                    valor_alvo=700.0,
                    horarios_execucao="07:00, 19:00",
                    agendar_no_windows=True,
                    ativa=True,
                )
            )
            db.commit()
            status = sincronizar_tarefas_windows_banco(db, gateway=self.fake_os)
            self.assertEqual(status.total_tarefas, 2)
            removidas = remover_todas_tarefas_windows(gateway=self.fake_os)
            self.assertEqual(removidas, 2)
        finally:
            db.close()
