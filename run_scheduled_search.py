# -*- coding: utf-8 -*-
"""
Executor standalone de buscas agendadas do GilsonViagens.
Funciona diretamente sobre o SQLite e Playwright sem precisar do servidor FastAPI rodando.
"""
import argparse
import asyncio
import logging

from app.database import SessionLocal, init_db
from app.scheduler import executar_busca_para_config, rotina_diaria_de_buscas
from app.structured_log_store import activar_coletor_estruturado

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
activar_coletor_estruturado()
logger = logging.getLogger("gilson_standalone_runner")


def _construir_parser_cli() -> argparse.ArgumentParser:
    """Configura os argumentos de linha de comando (--config-id ou --all)."""
    parser = argparse.ArgumentParser(
        description="Executa buscas de passagens do GilsonViagens sem o servidor web rodando."
    )
    parser.add_argument(
        "--config-id",
        type=int,
        default=None,
        help="ID da busca ativa específica a ser executada.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Executa todas as buscas ativas cadastradas no banco.",
    )
    return parser


async def executar_fluxo_standalone(
    config_id: int | None = None, executar_todas: bool = False
) -> str:
    """
    Inicializa o banco SQLite e executa uma busca individual ou todas as ativas.
    Exemplo: `await executar_fluxo_standalone(config_id=1)`
    """
    init_db()
    if config_id is not None:
        logger.info(f"[Standalone Windows Task] Iniciando busca individual #{config_id}...")
        res = await executar_busca_para_config(config_id, session_factory=SessionLocal)
        logger.info(f"[Standalone Windows Task] Resultado #{config_id}: {res.mensagem}")
        return res.mensagem
    if executar_todas:
        logger.info("[Standalone Windows Task] Executando todas as buscas ativas...")
        return await rotina_diaria_de_buscas(session_factory=SessionLocal)
    raise ValueError(
        f"Invalid CLI arguments config_id={config_id}, executar_todas={executar_todas}; "
        "expected --config-id <int> or --all."
    )


def main() -> None:
    """
    Ponto de entrada chamado pelo Agendador de Tarefas do Windows (`schtasks`).
    Exemplo: `python run_scheduled_search.py --config-id 1`
    """
    args = _construir_parser_cli().parse_args()
    usar_todas = bool(args.all or args.config_id is None)
    mensagem = asyncio.run(
        executar_fluxo_standalone(config_id=args.config_id, executar_todas=usar_todas)
    )
    print(mensagem)


if __name__ == "__main__":
    main()
