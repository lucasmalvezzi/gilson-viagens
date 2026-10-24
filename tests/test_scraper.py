from datetime import date
import unittest

from app.scraper import (
    buscar_menor_preco,
    construir_url_busca,
    extrair_menor_preco_de_elementos,
    extrair_menor_valor_de_texto,
)
from tests.fakes import FakeBrowserGateway, run_coroutine_synchronously


class ScraperTestSuite(unittest.TestCase):
    """Testes unitários F.I.R.S.T para o raspador de voos usando FakeBrowserGateway."""

    def test_construir_url_busca_com_e_sem_voo_direto(self) -> None:
        """Monta a URL parametrizada do Google Flights em BRL."""
        url = construir_url_busca(
            "gru", "jpa", date(2026, 11, 10), date(2026, 11, 15), apenas_direto=True
        )
        self.assertIn("nonstop%20Flights%20to%20JPA%20from%20GRU", url)
        self.assertIn("curr=BRL", url)

    def test_rejeita_codigo_aeroporto_invalido_com_mensagem_descritiva(self) -> None:
        """Levanta ValueError indicando o valor ofensivo quando origem é vazia."""
        with self.assertRaises(ValueError) as ctx:
            construir_url_busca("", "JPA", date(2026, 11, 10), date(2026, 11, 15))
        self.assertIn("Invalid origem=''", str(ctx.exception))

    def test_extrair_menor_valor_de_texto_filtra_valores_fora_da_faixa(self) -> None:
        """Extrai o menor valor em Reais ignorando números absurdos (< 50 ou > 80000)."""
        texto = "Taxa R$ 12,00 | Voo 1: R$ 1.450,50 | Voo 2: R$ 890 | Erro: R$ 99.999"
        menor = extrair_menor_valor_de_texto(texto)
        self.assertEqual(menor, 890.0)

    def test_extrair_menor_preco_de_elementos_descarta_escalas_quando_direto(self) -> None:
        """Ignora cards listitem que mencionam parada/escala quando apenas_direto=True."""
        itens = [
            "LATAM · 1 parada · R$ 520,00",
            "Azul · Voo direto sem escalas · R$ 740,00",
        ]
        preco_direto = extrair_menor_preco_de_elementos(itens, "", apenas_direto=True)
        preco_qualquer = extrair_menor_preco_de_elementos(itens, "", apenas_direto=False)
        self.assertEqual(preco_direto, 740.0)
        self.assertEqual(preco_qualquer, 520.0)

    def test_buscar_menor_preco_usa_fake_gateway_injetado(self) -> None:
        """Executa a varredura completa usando FakeBrowserGateway sem abrir navegador real."""
        fake_browser = FakeBrowserGateway(
            listitem_texts=["GOL · Voo direto · R$ 615,00"]
        )
        cotacao = run_coroutine_synchronously(
            buscar_menor_preco(
                origem="GRU",
                destino="JPA",
                duracao_dias=5,
                apenas_direto=True,
                data_inicio=date(2099, 5, 1),
                data_fim=date(2099, 5, 4),
                passo_dias=3,
                browser_gateway=fake_browser,
                pausa_segundos=0.0,
            )
        )
        self.assertIsNotNone(cotacao)
        assert cotacao is not None
        self.assertEqual(cotacao["valor"], 615.0)
        self.assertEqual(len(fake_browser.visited_urls), 2)
