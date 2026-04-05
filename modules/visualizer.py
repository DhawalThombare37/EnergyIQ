"""
Visualizer Module — plotly 6.x compatible, all charts dark-themed with proper text contrast.
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ── Design tokens
BG        = 'rgba(0,0,0,0)'
GRID      = 'rgba(255,255,255,0.08)'
TEXT      = '#e2e8f0'           # light slate — always visible on dark bg
TEXT_MUT  = '#94a3b8'
CYAN      = '#00d4ff'
PURPLE    = '#9b59fb'
GREEN     = '#10b981'
AMBER     = '#f59e0b'
RED       = '#ef4444'
PINK      = '#ec4899'

BASE = dict(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font=dict(family='Inter, sans-serif', color=TEXT, size=12),
    margin=dict(l=50, r=30, t=55, b=50),
    xaxis=dict(
        gridcolor=GRID, showline=False, zeroline=False,
        tickfont=dict(size=10, color=TEXT), title_font=dict(color=TEXT),
    ),
    yaxis=dict(
        gridcolor=GRID, showline=False, zeroline=False,
        tickfont=dict(size=10, color=TEXT), title_font=dict(color=TEXT),
    ),
    legend=dict(
        bgcolor='rgba(10,14,26,0.8)',
        bordercolor='rgba(255,255,255,0.15)',
        borderwidth=1,
        font=dict(color=TEXT),
    ),
    hovermode='x unified',
    title_font=dict(color=TEXT, size=14, family='Inter, sans-serif'),
)


def _fig(title='', **kwargs) -> go.Figure:
    fig = go.Figure()
    layout = dict(BASE)
    layout.update(kwargs)
    if title:
        layout['title'] = dict(text=title, font=dict(color=TEXT, size=14))
    fig.update_layout(**layout)
    return fig


def plot_actual_vs_predicted(dates, actual, predicted,
                              title='Actual vs Predicted',
                              actual_label='Actual',
                              pred_label='Predicted',
                              y_label='Value'):
    fig = _fig(title=title, yaxis_title=y_label)
    fig.add_trace(go.Scatter(
        x=dates, y=list(actual), mode='lines+markers', name=actual_label,
        line=dict(color=CYAN, width=2.5),
        marker=dict(size=5, color=CYAN),
        fill='tozeroy', fillcolor='rgba(0,212,255,0.08)',
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=list(predicted), mode='lines+markers', name=pred_label,
        line=dict(color=PURPLE, width=2.5, dash='dot'),
        marker=dict(size=5, symbol='x', color=PURPLE),
    ))
    return fig


def plot_daily_trend(daily: pd.DataFrame):
    fig = _fig(title='Daily Energy & Bill Trend', yaxis_title='Energy (kWh)')
    fig.add_trace(go.Scatter(
        x=daily['date'], y=daily['daily_energy_kwh'],
        mode='lines', name='Daily kWh',
        line=dict(color=CYAN, width=2),
        fill='tozeroy', fillcolor='rgba(0,212,255,0.10)',
    ))
    if 'daily_bill_slab' in daily.columns:
        fig.add_trace(go.Scatter(
            x=daily['date'], y=daily['daily_bill_slab'],
            mode='lines', name='Daily Bill (₹)',
            line=dict(color=AMBER, width=2),
            yaxis='y2',
        ))
        fig.update_layout(
            yaxis2=dict(
                overlaying='y', side='right', title_text='Bill (₹)',
                gridcolor='rgba(0,0,0,0)', showline=False, zeroline=False,
                tickfont=dict(size=10, color=AMBER),
                title_font=dict(color=AMBER),
            ),
        )
    return fig


def plot_bill_projection(dates, predicted_bills, predicted_kwh=None):
    colors = [CYAN if i % 2 == 0 else PURPLE for i in range(len(dates))]
    fig = _fig(title='Predicted Bill Projection', yaxis_title='Bill (₹)')
    fig.add_trace(go.Bar(
        x=dates, y=list(predicted_bills),
        name='Daily Bill (₹)',
        marker=dict(color=colors, opacity=0.85),
    ))
    if predicted_kwh is not None:
        fig.add_trace(go.Scatter(
            x=dates, y=list(predicted_kwh),
            mode='lines', name='kWh',
            line=dict(color=GREEN, width=2),
            yaxis='y2',
        ))
        fig.update_layout(
            yaxis2=dict(
                overlaying='y', side='right', title_text='kWh',
                gridcolor='rgba(0,0,0,0)', showline=False, zeroline=False,
                tickfont=dict(size=10, color=GREEN),
                title_font=dict(color=GREEN),
            ),
        )
    return fig


def plot_peak_heatmap(hourly_df: pd.DataFrame):
    hours = hourly_df['hour'].tolist()
    power = hourly_df['avg_power'].tolist()
    fig = _fig(title='Hourly Average Power Distribution',
               xaxis_title='Hour of Day', yaxis_title='Avg Power (kW)')
    fig.add_trace(go.Bar(
        x=hours, y=power,
        marker=dict(
            color=power,
            colorscale=[[0, 'rgba(0,212,255,0.5)'], [0.5, PURPLE], [1.0, RED]],
            showscale=True,
            colorbar=dict(
                title=dict(text='kW', font=dict(color=TEXT)),
                tickfont=dict(color=TEXT),
            ),
        ),
        name='Avg Power (kW)',
    ))
    fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(0, 24)),
            ticktext=[f'{h:02d}:00' for h in range(24)],
            tickangle=-45,
            tickfont=dict(size=9, color=TEXT),
            gridcolor=GRID,
        ),
    )
    return fig


def plot_tariff_breakdown(breakdown: dict):
    slot_colors = {
        'Night_Off_Peak':  CYAN,
        'Morning_Peak':    AMBER,
        'Forenoon_Normal': GREEN,
        'Evening_Peak':    RED,
    }
    labels = list(breakdown.get('absolute', {}).keys())
    values = list(breakdown.get('absolute', {}).values())
    colors_list = [slot_colors.get(l, PURPLE) for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(
            colors=colors_list,
            line=dict(color='rgba(8,12,24,0.6)', width=2),
        ),
        textinfo='label+percent',
        textfont=dict(size=12, color='#ffffff'),
        hovertemplate='%{label}<br>₹%{value:.1f} (%{percent})<extra></extra>',
    ))
    fig.update_layout(
        title=dict(text='Cost by Tariff Slot', font=dict(color=TEXT, size=14)),
        paper_bgcolor=BG,
        font=dict(color=TEXT),
        showlegend=True,
        legend=dict(font=dict(color=TEXT), bgcolor='rgba(10,14,26,0.8)'),
        annotations=[dict(
            text='Cost<br>Split',
            x=0.5, y=0.5,
            font=dict(size=13, color=TEXT),
            showarrow=False,
        )],
    )
    return fig


def plot_efficiency_gauge(score: float):
    if score >= 75:
        bar_color, label = GREEN,  'Excellent'
    elif score >= 60:
        bar_color, label = CYAN,   'Good'
    elif score >= 40:
        bar_color, label = AMBER,  'Fair'
    else:
        bar_color, label = RED,    'Poor'

    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=score,
        number=dict(suffix='/100', font=dict(size=30, color=TEXT)),
        gauge=dict(
            axis=dict(
                range=[0, 100], tickwidth=1,
                tickcolor=TEXT,
                tickfont=dict(color=TEXT, size=10),
            ),
            bar=dict(color=bar_color, thickness=0.3),
            bgcolor='rgba(255,255,255,0.04)',
            borderwidth=0,
            steps=[
                dict(range=[0,  40],  color='rgba(239,68,68,0.12)'),
                dict(range=[40, 70],  color='rgba(245,158,11,0.12)'),
                dict(range=[70, 100], color='rgba(16,185,129,0.12)'),
            ],
            threshold=dict(line=dict(color=TEXT, width=2), thickness=0.75, value=70),
        ),
        title=dict(text=f'Efficiency: {label}', font=dict(size=13, color=bar_color)),
    ))
    fig.update_layout(
        height=260,
        paper_bgcolor=BG,
        font=dict(color=TEXT, family='Inter, sans-serif'),
        margin=dict(l=30, r=30, t=20, b=10),
    )
    return fig


def plot_sub_metering(daily: pd.DataFrame):
    sub_cols = ['Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3']
    available = [c for c in sub_cols if c in daily.columns]
    if not available:
        return None
    labels_map = {
        'Sub_metering_1': 'Kitchen & Freezer',
        'Sub_metering_2': 'Laundry & HVAC',
        'Sub_metering_3': 'Water Heater & AC',
    }
    fig = _fig(title='Sub-Meter Consumption', yaxis_title='Energy (Wh)')
    palette = [CYAN, PURPLE, GREEN]
    for i, col in enumerate(available):
        fig.add_trace(go.Scatter(
            x=daily['date'], y=daily[col],
            mode='lines', name=labels_map.get(col, col),
            line=dict(color=palette[i], width=1.8),
        ))
    return fig


def plot_monthly_bar(daily: pd.DataFrame):
    if 'month' not in daily.columns:
        return None
    monthly = daily.groupby('month')['daily_energy_kwh'].mean().reset_index()
    month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                   7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
    monthly['month_name'] = monthly['month'].map(month_names)
    vals = monthly['daily_energy_kwh'].tolist()
    mn   = min(vals) if vals else 0
    mx   = max(vals) if vals else 1

    fig = _fig(title='Monthly Avg Daily Consumption', yaxis_title='Avg kWh/day')
    fig.add_trace(go.Bar(
        x=monthly['month_name'],
        y=vals,
        marker=dict(
            color=vals,
            colorscale=[[0, CYAN], [0.5, PURPLE], [1.0, RED]],
            cmin=mn, cmax=mx,
            showscale=False,
        ),
        text=[f'{v:.1f}' for v in vals],
        textposition='outside',
        textfont=dict(color=TEXT, size=10),
    ))
    fig.update_layout(showlegend=False)
    return fig


def plot_dow_bar(dow_pattern: dict, peak_dow: str):
    days  = list(dow_pattern.keys())
    vals  = list(dow_pattern.values())
    colors = [RED if d == peak_dow else CYAN for d in days]
    fig = _fig(title='Day-of-Week Consumption Pattern', yaxis_title='Avg kWh/day')
    fig.add_trace(go.Bar(
        x=days, y=vals,
        marker=dict(color=colors, opacity=0.85),
        text=[f'{v:.2f}' for v in vals],
        textposition='outside',
        textfont=dict(color=TEXT, size=10),
    ))
    fig.update_layout(showlegend=False)
    return fig
