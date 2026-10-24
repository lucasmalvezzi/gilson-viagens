import unittest

from app.telegram_service import (
    enviar_alerta_preco,
    enviar_mensagem_telegram,
    formatar_mensagem_alerta_preco,
    testar_conexao_telegram,
)
from tests.fakes import FakeTelegramGateway, run_coroutine_synchronously


class TelegramServiceTestSuite(unittest.TestCase):
    """Testes unitários F.I.R.S.T para o serviço de notificações Telegram."""

    def test_formatar_mensagem_alerta_inclui_badge_voo_direto(self) -> None:
        """Gera HTML contendo os dados do trecho e badge de voo direto."""
        html = formatar_mensagem_alerta_preco(
            origem="VCP",
            destino="REC",
            data_ida="10/11/2026",
            data_volta="15/11/2026",
            valor_alvo=900.0,
            valor_encontrado=680.0,
            link_direto="https://www.google.com/travel/flights",
            apenas_direto=True,
        )
        self.assertIn("ALERTA DO GILSONVIAGENS", html)
        self.assertIn("Voo Direto (Sem escalas)", html)
        self.assertIn("680.00", html)

    def test_formatar_mensagem_rejeita_valor_negativo_ou_zero(self) -> None:
        """Levanta ValueError com o valor ofensivo quando valor_encontrado <= 0."""
        with self.assertRaises(ValueError) as ctx:
            formatar_mensagem_alerta_preco(
                "GRU", "JPA", "10/11", "15/11", 800.0, 0.0, "https://flights"
            )
        self.assertIn("valor_encontrado=0.0", str(ctx.exception))

    def test_enviar_alerta_preco_delega_para_fake_gateway(self) -> None:
        """Envia o alerta HTML usando FakeTelegramGateway e valida o destinatário."""
        fake_tg = FakeTelegramGateway(succeed=True)
        enviado = run_coroutine_synchronously(
            enviar_alerta_preco(
                bot_token="123:TOKEN",
                chat_id="987654",
                origem="GRU",
                destino="JPA",
                data_ida="10/11/2026",
                data_volta="15/11/2026",
                valor_alvo=800.0,
                valor_encontrado=599.0,
                link_direto="https://www.google.com/travel/flights",
                gateway=fake_tg,
            )
        )
        self.assertTrue(enviado)
        self.assertEqual(len(fake_tg.sent_messages), 1)
        self.assertEqual(fake_tg.sent_messages[0][1], "987654")

    def test_enviar_mensagem_retorna_false_sem_credenciais(self) -> None:
        """Retorna False imediatamente quando token ou chat_id estão vazios."""
        fake_tg = FakeTelegramGateway(succeed=True)
        resultado = run_coroutine_synchronously(
            enviar_mensagem_telegram("", "987654", "Oi", gateway=fake_tg)
        )
        self.assertFalse(resultado)
        self.assertEqual(len(fake_tg.sent_messages), 0)

    def test_testar_conexao_telegram_com_fake_gateway(self) -> None:
        """Valida o retorno estruturado de testar_conexao_telegram."""
        fake_tg = FakeTelegramGateway(succeed=True)
        res = run_coroutine_synchronously(
            testar_conexao_telegram("123:TOK", "999", gateway=fake_tg)
        )
        self.assertTrue(res["sucesso"])
        self.assertIn("sucesso", res["mensagem"].lower())
