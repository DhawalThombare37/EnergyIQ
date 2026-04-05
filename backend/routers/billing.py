"""
Billing Router — TOU vs Slab projections, off-peak savings.
"""
import os
import sys
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from modules.billing_engine import project_monthly_bill, get_tariff_slot_cost_breakdown, get_peak_hour_analysis
from backend.routers.data import get_state
from backend.routers.predictions import get_pred_state

router = APIRouter()


def _safe(val):
    if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val)
    return val


@router.get("/projection")
def projection():
    state = get_state()
    if not state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    pred_state = get_pred_state()
    daily = state["daily"]
    preds = pred_state["predictions"]

    if preds is not None:
        src_kwh = preds["h_unit_pred"]
        src_bills = preds["h_bill_pred"]
        src_dates = list(preds["dates"])
        source = "predictions"
    else:
        src_kwh = daily.tail(30)["daily_energy_kwh"].values
        src_bills = daily.tail(30)["daily_bill_slab"].values
        src_dates = daily.tail(30)["date"].dt.strftime("%Y-%m-%d").tolist()
        source = "historical"

    proj = project_monthly_bill(src_kwh)
    return {
        "source": source,
        "dates": list(src_dates),
        "kwh_series": [_safe(x) for x in src_kwh],
        "bill_series": [_safe(x) for x in src_bills],
        "total_kwh": _safe(proj["total_kwh"]),
        "slab_bill_total": _safe(proj["slab_bill_total"]),
        "tou_bill_total": _safe(proj["tou_bill_total"]),
    }


@router.get("/breakdown")
def breakdown():
    state = get_state()
    if not state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    bd = get_tariff_slot_cost_breakdown(state["df"])
    if not bd or "absolute" not in bd:
        return []
    return [{"slot": k, "cost": _safe(v)} for k, v in bd["absolute"].items()]


class SavingsRequest(BaseModel):
    monthly_kwh: float
    shift_pct: int = 20


@router.post("/savings-calculator")
def savings_calculator(req: SavingsRequest):
    shifted = req.monthly_kwh * req.shift_pct / 100
    orig_cost = shifted * 6.50
    new_cost = shifted * 3.75
    saving = orig_cost - new_cost
    return {
        "shifted_kwh": float(f"{float(shifted):.2f}"),
        "cost_at_peak": float(f"{float(orig_cost):.2f}"),
        "cost_at_off_peak": float(f"{float(new_cost):.2f}"),
        "monthly_saving": float(f"{float(saving):.2f}"),
        "annual_saving": float(f"{float(saving * 12):.2f}"),
    }
