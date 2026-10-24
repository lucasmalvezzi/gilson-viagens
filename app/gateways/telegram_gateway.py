from typing import Protocol, TypedDict
import httpx

from app.schemas import TelegramTestResult


class TelegramSendMessagePayload(TypedDict):
    """Payload tipado enviado ao endpoint sendMessage da API do Telegram."""
    chat_id: str
    text: str
    parse_mode: str
    disable_web_page_preview: bool


class TelegramGatewayProtocol(Protocol):
    """Interface enxuta do projeto para envio de mensagens HTML via Telegram."""

    async def send_html_message(
        self, bot_token: str, chat_id: str, html_text: str
    ) -> TelegramTestResult:
        """Envia mensagem HTML para a API do Telegram e retorna resultado tipado."""
        ...


def _build_telegram_endpoint(bot_token: str) -> str:
    """Monta a URL do endpoint sendMessage da API oficial do Telegram."""
    cleaned_token = bot_token.strip()
    if not cleaned_token:
        raise ValueError(
            f"Invalid bot_token={bot_token!r}; expected non-empty Telegram token string."
        )
    return f"https://api.telegram.org/bot{cleaned_token}/sendMessage"


def _interpret_telegram_http_response(response: httpx.Response) -> TelegramTestResult:
    """Interpreta o corpo JSON retornado pelo Telegram sem usar nomes genéricos."""
    parsed_body = response.json()
    if response.status_code == 200 and parsed_body.get("ok"):
        return TelegramTestResult(
            sucesso=True,
            mensagem="Mensagem enviada com sucesso no Telegram!",
        )
    error_detail = parsed_body.get("description", response.text or "Erro desconhecido")
    return TelegramTestResult(
        sucesso=False,
        mensagem=f"Erro do Telegram: {error_detail}",
    )


class HttpxTelegramGateway:
    """
    Adaptador HTTP assíncrono que encapsula `httpx.AsyncClient` para o Telegram.
    Exemplo: `res = await HttpxTelegramGateway().send_html_message("123:ABC", "999", "<b>Oi</b>")`
    """

    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def send_html_message(
        self, bot_token: str, chat_id: str, html_text: str
    ) -> TelegramTestResult:
        """
        Dispara POST para sendMessage do Telegram e retorna `TelegramTestResult`.
        Exemplo: `await gateway.send_html_message(token, chat_id, "<b>Alerta</b>")`
        """
        endpoint_url = _build_telegram_endpoint(bot_token)
        request_payload = TelegramSendMessagePayload(
            chat_id=chat_id.strip(),
            text=html_text,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )
        try:
            return await self._post_payload(endpoint_url, request_payload)
        except Exception as exc:
            return TelegramTestResult(
                sucesso=False, mensagem=f"Falha de conexão: {str(exc)}"
            )

    async def _post_payload(
        self, endpoint_url: str, request_payload: TelegramSendMessagePayload
    ) -> TelegramTestResult:
        """Executa a chamada POST assíncrona via httpx e converte a resposta."""
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as http_client:
            http_response = await http_client.post(endpoint_url, json=request_payload)
            return _interpret_telegram_http_response(http_response)
