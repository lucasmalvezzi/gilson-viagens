import logging
from typing import Optional

from app.gateways.telegram_gateway import HttpxTelegramGateway, TelegramGatewayProtocol
from app.schemas import TelegramTestResult

logger = logging.getLogger(__name__)

MENSAGEM_TESTE_CONEXAO = (
    "🦎✈️ <b>GilsonViagens Conectado!</b>\n\n"
    "Pronto! O Gilson já sabe onde te avisar quando encontrar passagens baratas!"
)


def formatar_mensagem_alerta_preco(
    origem: str,
    destino: str,
    data_ida: str,
    data_volta: str,
    valor_alvo: float,
    valor_encontrado: float,
    link_direto: str,
    apenas_direto: bool = False,
) -> str:
    """
    Formata a mensagem HTML de alerta de preço atingido para envio no Telegram.
    Exemplo: `formatar_mensagem_alerta_preco("GRU", "JPA", "10/11", "15/11", 900.0, 750.0, "https://...")`
    """
    if valor_encontrado <= 0:
        raise ValueError(
            f"Invalid valor_encontrado={valor_encontrado}; expected positive float > 0."
        )
    badge = "\n✈️ <b>Voo Direto (Sem escalas)</b>" if apenas_direto else ""
    return (
        f"🦎🚨 <b>ALERTA DO GILSONVIAGENS!</b> ✈️\n\n"
        f"O Gilson achou uma passagem abaixo ou igual ao seu preço alvo!{badge}\n\n"
        f"📍 <b>Trecho:</b> <code>{origem.upper()}</code> ➡️ <code>{destino.upper()}</code>\n"
        f"📅 <b>Ida:</b> {data_ida}\n"
        f"📅 <b>Volta:</b> {data_volta}\n\n"
        f"🎯 <b>Seu Alvo:</b> R$ {valor_alvo:,.2f}\n"
        f"💰 <b>Menor Preço Encontrado:</b> <b>R$ {valor_encontrado:,.2f}</b> 🔥\n\n"
        f"🔗 <a href=\"{link_direto}\">Clique aqui para abrir no Google Flights</a>"
    )


async def enviar_mensagem_telegram(
    bot_token: str,
    chat_id: str,
    texto: str,
    gateway: Optional[TelegramGatewayProtocol] = None,
) -> bool:
    """
    Envia uma mensagem HTML via Telegram Bot API usando o gateway injetado.
    Exemplo: `await enviar_mensagem_telegram("123:ABC", "999", "<b>Alerta</b>")`
    """
    if not bot_token or not chat_id:
        logger.warning("Telegram Bot Token ou Chat ID não configurados.")
        return False
    adaptador = gateway or HttpxTelegramGateway()
    resultado = await adaptador.send_html_message(bot_token, chat_id, texto)
    if resultado["sucesso"]:
        logger.info(f"Mensagem enviada com sucesso para o Telegram ({chat_id}).")
        return True
    logger.error(f"Falha ao enviar para o Telegram: {resultado['mensagem']}")
    return False


async def enviar_alerta_preco(
    bot_token: str,
    chat_id: str,
    origem: str,
    destino: str,
    data_ida: str,
    data_volta: str,
    valor_alvo: float,
    valor_encontrado: float,
    link_direto: str,
    apenas_direto: bool = False,
    gateway: Optional[TelegramGatewayProtocol] = None,
) -> bool:
    """
    Envia alerta formatado para o usuário quando o preço for menor ou igual ao valor alvo.
    Exemplo: `await enviar_alerta_preco("123:ABC", "999", "GRU", "JPA", "10/11", "15/11", 900.0, 750.0, "https://...")`
    """
    html_alerta = formatar_mensagem_alerta_preco(
        origem=origem,
        destino=destino,
        data_ida=data_ida,
        data_volta=data_volta,
        valor_alvo=valor_alvo,
        valor_encontrado=valor_encontrado,
        link_direto=link_direto,
        apenas_direto=apenas_direto,
    )
    return await enviar_mensagem_telegram(bot_token, chat_id, html_alerta, gateway=gateway)


async def testar_conexao_telegram(
    bot_token: Optional[str],
    chat_id: Optional[str],
    gateway: Optional[TelegramGatewayProtocol] = None,
) -> TelegramTestResult:
    """
    Testa se o token e o chat_id são válidos enviando uma mensagem de teste.
    Exemplo: `await testar_conexao_telegram("123:ABC", "999")`
    """
    if not bot_token or not chat_id:
        return TelegramTestResult(
            sucesso=False,
            mensagem="Token do Bot e Chat ID são obrigatórios.",
        )
    adaptador = gateway or HttpxTelegramGateway()
    resultado = await adaptador.send_html_message(
        bot_token, chat_id, MENSAGEM_TESTE_CONEXAO
    )
    if resultado["sucesso"]:
        return TelegramTestResult(
            sucesso=True,
            mensagem="Mensagem de teste enviada com sucesso no Telegram!",
        )
    return resultado
