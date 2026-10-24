"""Camada de adaptadores (gateways) para isolar bibliotecas de terceiros e SO."""
from app.gateways.browser_gateway import (
    FlightBrowserGatewayProtocol,
    PlaywrightStealthGateway,
)
from app.gateways.os_scheduler_gateway import (
    OsSchedulerGatewayProtocol,
    TASK_NAME_PREFIX,
    WindowsTaskSchedulerGateway,
)
from app.gateways.telegram_gateway import (
    HttpxTelegramGateway,
    TelegramGatewayProtocol,
)

__all__ = [
    "FlightBrowserGatewayProtocol",
    "PlaywrightStealthGateway",
    "OsSchedulerGatewayProtocol",
    "TASK_NAME_PREFIX",
    "WindowsTaskSchedulerGateway",
    "TelegramGatewayProtocol",
    "HttpxTelegramGateway",
]
