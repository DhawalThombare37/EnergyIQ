"""
Advisor Router — Energy optimization recommendations.
"""
import os
import sys
from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from modules.advisor import generate_recommendations
from backend.routers.data import get_state
from backend.routers.predictions import get_pred_state

router = APIRouter()


@router.get("/recommendations")
def recommendations():
    state = get_state()
    if not state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    pred_state = get_pred_state()
    try:
        recs = generate_recommendations(state["daily"], pred_state["predictions"])
        return recs
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
