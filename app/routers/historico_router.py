from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import HistoricoPreco
from app.schemas import HistoricoPrecoResponse

router = APIRouter(prefix="/api/historico", tags=["historico"])

VALORES_FILTRO_VAZIO = ("null", "undefined", "", "0")


def _extrair_id_busca_opcional(id_busca_raw: Optional[str]) -> Optional[int]:
    """Converte o parâmetro de query id_busca em inteiro válido ou None."""
    if not id_busca_raw:
        return None
    limpo = str(id_busca_raw).strip().lower()
    if limpo in VALORES_FILTRO_VAZIO or not limpo.isdigit():
        return None
    return int(limpo)


@router.get("", response_model=List[HistoricoPrecoResponse])
def listar_historico(
    id_busca: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> List[HistoricoPrecoResponse]:
    """
    Lista o histórico de preços coletados usando o índice composto (id_busca, data_coleta).
    Exemplo: `GET /api/historico?id_busca=1&limit=50`
    """
    query = db.query(HistoricoPreco)
    busca_id = _extrair_id_busca_opcional(id_busca)
    if busca_id is not None:
        query = query.filter(HistoricoPreco.id_busca == busca_id)
    itens = (
        query.order_by(HistoricoPreco.data_coleta.desc())
        .offset(max(0, offset))
        .limit(min(max(1, limit), 200))
        .all()
    )
    return [HistoricoPrecoResponse.model_validate(item) for item in itens]
