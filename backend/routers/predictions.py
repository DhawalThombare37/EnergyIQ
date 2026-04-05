"""
Predictions Router — XGBoost 4-model forecast pipeline.
"""
import os
import sys
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from modules.model_engine import run_predictions
from modules.advisor import run_energy_audit, generate_recommendations
from backend.routers.data import get_state

router = APIRouter()

_pred_state: dict = {"predictions": None, "run": False}


class PredictRequest(BaseModel):
    train_days: int = 150
    pred_days: int = 30


def _safe(val):
    if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val)
    if isinstance(val, np.ndarray):
        return [_safe(x) for x in val.tolist()]
    if isinstance(val, list):
        return [_safe(x) for x in val]
    return val


@router.get("/status")
def status():
    return {"run": _pred_state["run"]}


@router.post("/run")
def run_pred(req: PredictRequest):
    state = get_state()
    if not state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    try:
        preds = run_predictions(state["daily"], req.train_days, req.pred_days)
        _pred_state["predictions"] = preds
        _pred_state["run"] = True

        # Also update audit & recommendations
        audit = run_energy_audit(state["daily"], state["df"])
        recs = generate_recommendations(state["daily"], preds)

        result = {
            "dates": list(preds["dates"]),
            "h_unit_actual": _safe(preds["h_unit_actual"]),
            "h_unit_pred": _safe(preds["h_unit_pred"]),
            "h_bill_actual": _safe(preds["h_bill_actual"]),
            "h_bill_pred": _safe(preds["h_bill_pred"]),
            "i_unit_actual": _safe(preds["i_unit_actual"]),
            "i_unit_pred": _safe(preds["i_unit_pred"]),
            "i_bill_actual": _safe(preds["i_bill_actual"]),
            "i_bill_pred": _safe(preds["i_bill_pred"]),
            "h_unit_mape": _safe(preds["h_unit_mape"]),
            "h_bill_mape": _safe(preds["h_bill_mape"]),
            "i_unit_mape": _safe(preds["i_unit_mape"]),
            "i_bill_mape": _safe(preds["i_bill_mape"]),
        }
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/results")
def get_results():
    if not _pred_state["run"] or _pred_state["predictions"] is None:
        raise HTTPException(status_code=404, detail="No predictions available. Run predictions first.")
    preds = _pred_state["predictions"]
    return {
        "dates": list(preds["dates"]),
        "h_unit_actual": _safe(preds["h_unit_actual"]),
        "h_unit_pred": _safe(preds["h_unit_pred"]),
        "h_bill_actual": _safe(preds["h_bill_actual"]),
        "h_bill_pred": _safe(preds["h_bill_pred"]),
        "i_unit_actual": _safe(preds["i_unit_actual"]),
        "i_unit_pred": _safe(preds["i_unit_pred"]),
        "i_bill_actual": _safe(preds["i_bill_actual"]),
        "i_bill_pred": _safe(preds["i_bill_pred"]),
        "h_unit_mape": _safe(preds["h_unit_mape"]),
        "h_bill_mape": _safe(preds["h_bill_mape"]),
        "i_unit_mape": _safe(preds["i_unit_mape"]),
        "i_bill_mape": _safe(preds["i_bill_mape"]),
    }


def get_pred_state():
    return _pred_state
