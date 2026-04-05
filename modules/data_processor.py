"""
Data Processor Module — pandas 2.x compatible
Loads, cleans, and engineers features from the household power consumption CSV.
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime


float_pattern = re.compile(r'[-+]?\d*\.\d+|\d+')

def extract_mean_floats(s):
    if s is None:
        return np.nan
    if isinstance(s, (int, float, np.floating, np.integer)):
        return float(s)
    s_str = str(s).strip()
    try:
        return float(s_str)
    except (ValueError, TypeError):
        pass
    matches = float_pattern.findall(s_str)
    if not matches:
        return np.nan
    return float(np.mean([float(m) for m in matches]))


EXPECTED_NUMERIC = [
    'Global_active_power', 'Global_reactive_power', 'Global_intensity',
    'Voltage', 'Tariff_Rate', 'Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3'
]

DAILY_TARIFF_MAP = {
    (22, 6):  {'slot': 'Night_Off_Peak',  'rate': 3.75},
    (6,  12): {'slot': 'Morning_Peak',    'rate': 5.50},
    (12, 18): {'slot': 'Forenoon_Normal', 'rate': 4.75},
    (18, 22): {'slot': 'Evening_Peak',    'rate': 6.50},
}

SLABS_INDIA_DAILY = [
    (3.3,  4.50),
    (6.6,  5.50),
    (13.3, 7.00),
    (None, 8.50),
]


def get_daily_tariff(hour):
    for (start_h, end_h), info in DAILY_TARIFF_MAP.items():
        if start_h < end_h:
            if start_h <= hour < end_h:
                return info
        else:
            if hour >= start_h or hour < end_h:
                return info
    return {'slot': 'Unknown', 'rate': 0.0}


def safe_parse_datetime(row):
    sdate = str(row.get('Date', '')).strip()
    stime = str(row.get('Time', '')).strip()
    for fmt in ("%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(f"{sdate} {stime}", fmt)
        except (ValueError, TypeError):
            pass
    try:
        return pd.to_datetime(sdate + " " + stime, dayfirst=True, errors='coerce')
    except Exception:
        return pd.NaT


def compute_slab_charge(total_units, slabs):
    remaining = total_units
    prev_limit = 0.0
    charge = 0.0
    for limit, rate in slabs:
        if limit is None:
            charge += remaining * rate
            remaining = 0.0
            break
        slab_width = limit - prev_limit
        used = min(remaining, slab_width)
        charge += used * rate
        remaining -= used
        prev_limit = limit
        if remaining <= 0:
            break
    if remaining > 0:
        charge += remaining * slabs[-1][1]
    return float(charge)


def compute_final_slab_bill(total_units, slabs=None, fixed_charge=0.0,
                             duty_pct=0.0, surcharge_pct=0.0, min_bill=None):
    if slabs is None:
        slabs = SLABS_INDIA_DAILY
    energy_charge = compute_slab_charge(total_units, slabs)
    subtotal = energy_charge + fixed_charge
    duty = subtotal * (duty_pct / 100.0)
    surcharge = subtotal * (surcharge_pct / 100.0)
    total = subtotal + duty + surcharge
    if min_bill is not None:
        total = max(total, min_bill)
    return {
        'total_kwh':     float(total_units),
        'energy_charge': energy_charge,
        'fixed_charge':  fixed_charge,
        'duty':          duty,
        'surcharge':     surcharge,
        'final_bill':    float(total)
    }


def _ffill_bfill(series: pd.Series) -> pd.Series:
    """pandas 2.x safe forward-fill then back-fill."""
    return series.ffill().bfill()


def load_and_process(filepath):
    """
    Full pipeline: load CSV → clean → features → daily aggregation.
    Returns (df_raw, daily_df).
    """
    # ── 1. Load
    if hasattr(filepath, 'read'):
        df = pd.read_csv(filepath, low_memory=False)
    else:
        df = pd.read_csv(filepath, low_memory=False, encoding='utf-8')

    # ── 2. Clean numerics
    for col in EXPECTED_NUMERIC:
        if col in df.columns:
            df[col] = df[col].apply(extract_mean_floats).astype(float)

    # ── 3. Parse datetime
    df['datetime'] = df.apply(safe_parse_datetime, axis=1)
    df = df.dropna(subset=['datetime']).reset_index(drop=True)
    df = df.sort_values('datetime').reset_index(drop=True)

    # ── 4. Sampling interval
    diffs = df['datetime'].diff().dt.total_seconds().dropna()
    interval_min = float(diffs.median() / 60.0) if len(diffs) > 0 else 1.0

    # ── 5. Energy per record
    df['energy_kwh'] = df['Global_active_power'] * (interval_min / 60.0)

    # ── 6. TOU
    df['Time_Hour'] = df['datetime'].dt.hour
    df['Tariff_Time_Slot_Daily'] = df['Time_Hour'].apply(lambda x: get_daily_tariff(x)['slot'])
    df['Tariff_Rate_Daily']      = df['Time_Hour'].apply(lambda x: get_daily_tariff(x)['rate'])
    df['cost_tou']               = df['energy_kwh'] * df['Tariff_Rate_Daily']

    # ── 7. Daily aggregation
    df['date'] = df['datetime'].dt.to_period('D').dt.start_time

    agg_funcs = {
        'energy_kwh':           'sum',
        'cost_tou':             'sum',
        'Global_active_power':  'mean',
    }
    optional = {
        'Voltage':                 'mean',
        'Global_reactive_power':   'mean',
        'Global_intensity':        'mean',
        'Sub_metering_1':          'sum',
        'Sub_metering_2':          'sum',
        'Sub_metering_3':          'sum',
    }
    for col, func in optional.items():
        if col in df.columns:
            agg_funcs[col] = func

    daily = (
        df.groupby('date', as_index=False)
          .agg(agg_funcs)
          .rename(columns={'energy_kwh': 'daily_energy_kwh', 'cost_tou': 'daily_bill_tou'})
    )

    daily['records_count']     = df.groupby('date')['energy_kwh'].count().values
    daily['day_of_week']       = daily['date'].dt.dayofweek
    daily['day_of_year_sin']   = np.sin(2 * np.pi * daily['date'].dt.dayofyear / 365)
    daily['day_of_year_cos']   = np.cos(2 * np.pi * daily['date'].dt.dayofyear / 365)
    daily['month']             = daily['date'].dt.month
    daily['year']              = daily['date'].dt.year

    # Festival flag
    if 'Festival' in df.columns:
        def fest_flag(grp):
            s = grp.dropna().astype(str).str.strip().str.lower()
            return int(any(v not in ('none', 'nan', '', 'na') for v in s))
        daily['festival_flag'] = df.groupby('date')['Festival'].apply(fest_flag).values
    else:
        daily['festival_flag'] = 0

    # Categorical modes
    for col in ['Season', 'DayOfWeek', 'Tariff_Time_Slot_Daily']:
        if col in df.columns:
            def mode_or_na(grp):
                grp2 = grp.dropna().astype(str)
                return grp2.mode().iloc[0] if len(grp2) > 0 else 'NA'
            daily[col + '_mode'] = df.groupby('date')[col].apply(mode_or_na).values

    # ── 8. Slab bill
    daily['daily_bill_slab'] = daily['daily_energy_kwh'].apply(
        lambda u: compute_final_slab_bill(u)['final_bill']
    )

    # ── 9. Lag features
    for i in range(1, 4):
        daily[f'daily_energy_kwh_lag{i}'] = daily['daily_energy_kwh'].shift(i)

    # ── 10. Rolling features
    roll_cols = [
        'Global_active_power', 'Global_reactive_power', 'Voltage', 'Global_intensity',
        'Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3'
    ]
    for col in roll_cols:
        if col in daily.columns:
            daily[f'{col}_rollmean3'] = daily[col].rolling(3, min_periods=1).mean()
            daily[f'{col}_rollstd3']  = daily[col].rolling(3, min_periods=1).std().fillna(0)

    daily = daily.sort_values('date').reset_index(drop=True)

    # ── 11. Fill NaN — pandas 2.x compatible
    num_cols = daily.select_dtypes(include=[np.number]).columns.tolist()
    for col in num_cols:
        daily[col] = _ffill_bfill(daily[col]).fillna(0)

    return df, daily


def get_hourly_profile(df: pd.DataFrame) -> pd.DataFrame:
    if 'Time_Hour' not in df.columns:
        df = df.copy()
        df['Time_Hour'] = df['datetime'].dt.hour
    return df.groupby('Time_Hour')['Global_active_power'].mean().reset_index()


def get_data_summary(df: pd.DataFrame, daily: pd.DataFrame) -> dict:
    return {
        'total_records':       len(df),
        'date_start':          daily['date'].min().strftime('%Y-%m-%d') if len(daily) > 0 else 'N/A',
        'date_end':            daily['date'].max().strftime('%Y-%m-%d') if len(daily) > 0 else 'N/A',
        'total_days':          len(daily),
        'total_kwh':           float(daily['daily_energy_kwh'].sum()),
        'avg_daily_kwh':       float(daily['daily_energy_kwh'].mean()),
        'max_daily_kwh':       float(daily['daily_energy_kwh'].max()),
        'total_bill_tou':      float(daily['daily_bill_tou'].sum()),
        'total_bill_slab':     float(daily['daily_bill_slab'].sum()),
        'avg_daily_bill_slab': float(daily['daily_bill_slab'].mean()),
    }
