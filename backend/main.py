"""
EnergyIQ — FastAPI Backend
Serves all ML, billing, audit, LLM chat, and PDF RAG endpoints.
"""
import sys
import os

# Make parent directory (existing modules) importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import data, predictions, billing, audit, advisor, chat, rag

app = FastAPI(title="EnergyIQ API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router,        prefix="/api/data",        tags=["Data"])
app.include_router(predictions.router, prefix="/api/predictions",  tags=["Predictions"])
app.include_router(billing.router,     prefix="/api/billing",      tags=["Billing"])
app.include_router(audit.router,       prefix="/api/audit",        tags=["Audit"])
app.include_router(advisor.router,     prefix="/api/advisor",      tags=["Advisor"])
app.include_router(chat.router,        prefix="/api/chat",         tags=["Chat"])
app.include_router(rag.router,         prefix="/api/rag",          tags=["RAG"])


@app.get("/")
def root():
    return {"status": "EnergyIQ API is running", "version": "2.0.0"}
