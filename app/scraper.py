import asyncio
from datetime import date
import logging
import random
import re
from typing import List, Optional, Tuple

from app.date_planner import gerar_datas_candidatas
from app.gateways.browser_gateway import (
    FlightBrowserGatewayProtocol,
    PlaywrightStealthGateway,
)
from app.schemas import LowestPriceQuote

logger = logging.getLogger(__name__)

# Regex para capturar R$ 1.250, R$ 500, R$ 450,00, R$ 1.200,50
BRL_PRICE_PATTERN = re.compile(r"R\$\s*([\d\.]+(?:,\d{2})?)")
LAYOVER_TERMS = ("parada", "paradas", "stop", "stops", "escala")
NONSTOP_TERMS = ("direto", "sem escalas", "nonstop")


def _validar_codigo_aeroporto(codigo: str, nome_campo: str) -> str:
    """Valida que o código IATA ou cidade possui entre 2 e 10 caracteres."""
    limpo = (codigo or "").strip().upper()
    if len(limpo) < 2 or len(limpo) > 10:
        raise ValueError(
            f"Invalid {nome_campo}={codigo!r}; expected IATA/city string with 2..10 chars."
        )
    return limpo


def construir_url_busca(
    origem: str,
    destino: str,
    data_ida: date,
    data_volta: date,
    apenas_direto: bool = False,
) -> str:
    """
    Monta a URL direta do Google Flights sem interação com inputs de UI.
    Exemplo: `construir_url_busca("GRU", "JPA", date(2026, 11, 10), date(2026, 11, 15))`
    """
    orig = _validar_codigo_aeroporto(origem, "origem")
    dest = _validar_codigo_aeroporto(destino, "destino")
    ida_str = data_ida.strftime("%Y-%m-%d")
    volta_str = data_volta.strftime("%Y-%m-%d")
    prefixo_direto = "nonstop%20" if apenas_direto else ""
    return (
        f"https://www.google.com/travel/flights?q={prefixo_direto}Flights%20to%20{dest}"
        f"%20from%20{orig}%20on%20{ida_str}%20through%20{volta_str}&curr=BRL"
    )


def _converter_moeda_br_para_float(valor_br: str) -> Optional[float]:
    """Converte string brasileira (ex: '1.250,50') para float dentro da faixa de sanidade."""
    try:
        # Converte formato brasileiro para float padrão
        valor_float = float(valor_br.replace(".", "").replace(",", "."))
    except ValueError:
        return None
    # Filtro de sanidade: passagens válidas geralmente entre R$ 50 e R$ 80.000
    return valor_float if 50.0 <= valor_float <= 80000.0 else None


def extrair_menor_valor_de_texto(texto: str) -> Optional[float]:
    """
    Localiza padrões de preço em Real (R$ 1.234 ou R$ 500) usando Regex Semântico.
    Exemplo: `extrair_menor_valor_de_texto("Voo direto por R$ 1.250,00 ida e volta")`
    """
    if not texto:
        return None
    matches = BRL_PRICE_PATTERN.findall(texto)
    valores = [_converter_moeda_br_para_float(m) for m in matches]
    validos = [v for v in valores if v is not None]
    return min(validos) if validos else None


def _item_possui_escala_indesejada(texto_item: str, apenas_direto: bool) -> bool:
    """Se a busca exige apenas voos diretos, descarta opções com paradas/escalas."""
    if not apenas_direto:
        return False
    minusculo = texto_item.lower()
    tem_parada = any(termo in minusculo for termo in LAYOVER_TERMS)
    eh_direto = any(termo in minusculo for termo in NONSTOP_TERMS)
    return tem_parada and not eh_direto


def extrair_menor_preco_de_elementos(
    textos_listitem: List[str],
    html_completo: str,
    apenas_direto: bool = False,
) -> Optional[float]:
    """
    Aplica filtro de voos diretos nos listitems ARIA (Regra 5.3) e fallback semântico.
    Exemplo: `extrair_menor_preco_de_elementos(["Voo direto R$ 650"], "", True)`
    """
    precos: List[float] = []
    for item_txt in textos_listitem:
        if _item_possui_escala_indesejada(item_txt, apenas_direto):
            continue
        preco = extrair_menor_valor_de_texto(item_txt)
        if preco is not None:
            precos.append(preco)
    if precos:
        return min(precos)
    # Fallback Semântico: se os listitems não trouxeram dados, analisa o HTML bruto
    if not apenas_direto and html_completo:
        return extrair_menor_valor_de_texto(html_completo)
    return None


async def _consultar_janela_de_data(
    gateway: FlightBrowserGatewayProtocol,
    origem: str,
    destino: str,
    dt_ida: date,
    dt_volta: date,
    apenas_direto: bool,
) -> Optional[LowestPriceQuote]:
    """Consulta uma única janela (ida, volta) no gateway e retorna cotação se houver."""
    url = construir_url_busca(origem, destino, dt_ida, dt_volta, apenas_direto)
    try:
        item_texts, raw_html = await gateway.fetch_rendered_flight_texts(url)
    except Exception as exc:
        logger.error(f"[{origem}->{destino}] Erro ao consultar {url}: {exc}")
        return None
    preco = extrair_menor_preco_de_elementos(item_texts, raw_html, apenas_direto)
    if preco is None:
        return None
    return LowestPriceQuote(
        valor=preco,
        data_ida=dt_ida,
        data_volta=dt_volta,
        link_direto=url,
        apenas_direto=apenas_direto,
    )


def _selecionar_menor_cotacao(
    atual: Optional[LowestPriceQuote], nova: Optional[LowestPriceQuote]
) -> Optional[LowestPriceQuote]:
    """Retorna a cotação de menor valor entre a cotação acumulada e a recém-extraída."""
    if nova is None:
        return atual
    if atual is None or nova["valor"] < atual["valor"]:
        return nova
    return atual


async def _varrer_janelas_candidatas(
    gateway: FlightBrowserGatewayProtocol,
    origem: str,
    destino: str,
    datas: List[Tuple[date, date]],
    apenas_direto: bool,
    pausa_entre_buscas: float,
) -> Optional[LowestPriceQuote]:
    """Itera pelas janelas candidatas e acumula a menor cotação encontrada."""
    melhor: Optional[LowestPriceQuote] = None
    for idx, (dt_ida, dt_volta) in enumerate(datas, start=1):
        cotacao = await _consultar_janela_de_data(
            gateway, origem, destino, dt_ida, dt_volta, apenas_direto
        )
        melhor = _selecionar_menor_cotacao(melhor, cotacao)
        if idx < len(datas) and pausa_entre_buscas > 0:
            await asyncio.sleep(pausa_entre_buscas)
    return melhor


async def buscar_menor_preco(
    origem: str,
    destino: str,
    mes_foco: Optional[int] = None,
    duracao_dias: int = 5,
    apenas_direto: bool = False,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    passo_dias: int = 3,
    estrategia_busca: str = "passo",
    browser_gateway: Optional[FlightBrowserGatewayProtocol] = None,
    pausa_segundos: Optional[float] = None,
) -> Optional[LowestPriceQuote]:
    """
    Executa a busca de menor tarifa no Google Flights usando o gateway injetado.
    Exemplo: `await buscar_menor_preco("GRU", "JPA", mes_foco=11, duracao_dias=5)`
    """
    orig = _validar_codigo_aeroporto(origem, "origem")
    dest = _validar_codigo_aeroporto(destino, "destino")
    datas = gerar_datas_candidatas(
        mes_foco, duracao_dias, data_inicio, data_fim, passo_dias, estrategia_busca
    )
    if not datas:
        logger.warning(f"[{orig}->{dest}] Nenhuma data candidata gerada.")
        return None
    gateway = browser_gateway or PlaywrightStealthGateway()
    pausa = random.uniform(1.0, 2.0) if pausa_segundos is None else pausa_segundos
    return await _varrer_janelas_candidatas(
        gateway, orig, dest, datas, apenas_direto, pausa
    )


__all__ = [
    "gerar_datas_candidatas",
    "construir_url_busca",
    "extrair_menor_valor_de_texto",
    "extrair_menor_preco_de_elementos",
    "buscar_menor_preco",
]
