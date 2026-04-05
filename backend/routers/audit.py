"""
Audit Router — Energy audit and peak hour analysis.
"""
import os
import sys
import numpy as np
from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from modules.advisor import run_energy_audit, compute_efficiency_score
from modules.billing_engine import get_peak_hour_analysis
from backend.routers.data import get_state

router = APIRouter()

_audit_cache: dict = {"audit": None}


def _safe(val):
    if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val)
    if isinstance(val, dict):
        return {k: _safe(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_safe(x) for x in val]
    return val


@router.post("/run")
def run_audit():
    state = get_state()
    if not state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    try:
        audit = run_energy_audit(state["daily"], state["df"])
        _audit_cache["audit"] = audit
        return _safe(audit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/results")
def get_results():
    state = get_state()
    if not state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    if _audit_cache["audit"] is None:
        # Auto-run
        audit = run_energy_audit(state["daily"], state["df"])
        _audit_cache["audit"] = audit
    return _safe(_audit_cache["audit"])


@router.get("/peak-hours")
def peak_hours():
    state = get_state()
    if not state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    try:
        hourly = get_peak_hour_analysis(state["df"])
        if hasattr(hourly, "to_dict"):
            return hourly.reset_index().to_dict(orient="records")
        return []
    except Exception:
        return []


@router.get("/efficiency-score")
def efficiency_score():
    state = get_state()
    if not state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    score = compute_efficiency_score(state["daily"])
    return {"score": score}


def get_audit_cache():
    return _audit_cache
