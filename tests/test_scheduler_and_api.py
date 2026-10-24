from datetime import date
import unittest

from app.models import ConfigBusca, ConfiguracaoSistema
from app.routers.configs_router import (
    alternar_status_config,
    atualizar_config,
    criar_config,
    deletar_config,
    listar_configs,
)
from app.routers.historico_router import listar_historico
from app.scheduler import (
    _parse_horario_hh_mm,
    executar_busca_para_config,
    rotina_diaria_de_buscas,
)
from app.schemas import ConfigBuscaCreate, ConfigBuscaUpdate, LowestPriceQuote
from tests.fakes import (
    FakeAlertSender,
    FakeOsSchedulerGateway,
    FakePriceFinder,
    InMemorySqliteDatabase,
    run_coroutine_synchronously,
)


class SchedulerAndApiTestSuite(unittest.TestCase):
    """Testes unitários e de regressão F.I.R.S.T com SQLite em memória e Fakes nomeados."""

    def setUp(self) -> None:
        """Inicializa banco SQLite em memória e fake do agendador do Windows."""
        self.mem_db = InMemorySqliteDatabase()
        self.fake_os = FakeOsSchedulerGateway()

    def tearDown(self) -> None:
        """Descarta conexões do banco em memória ao final do teste."""
        self.mem_db.dispose()

    def test_regressao_criar_e_editar_config_com_intervalo_sem_mes_foco(self) -> None:
        """Regressão: permite salvar intervalo personalizado com mes_foco=None e editar."""
        db = self.mem_db.create_session()
        try:
            payload = ConfigBuscaCreate(
                origem="vcp",
                destino="jpa",
                mes_foco=None,
                data_inicio=date(2026, 11, 10),
                data_fim=date(2026, 11, 25),
                passo_dias=3,
                estrategia_busca="passo",
                duracao_dias=6,
                valor_alvo=850.0,
                apenas_direto=True,
                horarios_execucao="08:00, 20:00",
                agendar_no_windows=True,
                ativa=True,
            )
            criada = criar_config(payload, db=db, os_gateway=self.fake_os)
            self.assertEqual(criada.origem, "VCP")
            self.assertIsNone(criada.mes_foco)
            self.assertEqual(criada.horarios_execucao, "08:00, 20:00")
            self.assertEqual(len(self.fake_os.list_project_tasks()), 2)

            atualizada = atualizar_config(
                criada.id,
                ConfigBuscaUpdate(valor_alvo=720.0, horarios_execucao="09:00, 14:00, 21:00"),
                db=db,
                os_gateway=self.fake_os,
            )
            self.assertEqual(atualizada.valor_alvo, 720.0)
            self.assertEqual(len(self.fake_os.list_project_tasks()), 3)
        finally:
            db.close()

    def test_toggle_listagem_e_exclusao_de_config(self) -> None:
        """Verifica alternância de status ativo, listagem enriquecida e exclusão."""
        db = self.mem_db.create_session()
        try:
            criada = criar_config(
                ConfigBuscaCreate(origem="GRU", destino="REC", mes_foco=10, valor_alvo=600.0),
                db=db,
                os_gateway=self.fake_os,
            )
            pausada = alternar_status_config(
                criada.id, db=db, os_gateway=self.fake_os
            )
            self.assertFalse(pausada.ativa)
            self.assertEqual(len(self.fake_os.list_project_tasks()), 0)
            self.assertEqual(len(listar_configs(db=db)), 1)
            deletar_config(criada.id, db=db, os_gateway=self.fake_os)
            self.assertEqual(len(listar_configs(db=db)), 0)
        finally:
            db.close()

    def test_executar_busca_salva_historico_e_dispara_alerta(self) -> None:
        """Verifica que executar_busca_para_config grava histórico e aciona FakeAlertSender."""
        db = self.mem_db.create_session()
        db.add(
            ConfiguracaoSistema(
                id=1, telegram_bot_token="123:TOK", telegram_chat_id="999"
            )
        )
        cfg = ConfigBusca(
            origem="GRU", destino="REC", mes_foco=11, duracao_dias=5, valor_alvo=700.0
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
        cfg_id = cfg.id
        db.close()

        cotacao = LowestPriceQuote(
            valor=550.0,
            data_ida=date(2026, 11, 10),
            data_volta=date(2026, 11, 15),
            link_direto="https://www.google.com/travel/flights",
            apenas_direto=False,
        )
        alerter = FakeAlertSender(succeed=True)
        res = run_coroutine_synchronously(
            executar_busca_para_config(
                cfg_id,
                session_factory=self.mem_db.create_session,
                price_finder=FakePriceFinder(quote=cotacao),
                alert_sender=alerter,
            )
        )
        self.assertEqual(res.menor_valor, 550.0)
        self.assertTrue(res.alerta_enviado)
        self.assertEqual(alerter.alerts_sent, 1)

        db_check = self.mem_db.create_session()
        self.assertEqual(len(listar_historico(id_busca=str(cfg_id), db=db_check)), 1)
        db_check.close()

    def test_rotina_diaria_atualiza_status_e_valida_horario(self) -> None:
        """Executa rotina_diaria_de_buscas com Fakes e valida parser de horário."""
        status_final = run_coroutine_synchronously(
            rotina_diaria_de_buscas(
                session_factory=self.mem_db.create_session,
                price_finder=FakePriceFinder(quote=None),
                alert_sender=FakeAlertSender(succeed=True),
                pausa_segundos=0.0,
            )
        )
        self.assertIn("Concluída com sucesso", status_final)
        with self.assertRaises(ValueError) as ctx:
            _parse_horario_hh_mm("25:99")
        self.assertIn("25:99", str(ctx.exception))
