from fastapi import APIRouter, Depends
from app.models.schemas import ExplainRequest, ExplainResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api", tags=["explain"])

_rag = None


def set_rag_service(service):
    global _rag
    _rag = service


@router.post("/explain", response_model=ExplainResponse)
def explain_term(req: ExplainRequest, user: dict = Depends(get_current_user)):
    result = _rag.explain(req.term, req.context or "")
    return ExplainResponse(**result)
