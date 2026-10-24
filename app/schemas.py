from datetime import date, datetime
from typing import List, Optional, TypedDict
from pydantic import BaseModel, ConfigDict, Field


class LowestPriceQuote(TypedDict):
    """Estrutura tipada para o menor preço encontrado pelo scraper."""
    valor: float
    data_ida: date
    data_volta: date
    link_direto: str
    apenas_direto: bool


class TelegramTestResult(TypedDict):
    """Estrutura tipada para resultado do teste de notificação do Telegram."""
    sucesso: bool
    mensagem: str


class StructuredLogEntry(TypedDict):
    """Entrada estruturada de log JSON no ring buffer."""
    id: int
    timestamp: str
    level: str
    logger: str
    message: str


class WindowsScheduledTaskEntry(TypedDict):
    """Representa uma tarefa registrada no Agendador de Tarefas do Windows."""
    task_name: str
    proximo_disparo: str
    status: str


class ConfigBuscaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    origem: str = Field(..., min_length=2, max_length=10, description="Código IATA ou cidade de origem (ex: GRU)")
    destino: str = Field(..., min_length=2, max_length=10, description="Código IATA ou cidade de destino (ex: JPA)")
    mes_foco: Optional[int] = Field(None, ge=1, le=12, description="Mês desejado (1-12)")
    data_inicio: Optional[date] = Field(None, description="Data início do intervalo personalizado")
    data_fim: Optional[date] = Field(None, description="Data fim do intervalo personalizado")
    passo_dias: Optional[int] = Field(3, ge=1, le=30, description="Passo em dias entre pesquisas")
    estrategia_busca: Optional[str] = Field("passo", description="passo, todos, fins_de_semana, mes")
    duracao_dias: Optional[int] = Field(5, ge=1, le=60, description="Duração da viagem em dias")
    valor_alvo: Optional[float] = Field(None, gt=0, description="Preço alvo em R$")
    apenas_direto: bool = Field(False, description="Filtrar apenas voos diretos (sem escalas)")
    horarios_execucao: str = Field("09:00", description="Horário(s) HH:MM separados por vírgula para esta busca")
    agendar_no_windows: bool = Field(True, description="Registrar tarefa independente no Windows Task Scheduler")
    ativa: bool = True


class ConfigBuscaCreate(ConfigBuscaBase):
    pass


class ConfigBuscaUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    origem: Optional[str] = None
    destino: Optional[str] = None
    mes_foco: Optional[int] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    passo_dias: Optional[int] = None
    estrategia_busca: Optional[str] = None
    duracao_dias: Optional[int] = None
    valor_alvo: Optional[float] = None
    apenas_direto: Optional[bool] = None
    horarios_execucao: Optional[str] = None
    agendar_no_windows: Optional[bool] = None
    ativa: Optional[bool] = None


class HistoricoPrecoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_busca: int
    data_coleta: datetime
    data_ida: date
    data_volta: date
    valor: float
    link_direto: str


class ConfigBuscaResponse(ConfigBuscaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: Optional[datetime] = None
    menor_preco_recente: Optional[float] = None
    ultima_coleta: Optional[datetime] = None
    link_recente: Optional[str] = None


class SettingsBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    horario_execucao: str = "09:00"


class SettingsResponse(SettingsBase):
    model_config = ConfigDict(from_attributes=True)

    ultimo_status: Optional[str] = None
    ultima_execucao: Optional[datetime] = None


class TestTelegramRequest(BaseModel):
    token: Optional[str] = None
    chat_id: Optional[str] = None


class SearchExecutionResult(BaseModel):
    config_id: int
    origem: str
    destino: str
    menor_valor: Optional[float]
    data_ida: Optional[str]
    data_volta: Optional[str]
    link: Optional[str]
    alerta_enviado: bool
    mensagem: str


class CallEstimateRequest(BaseModel):
    mes_foco: Optional[int] = None
    duracao_dias: int = 5
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    passo_dias: int = 3
    estrategia_busca: str = "passo"


class CallEstimateResponse(BaseModel):
    total_chamadas: int
    tempo_estimado_segundos: int
    amostras: List[str]


class LogListResponse(BaseModel):
    total: int
    logs: List[StructuredLogEntry]


class ActionMessageResponse(BaseModel):
    mensagem: str


class WindowsSchedulerStatusResponse(BaseModel):
    suportado: bool
    total_tarefas: int
    comando_standalone: str
    tarefas: List[WindowsScheduledTaskEntry]
    mensagem: str
