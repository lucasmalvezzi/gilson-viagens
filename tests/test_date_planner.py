from datetime import date
import unittest

from app.date_planner import calcular_estimativa_chamadas, gerar_datas_candidatas
from app.schemas import CallEstimateRequest


class DatePlannerTestSuite(unittest.TestCase):
    """Testes unitários F.I.R.S.T para planejamento de datas e estimativa de chamadas."""

    def test_gerar_datas_por_intervalo_passo_regular(self) -> None:
        """Gera pares de datas respeitando o passo de 3 dias no intervalo informado."""
        hoje = date(2026, 10, 1)
        datas = gerar_datas_candidatas(
            duracao_dias=5,
            data_inicio=date(2026, 10, 10),
            data_fim=date(2026, 10, 16),
            passo_dias=3,
            estrategia_busca="passo",
            referencia_hoje=hoje,
        )
        self.assertEqual(len(datas), 3)
        self.assertEqual(datas[0], (date(2026, 10, 10), date(2026, 10, 15)))
        self.assertEqual(datas[2], (date(2026, 10, 16), date(2026, 10, 21)))

    def test_gerar_datas_por_intervalo_apenas_fins_de_semana(self) -> None:
        """Filtra apenas sextas-feiras (4) e sábados (5) na estratégia fins_de_semana."""
        hoje = date(2026, 10, 1)
        datas = gerar_datas_candidatas(
            duracao_dias=4,
            data_inicio=date(2026, 10, 8),
            data_fim=date(2026, 10, 12),
            estrategia_busca="fins_de_semana",
            referencia_hoje=hoje,
        )
        self.assertEqual(len(datas), 2)
        self.assertIn(datas[0][0].weekday(), (4, 5))
        self.assertIn(datas[1][0].weekday(), (4, 5))

    def test_gerar_datas_por_mes_foco_retorna_sextas(self) -> None:
        """Gera sextas-feiras futuras dentro do mês de foco informado."""
        hoje = date(2026, 10, 1)
        datas = gerar_datas_candidatas(
            mes_foco=11, duracao_dias=7, referencia_hoje=hoje
        )
        self.assertGreaterEqual(len(datas), 4)
        self.assertEqual(datas[0][0].month, 11)
        self.assertEqual((datas[0][1] - datas[0][0]).days, 7)

    def test_rejeita_intervalo_invertido_com_mensagem_descritiva(self) -> None:
        """Levanta ValueError informando os valores ofensivos quando data_inicio > data_fim."""
        with self.assertRaises(ValueError) as ctx:
            gerar_datas_candidatas(
                data_inicio=date(2026, 12, 20),
                data_fim=date(2026, 12, 10),
            )
        self.assertIn("2026-12-20", str(ctx.exception))
        self.assertIn("expected data_inicio <= data_fim", str(ctx.exception))

    def test_rejeita_duracao_invalida_com_mensagem_descritiva(self) -> None:
        """Levanta ValueError quando duracao_dias é menor que 1."""
        with self.assertRaises(ValueError) as ctx:
            gerar_datas_candidatas(mes_foco=11, duracao_dias=0)
        self.assertIn("duracao_dias=0", str(ctx.exception))

    def test_calcular_estimativa_chamadas_retorna_amostras_e_tempo(self) -> None:
        """Calcula total de chamadas, tempo em segundos e amostras formatadas."""
        req = CallEstimateRequest(
            data_inicio=date(2026, 11, 1),
            data_fim=date(2026, 11, 10),
            duracao_dias=5,
            passo_dias=3,
            estrategia_busca="passo",
        )
        res = calcular_estimativa_chamadas(req, referencia_hoje=date(2026, 10, 1))
        self.assertEqual(res.total_chamadas, 4)
        self.assertEqual(res.tempo_estimado_segundos, 10)
        self.assertEqual(len(res.amostras), 4)
