"""
Chat Router — LLM conversational agent via Ollama.
"""
import os
import sys
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from modules.llm_agent import answer_query, build_context_dict, check_llm_available, QUICK_SUGGESTIONS
from backend.routers.data import get_state
from backend.routers.predictions import get_pred_state
from backend.routers.audit import get_audit_cache

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "llama-3.1-8b-instant"


@router.get("/status")
def ollama_status():
    available = check_llm_available()
    return {"available": available}


@router.get("/quick-suggestions")
def quick_suggestions():
    return list(QUICK_SUGGESTIONS.keys())


@router.post("/send")
def send_message(req: ChatRequest):
    state = get_state()
    pred_state = get_pred_state()
    audit_cache = get_audit_cache()

    ctx = build_context_dict(
        daily=state["daily"] if state["loaded"] else None,
        predictions=pred_state["predictions"],
        audit=audit_cache["audit"],
    )
    try:
        response = answer_query(req.message, ctx, model=req.model)
        return {"response": response}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
