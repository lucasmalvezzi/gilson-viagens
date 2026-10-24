from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class ConfigBusca(Base):
    __tablename__ = "configs_busca"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    origem = Column(String(10), nullable=False)
    destino = Column(String(10), nullable=False)
    mes_foco = Column(Integer, nullable=True)  # 1 to 12 (opcional se data_inicio for informada)
    data_inicio = Column(Date, nullable=True)  # Data início do intervalo personalizado
    data_fim = Column(Date, nullable=True)     # Data fim do intervalo personalizado
    passo_dias = Column(Integer, nullable=True, default=3)  # Frequência de dias entre buscas
    estrategia_busca = Column(String(30), nullable=True, default="passo")  # passo, todos, fins_de_semana
    duracao_dias = Column(Integer, nullable=False, default=5)
    valor_alvo = Column(Float, nullable=False)
    apenas_direto = Column(Boolean, nullable=False, default=False)
    horarios_execucao = Column(String(100), nullable=False, default="09:00")
    agendar_no_windows = Column(Boolean, nullable=False, default=True)
    ativa = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    # Relationships
    historicos = relationship("HistoricoPreco", back_populates="config", cascade="all, delete-orphan")


class HistoricoPreco(Base):
    __tablename__ = "historico_precos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_busca = Column(Integer, ForeignKey("configs_busca.id", ondelete="CASCADE"), nullable=False, index=True)
    data_coleta = Column(DateTime, nullable=False, default=datetime.utcnow)
    data_ida = Column(Date, nullable=False)
    data_volta = Column(Date, nullable=False)
    valor = Column(Float, nullable=False)
    link_direto = Column(String(1000), nullable=False)

    __table_args__ = (
        Index("ix_historico_id_busca_data_coleta", "id_busca", "data_coleta"),
        Index("ix_historico_data_coleta", "data_coleta"),
    )

    # Relationships
    config = relationship("ConfigBusca", back_populates="historicos")


class ConfiguracaoSistema(Base):
    __tablename__ = "configuracoes_sistema"

    id = Column(Integer, primary_key=True, default=1)
    telegram_bot_token = Column(String(255), nullable=True)
    telegram_chat_id = Column(String(100), nullable=True)
    horario_execucao = Column(String(5), nullable=False, default="09:00")  # HH:MM
    ultimo_status = Column(String(500), nullable=True)
    ultima_execucao = Column(DateTime, nullable=True)
