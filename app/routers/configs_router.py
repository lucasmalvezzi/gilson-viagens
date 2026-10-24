from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.date_planner import calcular_estimativa_chamadas
from app.gateways.os_scheduler_gateway import OsSchedulerGatewayProtocol
from app.models import ConfigBusca, HistoricoPreco
from app.os_schedule_sync import (
    get_os_scheduler_gateway,
    normalizar_horarios_csv,
    sincronizar_tarefas_windows_banco,
)
from app.scheduler import executar_busca_para_config, sincronizar_jobs_por_busca
from app.schemas import (
    CallEstimateRequest,
    CallEstimateResponse,
    ConfigBuscaCreate,
    ConfigBuscaResponse,
    ConfigBuscaUpdate,
    SearchExecutionResult,
)

router = APIRouter(prefix="/api/configs", tags=["configs"])


def _buscar_config_ou_404(db: Session, config_id: int) -> ConfigBusca:
    """Retorna a ConfigBusca pelo ID ou levanta HTTPException 404 descritivo."""
    cfg = db.query(ConfigBusca).filter(ConfigBusca.id == config_id).first()
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ConfigBusca id={config_id} not found; expected existing integer ID.",
        )
    return cfg


def _carregar_ultimos_historicos_por_busca(
    db: Session,
) -> list[HistoricoPreco]:
    """Otimização anti-N+1: busca os últimos registros de todas as buscas em 1 query."""
    subquery = (
        db.query(
            HistoricoPreco.id_busca,
            func.max(HistoricoPreco.id).label("max_id"),
        )
        .group_by(HistoricoPreco.id_busca)
        .subquery()
    )
    return (
        db.query(HistoricoPreco)
        .join(subquery, HistoricoPreco.id == subquery.c.max_id)
        .all()
    )


def _enriquecer_config_com_historico(
    cfg: ConfigBusca, ultimo: HistoricoPreco | None
) -> ConfigBuscaResponse:
    """Converte ConfigBusca em ConfigBuscaResponse preenchendo dados da última coleta."""
    resp = ConfigBuscaResponse.model_validate(cfg)
    if ultimo is not None:
        resp.menor_preco_recente = ultimo.valor
        resp.ultima_coleta = ultimo.data_coleta
        resp.link_recente = ultimo.link_direto
    return resp


def _aplicar_campos_atualizados(cfg: ConfigBusca, payload: ConfigBuscaUpdate) -> None:
    """Aplica apenas os campos explicitamente enviados no payload de atualização."""
    valores_enviados = payload.model_dump(exclude_unset=True)
    for nome_campo, novo_valor in valores_enviados.items():
        if nome_campo in ("origem", "destino") and isinstance(novo_valor, str):
            novo_valor = novo_valor.strip().upper()
        if nome_campo == "horarios_execucao" and isinstance(novo_valor, str):
            novo_valor = normalizar_horarios_csv(novo_valor)
        setattr(cfg, nome_campo, novo_valor)


def _sincronizar_agendadores_apos_mudanca(
    db: Session, os_gateway: Optional[OsSchedulerGatewayProtocol] = None
) -> None:
    """Atualiza jobs em memória (APScheduler) e tarefas do Agendador do Windows."""
    sincronizar_jobs_por_busca(db)
    sincronizar_tarefas_windows_banco(db, gateway=os_gateway)


@router.get("", response_model=List[ConfigBuscaResponse])
def listar_configs(db: Session = Depends(get_db)) -> List[ConfigBuscaResponse]:
    """
    Lista todas as configurações de busca enriquecidas com a última coleta.
    Exemplo: `GET /api/configs`
    """
    configs = db.query(ConfigBusca).all()
    if not configs:
        return []
    ultimos = _carregar_ultimos_historicos_por_busca(db)
    mapa_ultimos = {item.id_busca: item for item in ultimos}
    return [_enriquecer_config_com_historico(c, mapa_ultimos.get(c.id)) for c in configs]


@router.post(
    "", response_model=ConfigBuscaResponse, status_code=status.HTTP_201_CREATED
)
def criar_config(
    payload: ConfigBuscaCreate,
    db: Session = Depends(get_db),
    os_gateway: OsSchedulerGatewayProtocol = Depends(get_os_scheduler_gateway),
) -> ConfigBuscaResponse:
    """
    Cria um novo monitoramento de trecho aéreo e agenda seus horários de execução.
    Exemplo: `POST /api/configs {"origem": "GRU", "destino": "JPA", "valor_alvo": 800}`
    """
    nova_config = ConfigBusca(
        origem=payload.origem.strip().upper(),
        destino=payload.destino.strip().upper(),
        mes_foco=payload.mes_foco,
        data_inicio=payload.data_inicio,
        data_fim=payload.data_fim,
        passo_dias=payload.passo_dias or 3,
        estrategia_busca=payload.estrategia_busca or "passo",
        duracao_dias=payload.duracao_dias or 5,
        valor_alvo=payload.valor_alvo or 0.0,
        apenas_direto=payload.apenas_direto,
        horarios_execucao=normalizar_horarios_csv(payload.horarios_execucao),
        agendar_no_windows=payload.agendar_no_windows,
        ativa=payload.ativa,
    )
    db.add(nova_config)
    db.commit()
    db.refresh(nova_config)
    _sincronizar_agendadores_apos_mudanca(db, os_gateway)
    return ConfigBuscaResponse.model_validate(nova_config)


@router.put("/{config_id}", response_model=ConfigBuscaResponse)
def atualizar_config(
    config_id: int,
    payload: ConfigBuscaUpdate,
    db: Session = Depends(get_db),
    os_gateway: OsSchedulerGatewayProtocol = Depends(get_os_scheduler_gateway),
) -> ConfigBuscaResponse:
    """
    Atualiza campos e horários de um monitoramento existente e sincroniza agendadores.
    Exemplo: `PUT /api/configs/1 {"valor_alvo": 750, "horarios_execucao": "08:00, 20:00"}`
    """
    cfg = _buscar_config_ou_404(db, config_id)
    _aplicar_campos_atualizados(cfg, payload)
    db.commit()
    db.refresh(cfg)
    _sincronizar_agendadores_apos_mudanca(db, os_gateway)
    ultimo = (
        db.query(HistoricoPreco)
        .filter(HistoricoPreco.id_busca == cfg.id)
        .order_by(HistoricoPreco.id.desc())
        .first()
    )
    return _enriquecer_config_com_historico(cfg, ultimo)


@router.patch("/{config_id}/toggle", response_model=ConfigBuscaResponse)
def alternar_status_config(
    config_id: int,
    db: Session = Depends(get_db),
    os_gateway: OsSchedulerGatewayProtocol = Depends(get_os_scheduler_gateway),
) -> ConfigBuscaResponse:
    """
    Alterna o status ativo/pausado de uma configuração de busca e reagenda.
    Exemplo: `PATCH /api/configs/1/toggle`
    """
    cfg = _buscar_config_ou_404(db, config_id)
    cfg.ativa = not cfg.ativa
    db.commit()
    db.refresh(cfg)
    _sincronizar_agendadores_apos_mudanca(db, os_gateway)
    return ConfigBuscaResponse.model_validate(cfg)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_config(
    config_id: int,
    db: Session = Depends(get_db),
    os_gateway: OsSchedulerGatewayProtocol = Depends(get_os_scheduler_gateway),
) -> None:
    """
    Remove uma configuração de busca, seus históricos e seus agendamentos.
    Exemplo: `DELETE /api/configs/1`
    """
    cfg = _buscar_config_ou_404(db, config_id)
    db.delete(cfg)
    db.commit()
    _sincronizar_agendadores_apos_mudanca(db, os_gateway)


@router.post("/{config_id}/buscar-agora", response_model=SearchExecutionResult)
async def buscar_agora_config(
    config_id: int, db: Session = Depends(get_db)
) -> SearchExecutionResult:
    """
    Dispara imediatamente o scraper para o monitoramento informado.
    Exemplo: `POST /api/configs/1/buscar-agora`
    """
    _buscar_config_ou_404(db, config_id)
    return await executar_busca_para_config(config_id)


@router.post("/estimar-chamadas", response_model=CallEstimateResponse)
def estimar_chamadas(payload: CallEstimateRequest) -> CallEstimateResponse:
    """
    Estima a quantidade de requisições e tempo de execução para os parâmetros informados.
    Exemplo: `POST /api/configs/estimar-chamadas {"mes_foco": 11, "duracao_dias": 5}`
    """
    return calcular_estimativa_chamadas(payload)
