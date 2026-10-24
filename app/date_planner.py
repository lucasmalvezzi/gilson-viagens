import calendar
from datetime import date, timedelta
from typing import List, Optional, Tuple

from app.schemas import CallEstimateRequest, CallEstimateResponse


def _resolver_passo_dias(estrategia_busca: str, passo_dias: int) -> int:
    """Determina o incremento de dias conforme a estratégia escolhida."""
    if estrategia_busca in ("todos", "fins_de_semana"):
        return 1
    return max(1, passo_dias or 3)


def _gerar_datas_por_intervalo(
    data_inicio: date,
    data_fim: date,
    duracao_dias: int,
    passo_dias: int,
    estrategia_busca: str,
    hoje: date
) -> List[Tuple[date, date]]:
    """Gera pares (ida, volta) dentro de um intervalo personalizado de datas."""
    if data_inicio > data_fim:
        raise ValueError(
            f"Invalid date range data_inicio={data_inicio} > data_fim={data_fim}; "
            "expected data_inicio <= data_fim (YYYY-MM-DD)."
        )
    cur_dt = max(data_inicio, hoje + timedelta(days=1))
    fim_dt = max(data_fim, cur_dt)
    passo = _resolver_passo_dias(estrategia_busca, passo_dias)
    candidatas: List[Tuple[date, date]] = []
    while cur_dt <= fim_dt:
        if estrategia_busca != "fins_de_semana" or cur_dt.weekday() in (4, 5):
            candidatas.append((cur_dt, cur_dt + timedelta(days=duracao_dias)))
        cur_dt += timedelta(days=passo)
    return candidatas


def _gerar_sextas_do_mes(
    ano: int,
    mes: int,
    ultimo_dia_mes: int,
    duracao_dias: int,
    hoje: date
) -> List[Tuple[date, date]]:
    """Retorna todas as sextas-feiras futuras dentro do mês especificado."""
    sextas: List[Tuple[date, date]] = []
    for dia in range(1, ultimo_dia_mes + 1):
        dt_ida = date(ano, mes, dia)
        if dt_ida > hoje and dt_ida.weekday() == 4:
            sextas.append((dt_ida, dt_ida + timedelta(days=duracao_dias)))
    return sextas


def _gerar_datas_fallback_do_mes(
    ano: int,
    mes: int,
    ultimo_dia_mes: int,
    duracao_dias: int,
    hoje: date
) -> List[Tuple[date, date]]:
    """Retorna dias fixos (5, 12, 19, 26) quando não restam sextas-feiras no mês."""
    dias_validos = [d for d in (5, 12, 19, 26) if d <= ultimo_dia_mes]
    pares: List[Tuple[date, date]] = []
    for dia in dias_validos:
        dt_ida = date(ano, mes, dia)
        if dt_ida > hoje:
            pares.append((dt_ida, dt_ida + timedelta(days=duracao_dias)))
    return pares


def _gerar_datas_por_mes_foco(
    mes_foco: Optional[int],
    duracao_dias: int,
    hoje: date
) -> List[Tuple[date, date]]:
    """Gera até 8 pares de datas candidatas focadas em um mês específico (1..12)."""
    mes = mes_foco or (hoje.month + 1 if hoje.month < 12 else 1)
    if not (1 <= mes <= 12):
        raise ValueError(f"Invalid mes_foco={mes_foco}; expected integer between 1 and 12.")
    ano = hoje.year + (1 if mes < hoje.month else 0)
    _, ultimo_dia_mes = calendar.monthrange(ano, mes)
    sextas = _gerar_sextas_do_mes(ano, mes, ultimo_dia_mes, duracao_dias, hoje)
    if sextas:
        return sextas[:8]
    return _gerar_datas_fallback_do_mes(ano, mes, ultimo_dia_mes, duracao_dias, hoje)[:8]


def gerar_datas_candidatas(
    mes_foco: Optional[int] = None,
    duracao_dias: int = 5,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    passo_dias: int = 3,
    estrategia_busca: str = "passo",
    referencia_hoje: Optional[date] = None
) -> List[Tuple[date, date]]:
    """
    Gera pares de datas (ida, volta) programaticamente para consulta de voos.
    Exemplo: `gerar_datas_candidatas(mes_foco=1, duracao_dias=7)`
    """
    if duracao_dias < 1:
        raise ValueError(f"Invalid duracao_dias={duracao_dias}; expected integer >= 1.")
    hoje = referencia_hoje or date.today()
    if data_inicio and data_fim:
        return _gerar_datas_por_intervalo(
            data_inicio, data_fim, duracao_dias, passo_dias, estrategia_busca, hoje
        )
    return _gerar_datas_por_mes_foco(mes_foco, duracao_dias, hoje)


def calcular_estimativa_chamadas(
    parametros: CallEstimateRequest,
    referencia_hoje: Optional[date] = None
) -> CallEstimateResponse:
    """
    Calcula total de chamadas, tempo previsto e até 6 amostras formatadas de datas.
    Exemplo: `calcular_estimativa_chamadas(CallEstimateRequest(mes_foco=3, duracao_dias=5))`
    """
    datas = gerar_datas_candidatas(
        mes_foco=parametros.mes_foco,
        duracao_dias=parametros.duracao_dias,
        data_inicio=parametros.data_inicio,
        data_fim=parametros.data_fim,
        passo_dias=parametros.passo_dias,
        estrategia_busca=parametros.estrategia_busca,
        referencia_hoje=referencia_hoje
    )
    amostras = [
        f"{ida.strftime('%d/%m/%Y')} a {volta.strftime('%d/%m/%Y')}"
        for ida, volta in datas[:6]
    ]
    return CallEstimateResponse(
        total_chamadas=len(datas),
        tempo_estimado_segundos=round(len(datas) * 2.5),
        amostras=amostras
    )
