"""
Energy Advisor Module
Rules-based energy optimization recommendations and audit engine.
"""

import numpy as np
import pandas as pd


def compute_efficiency_score(daily: pd.DataFrame) -> float:
    """
    Compute efficiency score 0–100 based on:
    - Coefficient of variation (lower = more stable = better)
    - Peak hour concentration (lower = better)
    - Average load factor
    """
    if daily is None or len(daily) == 0:
        return 50.0

    kwh = daily['daily_energy_kwh'].values
    mean_kwh = np.mean(kwh)
    if mean_kwh == 0:
        return 50.0

    cv = np.std(kwh) / mean_kwh  # lower is better
    cv_score = max(0, 100 - cv * 100)

    # Penalize for very high peak days
    max_kwh = np.max(kwh)
    peak_ratio = max_kwh / mean_kwh
    peak_score = max(0, 100 - (peak_ratio - 1) * 20)

    score = cv_score * 0.5 + peak_score * 0.5
    return round(min(100.0, max(0.0, score)), 1)


def generate_recommendations(daily: pd.DataFrame, predictions: dict = None) -> list:
    """
    Generate actionable energy-saving recommendations.
    Each recommendation is a dict with: title, detail, priority, saving_est, icon.
    """
    recs = []
    kwh = daily['daily_energy_kwh'].values
    mean_kwh = np.mean(kwh)
    max_kwh = np.max(kwh)

    # --- Recommendation 1: Peak shift ---
    if 'daily_bill_tou' in daily.columns and 'daily_bill_slab' in daily.columns:
        avg_tou = daily['daily_bill_tou'].mean()
        avg_slab = daily['daily_bill_slab'].mean()
        if avg_tou > avg_slab * 1.1:
            recs.append({
                'icon': '⏰',
                'title': 'Shift Loads to Off-Peak Hours',
                'detail': (
                    f"Your TOU billing (₹{avg_tou:.1f}/day) is significantly higher than slab billing "
                    f"(₹{avg_slab:.1f}/day). Moving 20% of Evening Peak (6PM–10PM) consumption "
                    "to Night Off-Peak (10PM–6AM) can reduce bills."
                ),
                'priority': 'HIGH',
                'saving_est': '15–25%',
            })

    # --- Recommendation 2: High peak day alert ---
    peak_ratio = max_kwh / mean_kwh if mean_kwh > 0 else 1
    if peak_ratio > 1.5:
        recs.append({
            'icon': '⚡',
            'title': 'Reduce Peak Demand Spikes',
            'detail': (
                f"Your maximum daily consumption ({max_kwh:.2f} kWh) is {peak_ratio:.1f}x "
                f"the average ({mean_kwh:.2f} kWh). Avoid running multiple high-power "
                "appliances simultaneously during morning/evening peaks."
            ),
            'priority': 'HIGH',
            'saving_est': '10–20%',
        })

    # --- Recommendation 3: Sub-metering imbalance ---
    sub_cols = ['Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3']
    available_subs = [c for c in sub_cols if c in daily.columns]
    if len(available_subs) >= 2:
        sub_totals = {c: daily[c].sum() for c in available_subs}
        max_sub = max(sub_totals, key=sub_totals.get)
        max_val = sub_totals[max_sub]
        total_sub = sum(sub_totals.values())
        if total_sub > 0 and max_val / total_sub > 0.6:
            names = {
                'Sub_metering_1': 'Kitchen/Washing zone',
                'Sub_metering_2': 'Laundry/Climate zone',
                'Sub_metering_3': 'Water Heater/AC zone'
            }
            recs.append({
                'icon': '🔌',
                'title': 'Load Imbalance Detected',
                'detail': (
                    f"{names.get(max_sub, max_sub)} accounts for over 60% of your sub-metered "
                    "consumption. Consider redistributing high-energy tasks across different times "
                    "or upgrading to more efficient appliances in this zone."
                ),
                'priority': 'MEDIUM',
                'saving_est': '5–15%',
            })

    # --- Recommendation 4: Voltage fluctuation ---
    if 'Voltage' in daily.columns:
        avg_volt = daily['Voltage'].mean()
        if avg_volt < 220 or avg_volt > 250:
            recs.append({
                'icon': '🔋',
                'title': 'Voltage Anomaly Detected',
                'detail': (
                    f"Average voltage ({avg_volt:.1f}V) is outside the optimal 220–250V range. "
                    "Install a voltage stabilizer or surge protector to prevent appliance damage "
                    "and energy waste."
                ),
                'priority': 'MEDIUM',
                'saving_est': '3–8%',
            })

    # --- Recommendation 5: Month-over-month trend ---
    if 'month' in daily.columns and len(daily) > 60:
        monthly = daily.groupby('month')['daily_energy_kwh'].mean()
        if len(monthly) >= 2:
            recent_month = monthly.iloc[-1]
            prev_month = monthly.iloc[-2]
            if prev_month > 0 and recent_month > prev_month * 1.1:
                recs.append({
                    'icon': '📈',
                    'title': 'Rising Consumption Trend',
                    'detail': (
                        f"Your average daily consumption increased by "
                        f"{((recent_month - prev_month) / prev_month * 100):.1f}% in the most recent month. "
                        "Check for newly added appliances or seasonal changes. Consider a smart energy monitor."
                    ),
                    'priority': 'MEDIUM',
                    'saving_est': '5–12%',
                })

    # --- Recommendation 6: Night Off-Peak opportunity ---
    recs.append({
        'icon': '🌙',
        'title': 'Maximise Night Off-Peak Usage',
        'detail': (
            "Night Off-Peak rate (₹3.75/unit, 10PM–6AM) is 42% cheaper than Evening Peak rate "
            "(₹6.50/unit). Schedule dishwashers, EV charging, and water heaters to run overnight."
        ),
        'priority': 'LOW',
        'saving_est': '8–18%',
    })

    # --- Recommendation 7: Appliance efficiency ---
    recs.append({
        'icon': '💡',
        'title': 'Upgrade to Energy Star Appliances',
        'detail': (
            "Older appliances consume 20–40% more energy. Switching to BEE 5-star rated "
            "refrigerators, ACs, and washing machines can deliver long-term savings. "
            "Look for ACs with inverter technology for variable-speed compressors."
        ),
        'priority': 'LOW',
        'saving_est': '15–30%',
    })

    # --- Prediction-based recommendation ---
    if predictions:
        pred_kwh = predictions.get('h_unit_pred', [])
        if len(pred_kwh) > 0:
            future_avg = np.mean(pred_kwh)
            if future_avg > mean_kwh * 1.05:
                recs.append({
                    'icon': '🔮',
                    'title': 'Predicted Consumption Increase',
                    'detail': (
                        f"AI models predict your average daily consumption will be "
                        f"{future_avg:.2f} kWh over the next {len(pred_kwh)} days, "
                        f"which is {((future_avg - mean_kwh) / mean_kwh * 100):.1f}% higher than historical average. "
                        "Proactively reduce usage during peak hours."
                    ),
                    'priority': 'HIGH',
                    'saving_est': '10–20%',
                })

    return recs


def run_energy_audit(daily: pd.DataFrame, raw_df: pd.DataFrame = None) -> dict:
    """
    Full energy audit report.
    """
    kwh = daily['daily_energy_kwh'].values
    bills = daily['daily_bill_slab'].values if 'daily_bill_slab' in daily.columns else np.zeros(len(kwh))

    efficiency_score = compute_efficiency_score(daily)

    # High consumption days
    threshold_95 = np.percentile(kwh, 95)
    high_days = daily[daily['daily_energy_kwh'] >= threshold_95]

    # Day-of-week pattern
    dow_avg = daily.groupby('day_of_week')['daily_energy_kwh'].mean().to_dict()
    dow_names = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
    dow_pattern = {dow_names.get(k, str(k)): round(v, 3) for k, v in dow_avg.items()}
    peak_dow = max(dow_pattern, key=dow_pattern.get)

    # Monthly averages
    if 'month' in daily.columns:
        month_avg = daily.groupby('month')['daily_energy_kwh'].mean().round(3).to_dict()
    else:
        month_avg = {}

    # Sub-metering breakdown
    sub_breakdown = {}
    for c in ['Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3']:
        if c in daily.columns:
            sub_breakdown[c] = float(daily[c].sum())

    # Bill stats
    total_bill = float(np.sum(bills))
    avg_daily_bill = float(np.mean(bills))

    findings = []
    cv = np.std(kwh) / np.mean(kwh) if np.mean(kwh) > 0 else 0
    if cv > 0.4:
        findings.append({'severity': 'HIGH',   'text': f'High load variability (CV={cv:.2f}). Suggests irregular appliance usage.'})
    if np.max(kwh) > np.mean(kwh) * 2:
        findings.append({'severity': 'HIGH',   'text': f'Extreme peak day detected: {np.max(kwh):.2f} kWh (2x+ average).'})
    if efficiency_score < 50:
        findings.append({'severity': 'HIGH',   'text': f'Low efficiency score ({efficiency_score}/100). Significant optimization potential.'})
    elif efficiency_score < 70:
        findings.append({'severity': 'MEDIUM', 'text': f'Moderate efficiency ({efficiency_score}/100). Room for improvement.'})
    else:
        findings.append({'severity': 'LOW',    'text': f'Good efficiency score ({efficiency_score}/100). Maintain current practices.'})
    if peak_dow in ['Sat', 'Sun']:
        findings.append({'severity': 'MEDIUM', 'text': f'Highest consumption on {peak_dow}s — consider scheduling tasks on weekdays.'})

    return {
        'efficiency_score': efficiency_score,
        'total_kwh': float(np.sum(kwh)),
        'avg_daily_kwh': float(np.mean(kwh)),
        'max_daily_kwh': float(np.max(kwh)),
        'min_daily_kwh': float(np.min(kwh)),
        'std_daily_kwh': float(np.std(kwh)),
        'total_bill_slab': total_bill,
        'avg_daily_bill': avg_daily_bill,
        'high_consumption_days': len(high_days),
        'threshold_95_kwh': float(threshold_95),
        'dow_pattern': dow_pattern,
        'peak_day_of_week': peak_dow,
        'monthly_avg_kwh': month_avg,
        'sub_metering_totals': sub_breakdown,
        'findings': findings,
        'total_days_analyzed': len(daily),
    }
