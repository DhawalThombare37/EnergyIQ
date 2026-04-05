"""
Billing Engine Module — pandas 2.x compatible
"""

import numpy as np
import pandas as pd
from modules.data_processor import SLABS_INDIA_DAILY, DAILY_TARIFF_MAP, compute_final_slab_bill


def project_monthly_bill(pred_kwh_array) -> dict:
    pred_kwh_array = np.asarray(pred_kwh_array, dtype=float)
    total_kwh = float(np.sum(pred_kwh_array))
    daily_bills = [compute_final_slab_bill(float(k))['final_bill'] for k in pred_kwh_array]
    avg_tou_rate = (8 * 3.75 + 6 * 5.50 + 6 * 4.75 + 4 * 6.50) / 24.0
    tou_bill = total_kwh * avg_tou_rate
    return {
        'total_kwh':          total_kwh,
        'avg_daily_kwh':      float(np.mean(pred_kwh_array)),
        'slab_bill_total':    float(np.sum(daily_bills)),
        'tou_bill_total':     tou_bill,
        'avg_daily_bill_slab':float(np.mean(daily_bills)),
        'daily_bills':        daily_bills,
    }


def get_tariff_slot_cost_breakdown(df: pd.DataFrame) -> dict:
    if 'Tariff_Time_Slot_Daily' not in df.columns or 'cost_tou' not in df.columns:
        return {}
    grouped = df.groupby('Tariff_Time_Slot_Daily')['cost_tou'].sum()
    total = float(grouped.sum())
    if total == 0:
        return {}
    breakdown = {str(slot): float(cost) for slot, cost in grouped.items()}
    pct = {str(slot): float(cost / total * 100) for slot, cost in grouped.items()}
    return {'absolute': breakdown, 'percentage': pct, 'total': total}


def get_peak_hour_analysis(df: pd.DataFrame) -> pd.DataFrame:
    if 'Time_Hour' not in df.columns:
        df = df.copy()
        if 'datetime' in df.columns:
            df['Time_Hour'] = pd.to_datetime(df['datetime']).dt.hour
        else:
            return pd.DataFrame({'hour': range(24), 'avg_power': [0]*24,
                                  'max_power': [0]*24, 'std_power': [0]*24})
    result = (
        df.groupby('Time_Hour')['Global_active_power']
          .agg(['mean', 'max', 'std'])
          .reset_index()
    )
    result.columns = ['hour', 'avg_power', 'max_power', 'std_power']
    result['std_power'] = result['std_power'].fillna(0)
    return result


def savings_from_shift(df: pd.DataFrame, shift_from_slot: str,
                        shift_to_slot: str = 'Night_Off_Peak',
                        shift_pct: float = 0.20) -> dict:
    slot_rates = {info['slot']: info['rate'] for _, info in DAILY_TARIFF_MAP.items()}
    from_rate = slot_rates.get(shift_from_slot, 6.50)
    to_rate   = slot_rates.get(shift_to_slot, 3.75)

    if 'Tariff_Time_Slot_Daily' in df.columns and 'energy_kwh' in df.columns:
        peak_energy = float(df[df['Tariff_Time_Slot_Daily'] == shift_from_slot]['energy_kwh'].sum())
    elif 'daily_energy_kwh' in df.columns:
        peak_energy = float(df['daily_energy_kwh'].sum() * 0.3)
    else:
        peak_energy = 0.0

    shifted_kwh    = peak_energy * shift_pct
    original_cost  = shifted_kwh * from_rate
    new_cost       = shifted_kwh * to_rate
    saving         = original_cost - new_cost
    return {
        'shifted_kwh':   shifted_kwh,
        'original_cost': original_cost,
        'new_cost':      new_cost,
        'saving':        saving,
        'saving_pct':    (saving / original_cost * 100) if original_cost > 0 else 0,
    }
