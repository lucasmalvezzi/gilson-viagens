import asyncio
from datetime import datetime
import logging
from typing import Awaitable, Callable, Optional, Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import ConfigBusca, ConfiguracaoSistema, HistoricoPreco
from app.os_schedule_sync import extrair_lista_horarios_validos, parse_horario_hh_mm
from app.schemas import LowestPriceQuote, SearchExecutionResult
from app.scraper import buscar_menor_preco
from app.telegram_service import enviar_alerta_preco

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

SessionFactoryType = Callable[[], Session]
PriceFinderCallable = Callable[..., Awaitable[Optional[LowestPriceQuote]]]
AlertSenderCallable = Callable[..., Awaitable[bool]]

# Re-exportado para compatibilidade com testes e chamadas internas
_parse_horario_hh_mm = parse_horario_hh_mm


def _persistir_historico_preco(
    db: Session, config_id: int, cotacao: LowestPriceQuote
) -> HistoricoPreco:
    """Salva o resultado da coleta na tabela historico_precos."""
    registro = HistoricoPreco(
        id_busca=config_id,
        data_coleta=datetime.utcnow(),
        data_ida=cotacao["data_ida"],
        data_volta=cotacao["data_volta"],
        valor=cotacao["valor"],
        link_direto=cotacao["link_direto"],
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


async def _disparar_alerta_se_atingiu_alvo(
    db: Session,
    config: ConfigBusca,
    cotacao: LowestPriceQuote,
    alert_sender: AlertSenderCallable,
) -> bool:
    """Regra 6: Se valor_capturado <= valor_alvo, consome API do Telegram."""
    if cotacao["valor"] > config.valor_alvo:
        return False
    config_sis = db.query(ConfiguracaoSistema).first()
    if not config_sis or not config_sis.telegram_bot_token or not config_sis.telegram_chat_id:
        logger.warning("Alerta disparado, mas Telegram não configurado no sistema.")
        return False
    return await alert_sender(
        bot_token=config_sis.telegram_bot_token,
        chat_id=config_sis.telegram_chat_id,
        origem=config.origem,
        destino=config.destino,
        data_ida=cotacao["data_ida"].strftime("%d/%m/%Y"),
        data_volta=cotacao["data_volta"].strftime("%d/%m/%Y"),
        valor_alvo=config.valor_alvo,
        valor_encontrado=cotacao["valor"],
        link_direto=cotacao["link_direto"],
        apenas_direto=bool(config.apenas_direto),
    )


async def _consultar_preco_da_config(
    config: ConfigBusca, price_finder: PriceFinderCallable
) -> Optional[LowestPriceQuote]:
    """Invoca o buscador de preços com os parâmetros da ConfigBusca."""
    return await price_finder(
        origem=config.origem,
        destino=config.destino,
        mes_foco=config.mes_foco,
        duracao_dias=config.duracao_dias,
        apenas_direto=bool(config.apenas_direto),
        data_inicio=config.data_inicio,
        data_fim=config.data_fim,
        passo_dias=config.passo_dias or 3,
        estrategia_busca=config.estrategia_busca or "passo",
    )


def _construir_resultado_sem_voos(config: ConfigBusca) -> SearchExecutionResult:
    """Monta SearchExecutionResult quando nenhuma cotação é encontrada."""
    return SearchExecutionResult(
        config_id=config.id,
        origem=config.origem,
        destino=config.destino,
        menor_valor=None,
        data_ida=None,
        data_volta=None,
        link=None,
        alerta_enviado=False,
        mensagem="Nenhum voo ou preço encontrado na data especificada.",
    )


async def executar_busca_para_config(
    config_id: int,
    session_factory: SessionFactoryType = SessionLocal,
    price_finder: PriceFinderCallable = buscar_menor_preco,
    alert_sender: AlertSenderCallable = enviar_alerta_preco,
) -> SearchExecutionResult:
    """
    Executa a raspagem para uma configuração, salva histórico e envia alerta se aplicável.
    Exemplo: `res = await executar_busca_para_config(1)`
    """
    db: Session = session_factory()
    try:
        config = db.query(ConfigBusca).filter(ConfigBusca.id == config_id).first()
        if not config:
            raise ValueError(f"Invalid config_id={config_id}; ConfigBusca not found.")
        cotacao = await _consultar_preco_da_config(config, price_finder)
        if not cotacao:
            return _construir_resultado_sem_voos(config)
        _persistir_historico_preco(db, config.id, cotacao)
        alerta = await _disparar_alerta_se_atingiu_alvo(db, config, cotacao, alert_sender)
        return SearchExecutionResult(
            config_id=config.id,
            origem=config.origem,
            destino=config.destino,
            menor_valor=cotacao["valor"],
            data_ida=cotacao["data_ida"].strftime("%Y-%m-%d"),
            data_volta=cotacao["data_volta"].strftime("%Y-%m-%d"),
            link=cotacao["link_direto"],
            alerta_enviado=alerta,
            mensagem=f"Busca concluída. Menor valor: R$ {cotacao['valor']:.2f}",
        )
    finally:
        db.close()


def _obter_ou_criar_config_sistema(db: Session) -> ConfiguracaoSistema:
    """Retorna o registro único de ConfiguracaoSistema ou cria o padrão."""
    config_sis = db.query(ConfiguracaoSistema).first()
    if config_sis:
        return config_sis
    novo = ConfiguracaoSistema(id=1, horario_execucao="09:00")
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


async def _processar_buscas_ativas(
    buscas_ativas: list[ConfigBusca],
    session_factory: SessionFactoryType,
    price_finder: PriceFinderCallable,
    alert_sender: AlertSenderCallable,
    pausa_segundos: float,
) -> Tuple[int, int]:
    """Itera sobre as buscas ativas contabilizando execuções e alertas."""
    processadas = 0
    alertas = 0
    for cfg in buscas_ativas:
        res = await executar_busca_para_config(
            cfg.id, session_factory, price_finder, alert_sender
        )
        processadas += 1
        alertas += 1 if res.alerta_enviado else 0
        if pausa_segundos > 0:
            await asyncio.sleep(pausa_segundos)
    return processadas, alertas


async def rotina_diaria_de_buscas(
    session_factory: SessionFactoryType = SessionLocal,
    price_finder: PriceFinderCallable = buscar_menor_preco,
    alert_sender: AlertSenderCallable = enviar_alerta_preco,
    pausa_segundos: float = 5.0,
) -> str:
    """
    Rotina executada diariamente pelo APScheduler para todas as buscas ativas.
    Exemplo: `status_msg = await rotina_diaria_de_buscas()`
    """
    db: Session = session_factory()
    try:
        config_sis = _obter_ou_criar_config_sistema(db)
        config_sis.ultimo_status = "Em execução..."
        config_sis.ultima_execucao = datetime.utcnow()
        db.commit()
        ativas = db.query(ConfigBusca).filter(ConfigBusca.ativa == True).all()
        total, alertas = await _processar_buscas_ativas(
            ativas, session_factory, price_finder, alert_sender, pausa_segundos
        )
        config_sis.ultimo_status = f"Concluída com sucesso: {total} buscas, {alertas} alertas."
        db.commit()
        return config_sis.ultimo_status
    finally:
        db.close()


def _agendar_horarios_de_uma_config(
    cfg: ConfigBusca, target_scheduler: AsyncIOScheduler
) -> None:
    """Registra um CronTrigger para cada horário configurado na busca ativa."""
    horarios = extrair_lista_horarios_validos(cfg.horarios_execucao)
    for hora, minuto in horarios:
        job_id = f"busca_config_{cfg.id}_{hora:02d}{minuto:02d}"
        target_scheduler.add_job(
            executar_busca_para_config,
            trigger=CronTrigger(hour=hora, minute=minuto),
            args=[cfg.id],
            id=job_id,
            name=f"Busca #{cfg.id} ({cfg.origem}->{cfg.destino}) às {hora:02d}:{minuto:02d}",
            replace_existing=True,
        )


def sincronizar_jobs_por_busca(
    db: Session,
    target_scheduler: AsyncIOScheduler = scheduler,
) -> int:
    """
    Recria os jobs do APScheduler respeitando os horários individuais de cada busca ativa.
    Exemplo: `total_jobs = sincronizar_jobs_por_busca(db)`
    """
    target_scheduler.remove_all_jobs()
    ativas = db.query(ConfigBusca).filter(ConfigBusca.ativa == True).all()
    for cfg in ativas:
        _agendar_horarios_de_uma_config(cfg, target_scheduler)
    config_sis = db.query(ConfiguracaoSistema).first()
    horario_global = (
        config_sis.horario_execucao if config_sis and config_sis.horario_execucao else "09:00"
    )
    hora, minuto = parse_horario_hh_mm(horario_global)
    target_scheduler.add_job(
        rotina_diaria_de_buscas,
        trigger=CronTrigger(hour=hora, minute=minuto),
        id="rotina_diaria_passagens",
        name="Rotina Diária Global Google Flights",
        replace_existing=True,
    )
    return len(target_scheduler.get_jobs())


def reconfigurar_agendador(
    horario_hh_mm: str = "09:00",
    target_scheduler: AsyncIOScheduler = scheduler,
) -> None:
    """
    Atualiza o horário do cronjob diário global no APScheduler.
    Exemplo: `reconfigurar_agendador("08:30")`
    """
    hora, minuto = parse_horario_hh_mm(horario_hh_mm)
    target_scheduler.add_job(
        rotina_diaria_de_buscas,
        trigger=CronTrigger(hour=hora, minute=minuto),
        id="rotina_diaria_passagens",
        name="Rotina Diária Google Flights",
        replace_existing=True,
    )
    logger.info(f"Agendador global configurado para às {hora:02d}:{minuto:02d}.")


def iniciar_scheduler(
    session_factory: SessionFactoryType = SessionLocal,
    target_scheduler: AsyncIOScheduler = scheduler,
) -> None:
    """
    Inicia o APScheduler carregando os horários de cada busca ativa e o global.
    Exemplo: `iniciar_scheduler()`
    """
    if target_scheduler.running:
        return
    db = session_factory()
    try:
        sincronizar_jobs_por_busca(db, target_scheduler=target_scheduler)
        target_scheduler.start()
    finally:
        db.close()
