"""
LLM Agent Module
Conversational AI interface using Ollama Llama 3.2.
"""

import requests
import json
import numpy as np


import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

DEFAULT_MODEL = "llama-3.1-8b-instant"


def check_llm_available(model: str = DEFAULT_MODEL) -> bool:
    """Check if Groq API is configured."""
    return bool(GROQ_API_KEY)


def build_system_prompt(context: dict) -> str:
    """Build a rich system prompt with data context injected."""
    lines = [
        "You are EnergyIQ, an expert AI energy auditor and advisor.",
        "You specialise in electricity consumption analysis, billing, and energy efficiency.",
        "You always give specific, actionable, data-driven advice.",
        "Keep responses concise (3–5 sentences) unless a detailed breakdown is requested.",
        "",
        "=== CURRENT DATA CONTEXT ===",
    ]

    if context:
        if context.get('total_days'):
            lines.append(f"Dataset covers {context['total_days']} days of household power consumption data.")
        if context.get('avg_daily_kwh'):
            lines.append(f"Average daily consumption: {context['avg_daily_kwh']:.2f} kWh")
        if context.get('avg_daily_bill'):
            lines.append(f"Average daily bill: ₹{context['avg_daily_bill']:.2f}")
        if context.get('efficiency_score'):
            lines.append(f"Energy efficiency score: {context['efficiency_score']}/100")
        if context.get('pred_30day_kwh'):
            lines.append(f"Predicted consumption for next 30 days: {context['pred_30day_kwh']:.2f} kWh")
        if context.get('pred_30day_bill'):
            lines.append(f"Predicted bill for next 30 days: ₹{context['pred_30day_bill']:.2f}")
        if context.get('h_unit_mape'):
            lines.append(f"Model accuracy (MAPE): {context['h_unit_mape']:.1f}%")
        if context.get('peak_dow'):
            lines.append(f"Highest consumption day of week: {context['peak_dow']}")
        if context.get('findings'):
            lines.append(f"Key audit finding: {context['findings'][0]['text'] if context['findings'] else 'None'}")
        if context.get('tariff_info'):
            lines.append(f"Tariff info: Night Off-Peak ₹3.75, Morning Peak ₹5.50, Normal ₹4.75, Evening Peak ₹6.50")

    lines += [
        "",
        "Answer the user's question using this data context. If no data is available, say so and provide general advice.",
        "Always respond in a professional, friendly tone. Use ₹ for Indian Rupees and kWh for energy units.",
    ]
    return "\n".join(lines)


QUICK_SUGGESTIONS = {
    "Predict my electricity usage for the next 30 days.": "prediction",
    "Estimate my electricity bill for next month.": "bill",
    "Why is my electricity bill high?": "high_bill",
    "How can I reduce my electricity consumption?": "optimization",
    "Run an energy audit on my usage data.": "audit",
    "What are my peak usage hours?": "peak",
    "Compare TOU vs slab billing for me.": "billing_compare",
}


def query_llm(prompt: str, system: str = "", model: str = DEFAULT_MODEL,
                  stream: bool = False) -> str:
    """
    Call Groq API.
    Returns the response text or an error message.
    """
    if not GROQ_API_KEY:
        return "❌ GROQ_API_KEY is not configured. Please add it to your .env file."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    # Sanitize model: if it looks like an Ollama model (has a colon), force it to the Groq default
    if ":" in model:
        model = DEFAULT_MODEL

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 512,
        "top_p": 0.9,
        "stream": stream
    }
    try:
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            return data['choices'][0]['message']['content'].strip()
        else:
            return f"⚠️ Groq API returned status {resp.status_code}: {resp.text}"
    except requests.exceptions.Timeout:
        return "⏱️ Groq API response timed out. Please try again."
    except Exception as e:
        return f"❌ Error communicating with Groq API: {str(e)}"


def build_context_dict(daily=None, predictions=None, audit=None) -> dict:
    """Build a compact context dict to inject into the system prompt."""
    ctx = {}
    if daily is not None and len(daily) > 0:
        ctx['total_days'] = len(daily)
        ctx['avg_daily_kwh'] = float(daily['daily_energy_kwh'].mean())
        if 'daily_bill_slab' in daily.columns:
            ctx['avg_daily_bill'] = float(daily['daily_bill_slab'].mean())
        ctx['tariff_info'] = True

    if predictions:
        pred_kwh = predictions.get('h_unit_pred', np.array([]))
        pred_bill = predictions.get('h_bill_pred', np.array([]))
        if len(pred_kwh) > 0:
            ctx['pred_30day_kwh'] = float(np.sum(pred_kwh))
        if len(pred_bill) > 0:
            ctx['pred_30day_bill'] = float(np.sum(pred_bill))
        ctx['h_unit_mape'] = predictions.get('h_unit_mape', None)

    if audit:
        ctx['efficiency_score'] = audit.get('efficiency_score')
        ctx['peak_dow'] = audit.get('peak_day_of_week')
        ctx['findings'] = audit.get('findings', [])

    return ctx


def answer_query(user_question: str, context: dict, model: str = DEFAULT_MODEL) -> str:
    """Full pipeline: build system prompt + user question → LLM → response."""
    system = build_system_prompt(context)
    return query_llm(user_question, system=system, model=model)
