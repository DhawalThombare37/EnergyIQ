"""
EnergyIQ — AI-Driven Energy Auditor Platform
Main Streamlit App  |  Pandas 2.x • XGBoost 3.x • Plotly 6.x compatible
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# ── Page config (MUST be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="EnergyIQ — AI Energy Auditor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load custom CSS ──────────────────────────────────────────────────────────
_css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(_css_path):
    with open(_css_path, encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

# ── Module imports ───────────────────────────────────────────────────────────
from modules.data_processor import (
    load_and_process, get_data_summary, get_hourly_profile,
)
from modules.model_engine import run_predictions
from modules.billing_engine import (
    project_monthly_bill, get_tariff_slot_cost_breakdown, get_peak_hour_analysis,
)
from modules.advisor import (
    generate_recommendations, run_energy_audit, compute_efficiency_score,
)
from modules.llm_agent import (
    answer_query, build_context_dict, check_ollama_available,
    QUICK_SUGGESTIONS, DEFAULT_MODEL,
)
from modules.visualizer import (
    plot_actual_vs_predicted, plot_daily_trend, plot_bill_projection,
    plot_peak_heatmap, plot_tariff_breakdown, plot_efficiency_gauge,
    plot_sub_metering, plot_monthly_bar, plot_dow_bar,
)

# ── Session state defaults ───────────────────────────────────────────────────
_DEFAULTS = {
    'df': None, 'daily': None, 'predictions': None,
    'audit': None, 'recommendations': None,
    'chat_history': [], 'data_loaded': False, 'predictions_run': False,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

DEFAULT_CSV = os.path.join(os.path.dirname(__file__), "household_power_consumption_with_tariff.csv")

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 0.5rem;">
      <div style="font-size:2.4rem;">⚡</div>
      <div style="font-size:1.25rem;font-weight:800;color:#00d4ff;">EnergyIQ</div>
      <div style="font-size:0.7rem;color:#cbd5e1;letter-spacing:0.12em;text-transform:uppercase;">
        AI Energy Auditor
      </div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    page = st.radio(
        "nav", label_visibility="collapsed",
        options=[
            "🏠 Dashboard",
            "📤 Data Explorer",
            "🔮 Prediction Engine",
            "💰 Bill Estimator",
            "🔍 Energy Audit",
            "💡 Optimization Advisor",
            "🤖 AI Chat Agent",
        ],
    )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.78rem;color:#94a3b8;font-weight:600;'>📁 DATA SOURCE</p>",
        unsafe_allow_html=True,
    )
    use_default = st.checkbox("Use bundled dataset", value=True)

    if use_default and os.path.exists(DEFAULT_CSV):
        csv_source = DEFAULT_CSV
        st.success("Bundled dataset ready ✓")
    else:
        uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
        csv_source = uploaded

    if st.button("⚡ Load & Process Data", use_container_width=True):
        if csv_source is None:
            st.error("Select a data source first.")
        else:
            with st.spinner("Processing — please wait…"):
                try:
                    df, daily = load_and_process(csv_source)
                    st.session_state.df              = df
                    st.session_state.daily           = daily
                    st.session_state.data_loaded     = True
                    st.session_state.predictions     = None
                    st.session_state.predictions_run = False
                    st.session_state.audit           = None
                    st.session_state.recommendations = None
                    st.success(f"✓ {len(df):,} records · {len(daily)} days")
                except Exception as exc:
                    st.error(f"Load error: {exc}")

    if st.session_state.data_loaded:
        d = st.session_state.daily
        st.markdown(f"""
        <div style="background:rgba(0,212,255,0.07);border:1px solid rgba(0,212,255,0.2);
                    border-radius:10px;padding:0.65rem 0.9rem;margin-top:0.5rem;font-size:0.78rem;">
          <span style="color:#00d4ff;font-weight:700;">Dataset</span><br>
          <span style="color:#cbd5e1;">{len(d)} days &nbsp;·&nbsp; {len(st.session_state.df):,} records</span><br>
          <span style="color:#94a3b8;">{d['date'].min().strftime('%b %Y')} → {d['date'].max().strftime('%b %Y')}</span>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def _need_data():
    if not st.session_state.data_loaded:
        st.markdown("""
        <div style='text-align:center;padding:4rem 2rem;'>
          <div style='font-size:3rem;margin-bottom:1rem;'>📂</div>
          <div style='font-size:1.2rem;font-weight:700;color:#f0f4f8;margin-bottom:0.5rem;'>
            No Data Loaded</div>
          <div style='color:#cbd5e1;'>
            Use the sidebar to load your dataset first.</div>
        </div>""", unsafe_allow_html=True)
        return False
    return True


def kpi(label, value, sub="", icon="", color="#00d4ff"):
    return f"""
<div class='kpi-card'>
  <div class='kpi-icon'>{icon}</div>
  <div class='kpi-label'>{label}</div>
  <div class='kpi-value' style='color:{color};'>{value}</div>
  <div class='kpi-sub'>{sub}</div>
</div>"""


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 1 — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    st.markdown("<div class='page-title'><span class='grad-text'>⚡ EnergyIQ Dashboard</span></div>",
                unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>AI-Powered Energy Intelligence Platform</div>",
                unsafe_allow_html=True)

    if not st.session_state.data_loaded:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown("""
            <div style='text-align:center;padding:2.5rem 1rem;'>
              <div style='font-size:3.5rem;margin-bottom:0.8rem;'>⚡</div>
              <div style='font-size:1.5rem;font-weight:800;color:#00d4ff;margin-bottom:0.5rem;'>
                Welcome to EnergyIQ</div>
              <div style='color:#cbd5e1;font-size:0.95rem;max-width:380px;margin:0 auto 1.5rem;'>
                Your AI-driven digital energy auditor. Load your dataset from the sidebar.
              </div>
            </div>""", unsafe_allow_html=True)
            r1, r2 = st.columns(2)
            feats = [
                ("🔮", "30-Day Forecasts",   "XGBoost ML predictions"),
                ("💰", "Bill Estimation",    "TOU & slab billing"),
                ("🔍", "Energy Audit",       "Efficiency scoring"),
                ("🤖", "AI Chat Agent",      "Llama 3.2 powered"),
            ]
            for i, (ic, ttl, desc) in enumerate(feats):
                with (r1 if i % 2 == 0 else r2):
                    st.markdown(f"""
                    <div class='kpi-card' style='margin-bottom:0.8rem;'>
                      <div style='font-size:1.6rem;margin-bottom:0.3rem;'>{ic}</div>
                      <div style='font-weight:700;color:#f0f4f8;'>{ttl}</div>
                      <div style='font-size:0.78rem;color:#cbd5e1;'>{desc}</div>
                    </div>""", unsafe_allow_html=True)
    else:
        daily   = st.session_state.daily
        summary = get_data_summary(st.session_state.df, daily)
        eff     = compute_efficiency_score(daily)

        if st.session_state.audit is None:
            with st.spinner("Running audit…"):
                st.session_state.audit = run_energy_audit(daily, st.session_state.df)
        audit = st.session_state.audit

        # KPI row
        c1, c2, c3, c4 = st.columns(4)
        eff_col = "#10b981" if eff >= 70 else "#f59e0b" if eff >= 50 else "#ef4444"
        with c1: st.markdown(kpi("Total Energy",       f"{summary['total_kwh']:.0f} kWh",  "Total consumed",     "⚡"), unsafe_allow_html=True)
        with c2: st.markdown(kpi("Avg Daily Usage",    f"{summary['avg_daily_kwh']:.2f} kWh", "per day",         "📊", "#9b59fb"), unsafe_allow_html=True)
        with c3: st.markdown(kpi("Avg Daily Bill",     f"₹{summary['avg_daily_bill_slab']:.0f}", "Slab billing", "💰", "#f59e0b"), unsafe_allow_html=True)
        with c4: st.markdown(kpi("Efficiency Score",   f"{eff}",  "/ 100",                  "🏆", eff_col), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        cl, cr = st.columns([2, 1])
        with cl:
            st.plotly_chart(plot_daily_trend(daily), use_container_width=True,
                            config={"displayModeBar": False})
        with cr:
            st.plotly_chart(plot_efficiency_gauge(eff), use_container_width=True,
                            config={"displayModeBar": False})
            st.markdown("""<div class='section-card'>
              <div style='font-size:0.75rem;font-weight:700;color:#94a3b8;margin-bottom:0.5rem;'>
                QUICK STATS</div>""", unsafe_allow_html=True)
            for lbl, val in [
                ("Date Range",       f"{summary['date_start']} → {summary['date_end']}"),
                ("Total Days",       f"{summary['total_days']}"),
                ("Peak Day",         f"{summary['max_daily_kwh']:.2f} kWh"),
                ("Total Bill",       f"₹{summary['total_bill_slab']:.0f}"),
                ("High-Usage Days",  f"{audit.get('high_consumption_days',0)} days"),
            ]:
                st.markdown(
                    f"<div class='stat-row'><span class='stat-label'>{lbl}</span>"
                    f"<span class='stat-value'>{val}</span></div>",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        fig_m = plot_monthly_bar(daily)
        if fig_m:
            st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 2 — DATA EXPLORER
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📤 Data Explorer":
    st.markdown("<div class='page-title'><span class='grad-text'>📤 Data Explorer</span></div>",
                unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Inspect and understand your energy dataset</div>",
                unsafe_allow_html=True)
    if not _need_data():
        st.stop()

    df    = st.session_state.df
    daily = st.session_state.daily

    tab1, tab2, tab3 = st.tabs(["📋 Raw Data", "📅 Daily Aggregated", "📈 Statistics"])

    with tab1:
        cols_show = [c for c in [
            'datetime','Date','Time','Global_active_power','Global_reactive_power',
            'Voltage','Sub_metering_1','Sub_metering_2','Sub_metering_3',
            'Tariff_Time_Slot_Daily','Tariff_Rate_Daily','energy_kwh','cost_tou',
        ] if c in df.columns]
        st.markdown(
            f"<p style='color:#cbd5e1;'><b style='color:#f0f4f8;'>{len(df):,}</b> records "
            f"| <b style='color:#f0f4f8;'>{len(df.columns)}</b> columns</p>",
            unsafe_allow_html=True,
        )
        n = st.slider("Rows to preview", 10, 500, 50)
        st.dataframe(df[cols_show].head(n), use_container_width=True)

    with tab2:
        daily_cols = [c for c in [
            'date','daily_energy_kwh','daily_bill_slab','daily_bill_tou',
            'Global_active_power','Voltage',
            'Sub_metering_1','Sub_metering_2','Sub_metering_3',
            'day_of_week','month',
        ] if c in daily.columns]
        st.markdown(
            f"<p style='color:#cbd5e1;'><b style='color:#f0f4f8;'>{len(daily)}</b> daily records</p>",
            unsafe_allow_html=True,
        )
        n2 = st.slider("Rows to preview ", 5, len(daily), min(30, len(daily)))
        st.dataframe(daily[daily_cols].head(n2).round(4), use_container_width=True)

    with tab3:
        ca, cb = st.columns(2)
        with ca:
            st.markdown("#### Raw Data Statistics")
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            st.dataframe(df[num_cols[:8]].describe().round(3), use_container_width=True)
        with cb:
            st.markdown("#### Daily Aggregated Statistics")
            d_num = daily.select_dtypes(include=[np.number]).columns[:8].tolist()
            st.dataframe(daily[d_num].describe().round(3), use_container_width=True)

        st.markdown("#### Missing Value Analysis")
        missing     = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        miss_df     = pd.DataFrame({"Missing Count": missing, "Missing %": missing_pct})
        miss_df     = miss_df[miss_df["Missing Count"] > 0]
        if miss_df.empty:
            st.success("✅ No missing values in the dataset!")
        else:
            st.dataframe(miss_df, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 3 — PREDICTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🔮 Prediction Engine":
    st.markdown("<div class='page-title'><span class='grad-text'>🔮 Prediction Engine</span></div>",
                unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>XGBoost 4-model forecasting pipeline</div>",
                unsafe_allow_html=True)
    if not _need_data():
        st.stop()

    max_train = max(1, len(st.session_state.daily) - 5)
    c1, c2, c3 = st.columns(3)
    with c1:
        train_days = st.number_input("Training Days", min_value=10, max_value=max_train,
                                     value=min(150, max_train - 10), step=10)
    with c2:
        pred_days = st.number_input("Prediction Days", min_value=1,
                                    max_value=max(1, len(st.session_state.daily) - int(train_days)),
                                    value=min(30, max(1, len(st.session_state.daily) - int(train_days))),
                                    step=1)
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button("🚀 Run Predictions", use_container_width=True)

    if run_btn:
        with st.spinner("Training XGBoost models… this may take 30–60 seconds."):
            try:
                preds = run_predictions(st.session_state.daily, int(train_days), int(pred_days))
                st.session_state.predictions     = preds
                st.session_state.predictions_run = True
                st.session_state.audit           = run_energy_audit(
                    st.session_state.daily, st.session_state.df
                )
                st.session_state.recommendations = generate_recommendations(
                    st.session_state.daily, preds
                )
                st.success("✅ Models trained successfully!")
            except Exception as exc:
                st.error(f"Prediction error: {exc}")
                st.stop()

    preds = st.session_state.predictions
    if preds is None:
        st.markdown("""
        <div style='text-align:center;padding:3rem;background:rgba(0,212,255,0.04);
                    border:1px solid rgba(0,212,255,0.12);border-radius:14px;'>
          <div style='font-size:2.5rem;margin-bottom:0.6rem;'>🔮</div>
          <div style='font-weight:700;color:#f0f4f8;margin-bottom:0.4rem;'>Ready to Predict</div>
          <div style='color:#cbd5e1;'>Configure parameters above and click Run Predictions.</div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    # MAPE scorecards
    m1, m2, m3, m4 = st.columns(4)
    for col, lbl, val in zip(
        [m1, m2, m3, m4],
        ["🏠 kWh MAPE", "🏠 Bill MAPE", "🏭 kWh MAPE", "🏭 Bill MAPE"],
        [preds['h_unit_mape'], preds['h_bill_mape'], preds['i_unit_mape'], preds['i_bill_mape']],
    ):
        c = "#10b981" if val < 10 else "#f59e0b" if val < 20 else "#ef4444"
        with col:
            st.markdown(kpi(lbl, f"{val:.1f}%", "Lower is better", "", c), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    dates = preds['dates']

    cl, cr = st.columns(2)
    with cl:
        st.plotly_chart(
            plot_actual_vs_predicted(dates, preds['h_unit_actual'], preds['h_unit_pred'],
                                     "Household kWh — Actual vs Predicted",
                                     "Actual kWh", "Predicted kWh", "kWh"),
            use_container_width=True, config={"displayModeBar": False},
        )
    with cr:
        st.plotly_chart(
            plot_actual_vs_predicted(dates, preds['h_bill_actual'], preds['h_bill_pred'],
                                     "Household Slab Bill — Actual vs Predicted",
                                     "Actual ₹", "Predicted ₹", "₹"),
            use_container_width=True, config={"displayModeBar": False},
        )

    cl2, cr2 = st.columns(2)
    with cl2:
        st.plotly_chart(
            plot_actual_vs_predicted(dates, preds['i_unit_actual'], preds['i_unit_pred'],
                                     "Industrial kWh — Actual vs Predicted",
                                     "Actual kWh", "Predicted kWh", "kWh"),
            use_container_width=True, config={"displayModeBar": False},
        )
    with cr2:
        st.plotly_chart(
            plot_actual_vs_predicted(dates, preds['i_bill_actual'], preds['i_bill_pred'],
                                     "Industrial TOU Bill — Actual vs Predicted",
                                     "Actual ₹", "Predicted ₹", "₹"),
            use_container_width=True, config={"displayModeBar": False},
        )

    # Downloads
    st.markdown("---")
    st.markdown("### 💾 Download Predictions")
    dl1, dl2 = st.columns(2)
    with dl1:
        h = pd.DataFrame({
            "date":                dates,
            "actual_units_kwh":    preds['h_unit_actual'],
            "predicted_units_kwh": preds['h_unit_pred'],
            "actual_slab_bill":    preds['h_bill_actual'],
            "predicted_slab_bill": preds['h_bill_pred'],
        })
        st.download_button("⬇️ Household CSV", h.to_csv(index=False).encode(),
                           "household_predictions.csv", "text/csv", use_container_width=True)
    with dl2:
        ind = pd.DataFrame({
            "date":                dates,
            "actual_units_kwh":    preds['i_unit_actual'],
            "predicted_units_kwh": preds['i_unit_pred'],
            "actual_tou_bill":     preds['i_bill_actual'],
            "predicted_tou_bill":  preds['i_bill_pred'],
        })
        st.download_button("⬇️ Industrial CSV", ind.to_csv(index=False).encode(),
                           "industrial_predictions.csv", "text/csv", use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 4 — BILL ESTIMATOR
# ═══════════════════════════════════════════════════════════════════════════
elif page == "💰 Bill Estimator":
    st.markdown("<div class='page-title'><span class='grad-text'>💰 Bill Estimator</span></div>",
                unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>TOU vs Slab comparison and monthly projections</div>",
                unsafe_allow_html=True)
    if not _need_data():
        st.stop()

    daily  = st.session_state.daily
    df_raw = st.session_state.df
    bd     = get_tariff_slot_cost_breakdown(df_raw)

    c1, c2 = st.columns(2)
    with c1:
        if bd:
            st.plotly_chart(plot_tariff_breakdown(bd), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("No tariff breakdown data available in this dataset.")

    with c2:
        st.markdown("#### Tariff Rates (TOU)")
        st.dataframe(pd.DataFrame([
            {"Slot": "🌙 Night Off-Peak",  "Hours": "10PM–6AM",  "₹/kWh": 3.75},
            {"Slot": "🌅 Morning Peak",    "Hours": "6AM–12PM",  "₹/kWh": 5.50},
            {"Slot": "☀️ Forenoon Normal", "Hours": "12PM–6PM",  "₹/kWh": 4.75},
            {"Slot": "🌆 Evening Peak",    "Hours": "6PM–10PM",  "₹/kWh": 6.50},
        ]), hide_index=True, use_container_width=True)

        st.markdown("#### Daily Slab Rates")
        st.dataframe(pd.DataFrame([
            {"Daily (kWh)": "0 – 3.3",   "₹/unit": 4.50},
            {"Daily (kWh)": "3.3 – 6.6", "₹/unit": 5.50},
            {"Daily (kWh)": "6.6 – 13.3","₹/unit": 7.00},
            {"Daily (kWh)": "> 13.3",    "₹/unit": 8.50},
        ]), hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### 30-Day Bill Projection")
    preds = st.session_state.predictions
    if preds is None:
        src_kwh   = daily.tail(30)['daily_energy_kwh'].values
        src_bills = daily.tail(30)['daily_bill_slab'].values
        src_dates = daily.tail(30)['date'].dt.strftime('%Y-%m-%d').tolist()
        note = "*(using last 30 historical days — run Prediction Engine for AI forecast)*"
        st.caption(note)
    else:
        src_kwh   = preds['h_unit_pred']
        src_bills = preds['h_bill_pred']
        src_dates = preds['dates']

    proj = project_monthly_bill(src_kwh)
    p1, p2, p3, p4 = st.columns(4)
    diff = proj['slab_bill_total'] - proj['tou_bill_total']
    save_label = "TOU Saves" if diff < 0 else "Slab Saves"
    with p1: st.markdown(kpi("Projected kWh",    f"{proj['total_kwh']:.1f}",       "30 days",    "⚡"),      unsafe_allow_html=True)
    with p2: st.markdown(kpi("Slab Bill (30d)",  f"₹{proj['slab_bill_total']:.0f}", "Estimated", "🧮", "#9b59fb"), unsafe_allow_html=True)
    with p3: st.markdown(kpi("TOU Bill (30d)",   f"₹{proj['tou_bill_total']:.0f}",  "Estimated", "🕐", "#f59e0b"), unsafe_allow_html=True)
    with p4:
        c = "#10b981" if abs(diff) > 0 else "#94a3b8"
        st.markdown(kpi(save_label, f"₹{abs(diff):.0f}", "Over 30 days", "💡", c), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.plotly_chart(
        plot_bill_projection(src_dates, src_bills, src_kwh),
        use_container_width=True, config={"displayModeBar": False},
    )

    # Savings calculator
    st.markdown("---")
    st.markdown("### 🧮 Off-Peak Shift Savings Calculator")
    sc1, sc2 = st.columns(2)
    with sc1:
        monthly_input = st.number_input("Monthly Usage (kWh)", 10.0, 5000.0,
                                        float(proj['total_kwh']), 10.0)
        shift         = st.slider("% to shift to Night Off-Peak", 5, 50, 20)
    with sc2:
        shifted     = monthly_input * shift / 100
        orig_cost   = shifted * 6.50
        new_cost    = shifted * 3.75
        saving      = orig_cost - new_cost
        st.markdown(f"""
        <div class='section-card'>
          <div style='font-size:0.75rem;color:#94a3b8;margin-bottom:0.8rem;font-weight:700;'>
            ESTIMATED SAVINGS</div>
          <div class='stat-row'><span class='stat-label'>Energy shifted</span>
            <span class='stat-value'>{shifted:.1f} kWh</span></div>
          <div class='stat-row'><span class='stat-label'>Cost at Evening Peak</span>
            <span class='stat-value'>₹{orig_cost:.0f}</span></div>
          <div class='stat-row'><span class='stat-label'>Cost at Off-Peak</span>
            <span class='stat-value'>₹{new_cost:.0f}</span></div>
          <div class='stat-row'><span class='stat-label'>Monthly Saving</span>
            <span class='stat-value' style='color:#10b981;font-size:1.2rem;'>₹{saving:.0f}</span></div>
          <div class='stat-row'><span class='stat-label'>Annual Saving</span>
            <span class='stat-value' style='color:#10b981;'>₹{saving*12:.0f}</span></div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 5 — ENERGY AUDIT
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🔍 Energy Audit":
    st.markdown("<div class='page-title'><span class='grad-text'>🔍 Energy Audit Report</span></div>",
                unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Comprehensive energy efficiency analysis</div>",
                unsafe_allow_html=True)
    if not _need_data():
        st.stop()

    daily  = st.session_state.daily
    df_raw = st.session_state.df

    if st.button("🔄 Re-run Audit") or st.session_state.audit is None:
        with st.spinner("Running audit…"):
            st.session_state.audit = run_energy_audit(daily, df_raw)
    audit = st.session_state.audit

    cg, cs = st.columns([1, 2])
    with cg:
        st.plotly_chart(plot_efficiency_gauge(audit['efficiency_score']),
                        use_container_width=True, config={"displayModeBar": False})
    with cs:
        st.markdown("#### Audit Summary")
        a1, a2 = st.columns(2)
        rows = [
            ("Total kWh",       f"{audit['total_kwh']:.1f} kWh"),
            ("Avg Daily kWh",   f"{audit['avg_daily_kwh']:.2f} kWh"),
            ("Peak Day kWh",    f"{audit['max_daily_kwh']:.2f} kWh"),
            ("Std Dev",         f"{audit['std_daily_kwh']:.2f} kWh"),
            ("Total Bill",      f"₹{audit['total_bill_slab']:.0f}"),
            ("Avg Daily Bill",  f"₹{audit['avg_daily_bill']:.0f}"),
            ("High-Usage Days", f"{audit['high_consumption_days']} (>P95)"),
            ("Days Analysed",   f"{audit['total_days_analyzed']}"),
        ]
        for i, (lbl, val) in enumerate(rows):
            with (a1 if i % 2 == 0 else a2):
                st.markdown(
                    f"<div class='stat-row'><span class='stat-label'>{lbl}</span>"
                    f"<span class='stat-value'>{val}</span></div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.markdown("### 🔎 Audit Findings")
    for f in audit['findings']:
        sev = f['severity']
        ic  = "🔴" if sev == "HIGH" else "🟡" if sev == "MEDIUM" else "🟢"
        st.markdown(f"""
        <div class='rec-card {sev}'>
          <div class='rec-title'>{ic} {f['text']}</div>
          <span class='badge badge-{sev}'>{sev} Severity</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    ch1, ch2 = st.columns(2)
    with ch1:
        hourly = get_peak_hour_analysis(df_raw)
        st.plotly_chart(plot_peak_heatmap(hourly), use_container_width=True,
                        config={"displayModeBar": False})
    with ch2:
        fig_sub = plot_sub_metering(daily)
        if fig_sub:
            st.plotly_chart(fig_sub, use_container_width=True, config={"displayModeBar": False})
        else:
            st.plotly_chart(
                plot_dow_bar(audit.get('dow_pattern', {}), audit.get('peak_day_of_week', '')),
                use_container_width=True, config={"displayModeBar": False},
            )

    if audit.get('sub_metering_totals'):
        st.markdown("---")
        st.markdown("### 🔌 Sub-Meter Breakdown")
        sub_names = {
            'Sub_metering_1': '🍳 Kitchen & Freezer',
            'Sub_metering_2': '👕 Laundry & Climate',
            'Sub_metering_3': '🚿 Water Heater & AC',
        }
        total_sub = sum(audit['sub_metering_totals'].values()) or 1
        for sub, val in audit['sub_metering_totals'].items():
            pct = val / total_sub * 100
            st.markdown(
                f"<div class='stat-row'><span class='stat-label'>{sub_names.get(sub, sub)}</span>"
                f"<span class='stat-value'>{val:.0f} Wh ({pct:.1f}%)</span></div>",
                unsafe_allow_html=True,
            )
            st.progress(int(min(pct, 100)))


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 6 — OPTIMIZATION ADVISOR
# ═══════════════════════════════════════════════════════════════════════════
elif page == "💡 Optimization Advisor":
    st.markdown("<div class='page-title'><span class='grad-text'>💡 Optimization Advisor</span></div>",
                unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Actionable recommendations to cut your energy bills</div>",
                unsafe_allow_html=True)
    if not _need_data():
        st.stop()

    daily = st.session_state.daily
    preds = st.session_state.predictions

    if st.button("🔄 Refresh") or st.session_state.recommendations is None:
        with st.spinner("Generating recommendations…"):
            st.session_state.recommendations = generate_recommendations(daily, preds)
    recs = st.session_state.recommendations

    n_h = sum(1 for r in recs if r['priority'] == 'HIGH')
    n_m = sum(1 for r in recs if r['priority'] == 'MEDIUM')
    n_l = sum(1 for r in recs if r['priority'] == 'LOW')

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(kpi("Total Tips",      str(len(recs)), "",           "💡"),          unsafe_allow_html=True)
    with c2: st.markdown(kpi("High Priority",   str(n_h),       "Act now",    "🔴", "#ef4444"), unsafe_allow_html=True)
    with c3: st.markdown(kpi("Medium Priority", str(n_m),       "Plan soon",  "🟡", "#f59e0b"), unsafe_allow_html=True)
    with c4: st.markdown(kpi("Low Priority",    str(n_l),       "Long term",  "🟢", "#10b981"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    pri_filter = st.multiselect("Filter Priority", ["HIGH","MEDIUM","LOW"],
                                 default=["HIGH","MEDIUM","LOW"])

    for rec in recs:
        if rec['priority'] not in pri_filter:
            continue
        pc = {"HIGH":"#ef4444","MEDIUM":"#f59e0b","LOW":"#10b981"}[rec['priority']]
        bc = {"HIGH":"#fca5a5","MEDIUM":"#fcd34d","LOW":"#6ee7b7"}[rec['priority']]
        st.markdown(f"""
        <div class='rec-card {rec["priority"]}'>
          <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.35rem;'>
            <div class='rec-title'>{rec['icon']} {rec['title']}</div>
            <span class='badge badge-{rec["priority"]}'>{rec["priority"]}</span>
          </div>
          <div class='rec-detail'>{rec['detail']}</div>
          <div style='margin-top:0.5rem;font-size:0.8rem;color:#94a3b8;'>
            💰 Est. Savings: <strong style='color:{bc};'>{rec['saving_est']}</strong>
          </div>
        </div>""", unsafe_allow_html=True)

    with st.expander("📚 Energy Optimization Knowledge Base"):
        st.markdown("""
| Strategy | Description | Est. Savings |
|---|---|---|
| **Time-of-Use Shifting** | Run appliances at night (10PM–6AM) | 15–25% |
| **Solar PV** | Rooftop solar offsets daytime usage | 30–60% |
| **Smart Metering** | Real-time monitoring prevents waste | 5–15% |
| **LED Lighting** | Replace incandescents with LEDs | 70–80% lighting cost |
| **Inverter ACs** | Variable speed vs fixed speed | 20–40% |
| **Load Balancing** | Avoid simultaneous high-power appliances | 10–20% |
| **Insulation** | Wall/roof insulation reduces HVAC load | 10–25% |
""")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 7 — AI CHAT AGENT
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🤖 AI Chat Agent":
    st.markdown("<div class='page-title'><span class='grad-text'>🤖 EnergyIQ AI Advisor</span></div>",
                unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>Conversational AI powered by Llama 3.2 — ask anything about your energy</div>",
        unsafe_allow_html=True,
    )

    ollama_ok = check_ollama_available()
    if ollama_ok:
        st.success("✅ Ollama connected — Llama 3.2 is ready")
    else:
        st.warning(
            "⚠️ Ollama not detected. "
            "Install from [ollama.ai](https://ollama.ai), run `ollama pull llama3.2:1b`, then `ollama serve`. "
            "The AI will still respond with helpful guidance."
        )

    ctx = build_context_dict(
        daily=st.session_state.daily if st.session_state.data_loaded else None,
        predictions=st.session_state.predictions,
        audit=st.session_state.audit,
    )

    # Quick query buttons
    st.markdown("<p style='color:#cbd5e1;font-size:0.85rem;font-weight:600;'>⚡ Quick Queries:</p>",
                unsafe_allow_html=True)
    quick_cols = st.columns(3)
    quick_queries = list(QUICK_SUGGESTIONS.keys())
    quick_query = None
    for idx, q in enumerate(quick_queries[:6]):
        short = q[:38] + "…" if len(q) > 38 else q
        with quick_cols[idx % 3]:
            if st.button(short, key=f"q{idx}", use_container_width=True):
                quick_query = q

    st.markdown("<hr>", unsafe_allow_html=True)

    # Chat history
    chat_html = "<div class='chat-messages'>"
    for msg in st.session_state.chat_history:
        content = str(msg['content']).replace('\n', '<br>').replace('**', '')
        ts      = msg.get('ts', '')
        if msg['role'] == 'user':
            chat_html += f"""
            <div style='display:flex;justify-content:flex-end;margin-bottom:0.6rem;'>
              <div>
                <div class='chat-role' style='text-align:right;'>You · {ts}</div>
                <div class='chat-bubble-user'>{content}</div>
              </div>
              <div style='margin-left:0.6rem;font-size:1.3rem;'>👤</div>
            </div>"""
        else:
            chat_html += f"""
            <div style='display:flex;margin-bottom:0.6rem;'>
              <div style='margin-right:0.6rem;font-size:1.3rem;'>⚡</div>
              <div>
                <div class='chat-role'>EnergyIQ · {ts}</div>
                <div class='chat-bubble-ai'>{content}</div>
              </div>
            </div>"""

    if not st.session_state.chat_history:
        chat_html += """
        <div style='text-align:center;padding:2.5rem;color:#94a3b8;'>
          <div style='font-size:2rem;margin-bottom:0.5rem;'>💬</div>
          <div style='color:#cbd5e1;'>Ask me anything about your energy data!</div>
          <div style='font-size:0.8rem;margin-top:0.3rem;color:#94a3b8;'>
            e.g. "Why is my bill high?" · "Predict next month" · "How to save energy?"
          </div>
        </div>"""

    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)

    # Input
    inp_col, send_col = st.columns([5, 1])
    with inp_col:
        user_input = st.text_input(
            "msg", label_visibility="collapsed",
            placeholder="Ask EnergyIQ anything about your energy data…",
            key="chat_input",
        )
    with send_col:
        send_btn = st.button("Send ➤", use_container_width=True)

    query = quick_query or (user_input.strip() if send_btn and user_input.strip() else None)

    if query:
        ts = datetime.now().strftime("%H:%M")
        st.session_state.chat_history.append({'role': 'user', 'content': query, 'ts': ts})
        with st.spinner("EnergyIQ is thinking…"):
            response = answer_query(query, ctx, model=DEFAULT_MODEL)
        ts2 = datetime.now().strftime("%H:%M")
        st.session_state.chat_history.append({'role': 'ai', 'content': response, 'ts': ts2})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
