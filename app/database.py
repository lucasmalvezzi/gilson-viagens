from pathlib import Path
from typing import Any, Generator
from sqlalchemy import Connection, Engine, create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "flights.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine: Engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30.0  # Evita travamento por lock
    }
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    """
    Otimiza o SQLite para altíssima performance de leitura e escrita concorrente.
    Exemplo: acionado automaticamente pelo SQLAlchemy ao abrir conexão no pool.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode = WAL")       # Write-Ahead Logging (leituras e escritas simultâneas)
    cursor.execute("PRAGMA synchronous = NORMAL")     # Muito mais rápido sem perder integridade
    cursor.execute("PRAGMA cache_size = -64000")      # 64 MB de cache em memória RAM
    cursor.execute("PRAGMA temp_store = MEMORY")      # Tabelas temporárias na memória
    cursor.execute("PRAGMA mmap_size = 268435456")    # Memory-mapped I/O (256 MB)
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Provedor de sessão SQLAlchemy para injeção de dependência nas rotas FastAPI.
    Exemplo: `db: Session = Depends(get_db)`
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_SQL_CREATE_CONFIGS_NEW = """
CREATE TABLE configs_busca_new (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    origem VARCHAR(10) NOT NULL,
    destino VARCHAR(10) NOT NULL,
    mes_foco INTEGER NULL,
    data_inicio DATE NULL,
    data_fim DATE NULL,
    passo_dias INTEGER DEFAULT 3,
    estrategia_busca VARCHAR(30) DEFAULT 'passo',
    duracao_dias INTEGER NOT NULL DEFAULT 5,
    valor_alvo FLOAT NOT NULL,
    apenas_direto BOOLEAN NOT NULL DEFAULT 0,
    ativa BOOLEAN NOT NULL DEFAULT 1,
    criado_em DATETIME
)
"""

_SQL_COPY_CONFIGS = """
INSERT INTO configs_busca_new (
    id, origem, destino, mes_foco, data_inicio, data_fim,
    passo_dias, estrategia_busca, duracao_dias, valor_alvo,
    apenas_direto, ativa, criado_em
)
SELECT
    id, origem, destino, mes_foco, data_inicio, data_fim,
    COALESCE(passo_dias, 3), COALESCE(estrategia_busca, 'passo'),
    duracao_dias, valor_alvo, COALESCE(apenas_direto, 0),
    ativa, criado_em
FROM configs_busca
"""


def _migrar_tabela_configs_se_necessario(conn: Connection) -> None:
    """Recria configs_busca apenas quando mes_foco legado possui restrição NOT NULL."""
    cols = conn.exec_driver_sql("PRAGMA table_info(configs_busca)").fetchall()
    mes_foco_col = next((c for c in cols if c[1] == "mes_foco"), None)
    if not mes_foco_col or mes_foco_col[3] != 1:
        return
    conn.exec_driver_sql("PRAGMA foreign_keys = OFF")
    conn.exec_driver_sql(_SQL_CREATE_CONFIGS_NEW)
    conn.exec_driver_sql(_SQL_COPY_CONFIGS)
    conn.exec_driver_sql("DROP TABLE configs_busca")
    conn.exec_driver_sql("ALTER TABLE configs_busca_new RENAME TO configs_busca")
    conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_configs_busca_id ON configs_busca (id)")
    conn.exec_driver_sql("PRAGMA foreign_keys = ON")


def _adicionar_colunas_agendamento_se_ausentes(conn: Connection) -> None:
    """Adiciona colunas horarios_execucao e agendar_no_windows em bancos existentes."""
    cols = conn.exec_driver_sql("PRAGMA table_info(configs_busca)").fetchall()
    nomes_colunas = {c[1] for c in cols}
    if "horarios_execucao" not in nomes_colunas:
        conn.exec_driver_sql(
            "ALTER TABLE configs_busca ADD COLUMN horarios_execucao VARCHAR(100) NOT NULL DEFAULT '09:00'"
        )
    if "agendar_no_windows" not in nomes_colunas:
        conn.exec_driver_sql(
            "ALTER TABLE configs_busca ADD COLUMN agendar_no_windows BOOLEAN NOT NULL DEFAULT 1"
        )


def init_db(target_engine: Engine = engine) -> None:
    """
    Inicializa as tabelas do banco e aplica migrações automáticas de schema.
    Exemplo: `init_db(engine)`
    """
    Base.metadata.create_all(bind=target_engine)
    with target_engine.begin() as conn:
        _migrar_tabela_configs_se_necessario(conn)
        _adicionar_colunas_agendamento_se_ausentes(conn)
