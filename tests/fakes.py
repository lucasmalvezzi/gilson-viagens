from typing import Coroutine, List, Optional, Tuple, TypeVar
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, init_db
from app.schemas import (
    LowestPriceQuote,
    TelegramTestResult,
    WindowsScheduledTaskEntry,
)

T = TypeVar("T")


def run_coroutine_synchronously(coro: Coroutine[object, object, T]) -> T:
    """
    Executa uma corrotina pura de forma determinística sem abrir sockets de loopback.
    Exemplo: `res = run_coroutine_synchronously(minha_funcao_async())`
    """
    try:
        while True:
            coro.send(None)
    except StopIteration as stop:
        resultado: T = stop.value
        return resultado


class FakeBrowserGateway:
    """
    Fake nomeado de navegador para testes F.I.R.S.T sem abrir Chromium real.
    Exemplo: `gateway = FakeBrowserGateway(listitem_texts=["Voo direto R$ 580,00"])`
    """

    def __init__(
        self,
        listitem_texts: Optional[List[str]] = None,
        raw_html: str = "",
        should_raise: bool = False,
    ) -> None:
        self.listitem_texts: List[str] = listitem_texts or []
        self.raw_html: str = raw_html
        self.should_raise: bool = should_raise
        self.visited_urls: List[str] = []

    async def fetch_rendered_flight_texts(self, url: str) -> Tuple[List[str], str]:
        """
        Registra a URL consultada e retorna os textos configurados em memória.
        Exemplo: `texts, html = await fake_gateway.fetch_rendered_flight_texts(url)`
        """
        self.visited_urls.append(url)
        if self.should_raise:
            raise RuntimeError(f"Simulated browser error for url={url!r}")
        return list(self.listitem_texts), self.raw_html


class FakeTelegramGateway:
    """
    Fake nomeado da API do Telegram para validar envios sem rede externa.
    Exemplo: `tg = FakeTelegramGateway(succeed=True)`
    """

    def __init__(self, succeed: bool = True, error_msg: str = "Simulated failure") -> None:
        self.succeed: bool = succeed
        self.error_msg: str = error_msg
        self.sent_messages: List[Tuple[str, str, str]] = []

    async def send_html_message(
        self, bot_token: str, chat_id: str, html_text: str
    ) -> TelegramTestResult:
        """
        Armazena a mensagem enviada em memória e retorna `TelegramTestResult`.
        Exemplo: `res = await fake_tg.send_html_message("tok", "123", "<b>Oi</b>")`
        """
        self.sent_messages.append((bot_token, chat_id, html_text))
        if self.succeed:
            return TelegramTestResult(sucesso=True, mensagem="OK Fake")
        return TelegramTestResult(sucesso=False, mensagem=self.error_msg)


class FakePriceFinder:
    """
    Fake nomeado para substituir `buscar_menor_preco` em testes do agendador.
    Exemplo: `finder = FakePriceFinder(quote)`
    """

    def __init__(self, quote: Optional[LowestPriceQuote] = None) -> None:
        self.quote: Optional[LowestPriceQuote] = quote
        self.calls_count: int = 0

    async def __call__(self, **kwargs: object) -> Optional[LowestPriceQuote]:
        """Incrementa contador de chamadas e retorna a cotação configurada."""
        self.calls_count += 1
        return self.quote


class FakeAlertSender:
    """
    Fake nomeado para substituir `enviar_alerta_preco` em testes do agendador.
    Exemplo: `sender = FakeAlertSender(succeed=True)`
    """

    def __init__(self, succeed: bool = True) -> None:
        self.succeed: bool = succeed
        self.alerts_sent: int = 0

    async def __call__(self, **kwargs: object) -> bool:
        """Registra tentativa de alerta e retorna resultado configurado."""
        self.alerts_sent += 1
        return self.succeed


class InMemorySqliteDatabase:
    """
    Banco SQLite em memória isolado por teste com StaticPool.
    Exemplo: `mem_db = InMemorySqliteDatabase()`
    """

    def __init__(self) -> None:
        self.engine: Engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        init_db(target_engine=self.engine)
        self.session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_session(self) -> Session:
        """Cria e retorna uma nova sessão SQLAlchemy conectada ao banco em memória."""
        session: Session = self.session_factory()
        return session

    def dispose(self) -> None:
        """Fecha conexões do banco em memória ao final do teste."""
        self.engine.dispose()


class FakeOsSchedulerGateway:
    """
    Fake nomeado do Agendador de Tarefas do Windows (`schtasks.exe`) para testes F.I.R.S.T.
    Exemplo: `os_gw = FakeOsSchedulerGateway()`
    """

    def __init__(self) -> None:
        self.tasks: List[WindowsScheduledTaskEntry] = []

    def register_daily_task(
        self, task_name: str, horario_hh_mm: str, command_line: str
    ) -> bool:
        """Registra ou substitui a tarefa em memória."""
        self.delete_task(task_name)
        self.tasks.append(
            WindowsScheduledTaskEntry(
                task_name=task_name,
                proximo_disparo=f"Amanhã às {horario_hh_mm}",
                status="Pronto",
            )
        )
        return True

    def delete_task(self, task_name: str) -> bool:
        """Remove a tarefa da lista em memória."""
        antes = len(self.tasks)
        self.tasks = [t for t in self.tasks if t["task_name"] != task_name]
        return len(self.tasks) < antes

    def list_project_tasks(
        self, prefix: str = "GilsonViagens_Busca_"
    ) -> List[WindowsScheduledTaskEntry]:
        """Retorna todas as tarefas em memória cujo nome inicia com o prefixo."""
        return [t for t in self.tasks if t["task_name"].startswith(prefix)]
