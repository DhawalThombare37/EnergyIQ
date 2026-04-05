"""
Data Router — CSV upload, processing, summary, raw & daily data.
"""
import io
import os
import sys
import json
import numpy as np
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from modules.data_processor import load_and_process, get_data_summary, get_hourly_profile

router = APIRouter()

# In-memory store (per-process state)
_state: dict = {"df": None, "daily": None, "loaded": False}

DEFAULT_CSV = os.path.join(os.path.dirname(__file__), "../../household_power_consumption_with_tariff.csv")


def _safe(val):
    """Convert numpy/nan values to JSON-safe Python types."""
    if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val)
    if isinstance(val, np.ndarray):
        return val.tolist()
    return val


def _df_to_records(df: pd.DataFrame, limit: int = 500) -> list:
    df2 = df.head(limit).copy()
    for col in df2.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns:
        df2[col] = df2[col].astype(str)
    records = df2.to_dict(orient="records")
    return [{k: _safe(v) for k, v in row.items()} for row in records]


@router.get("/status")
def status():
    return {"loaded": _state["loaded"]}


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload and process a CSV file."""
    try:
        content = await file.read()
        buf = io.StringIO(content.decode("utf-8", errors="replace"))
        df, daily = load_and_process(buf)
        _state["df"] = df
        _state["daily"] = daily
        _state["loaded"] = True
        return {"success": True, "records": len(df), "days": len(daily)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/load-default")
def load_default():
    """Load the bundled default CSV dataset."""
    if not os.path.exists(DEFAULT_CSV):
        raise HTTPException(status_code=404, detail="Default dataset not found.")
    try:
        df, daily = load_and_process(DEFAULT_CSV)
        _state["df"] = df
        _state["daily"] = daily
        _state["loaded"] = True
        return {"success": True, "records": len(df), "days": len(daily)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/summary")
def summary():
    if not _state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    s = get_data_summary(_state["df"], _state["daily"])
    return {k: _safe(v) for k, v in s.items()}


@router.get("/daily")
def daily_data(limit: int = 500):
    if not _state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    return _df_to_records(_state["daily"], limit)


@router.get("/raw")
def raw_data(limit: int = 200):
    if not _state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    cols = [c for c in [
        "datetime", "Date", "Time", "Global_active_power", "Global_reactive_power",
        "Voltage", "Sub_metering_1", "Sub_metering_2", "Sub_metering_3",
        "Tariff_Time_Slot_Daily", "Tariff_Rate_Daily", "energy_kwh", "cost_tou",
    ] if c in _state["df"].columns]
    return _df_to_records(_state["df"][cols], limit)


@router.get("/stats")
def stats():
    if not _state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    df = _state["df"]
    daily = _state["daily"]
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    raw_stats = df[num_cols[:8]].describe().round(3).to_dict()
    d_num = daily.select_dtypes(include=[np.number]).columns[:8].tolist()
    daily_stats = daily[d_num].describe().round(3).to_dict()
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    miss_df = pd.DataFrame({"missing_count": missing, "missing_pct": missing_pct})
    miss_df = miss_df[miss_df["missing_count"] > 0]
    return {
        "raw_stats": raw_stats,
        "daily_stats": daily_stats,
        "missing": miss_df.to_dict(orient="index"),
    }


@router.get("/hourly-profile")
def hourly_profile():
    if not _state["loaded"]:
        raise HTTPException(status_code=400, detail="No data loaded.")
    try:
        hp = get_hourly_profile(_state["df"])
        return hp.to_dict(orient="records") if isinstance(hp, pd.DataFrame) else []
    except Exception:
        return []


def get_state():
    return _state
