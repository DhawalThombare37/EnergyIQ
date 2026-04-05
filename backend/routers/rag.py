"""
RAG Router — Lightweight Keyword-based PDF search.
Optimized for 512MB RAM environments by replacing neural embeddings with TF-IDF.
"""
import os
import sys
import gc
import shutil
import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from modules.llm_agent import query_llm

router = APIRouter()

# Attempt to import lightweight RAG deps
try:
    from PyPDF2 import PdfReader
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../uploaded")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Global state for the lightweight RAG
# We store chunks and the TF-IDF matrix in memory (very small footprint)
_rag_state: dict = {
    "indexed": False,
    "filename": None,
    "chunks": [],
    "vectorizer": None,
    "tfidf_matrix": None
}

def _extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    texts = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            texts.append(str(extracted))
    return "".join(texts)

@router.get("/status")
def rag_status():
    return {
        "available": RAG_AVAILABLE,
        "indexed": _rag_state["indexed"],
        "filename": _rag_state["filename"],
    }

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG dependencies missing.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    
    try:
        pdf_path = os.path.join(UPLOAD_DIR, file.filename)
        content = await file.read()
        with open(pdf_path, "wb") as f:
            f.write(content)

        # Extract text
        text = _extract_text_from_pdf(pdf_path)
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from this PDF.")

        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_text(text)
        
        # Build Lightweight TF-IDF Index
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(chunks)

        # Update state
        _rag_state["chunks"] = chunks
        _rag_state["vectorizer"] = vectorizer
        _rag_state["tfidf_matrix"] = tfidf_matrix
        _rag_state["indexed"] = True
        _rag_state["filename"] = file.filename

        return {"success": True, "filename": file.filename, "chunks": len(chunks)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        gc.collect()

class AskRequest(BaseModel):
    question: str
    model: Optional[str] = "llama-3.1-8b-instant"

@router.post("/ask")
def ask_question(req: AskRequest):
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG dependencies missing.")
    if not _rag_state["indexed"] or not _rag_state["chunks"]:
        raise HTTPException(status_code=400, detail="No PDF indexed. Upload a PDF first.")
    
    try:
        # 1. Retrieve relevant chunks using TF-IDF similarity
        query_vec = _rag_state["vectorizer"].transform([req.question])
        similarities = cosine_similarity(query_vec, _rag_state["tfidf_matrix"]).flatten()
        
        # Get top 3 most relevant chunks
        top_indices = similarities.argsort()[-3:][::-1]
        relevant_chunks = [_rag_state["chunks"][i] for i in top_indices if similarities[i] > 0]
        
        # If no keywords match, fall back to the first two chunks as general context
        if not relevant_chunks:
            relevant_chunks = _rag_state["chunks"][:2]

        context = "\n---\n".join(relevant_chunks)
        
        # 2. Call Groq with the context
        prompt = f"Context from PDF:\n{context}\n\nQuestion: {req.question}\n\nAnswer based STRICTLY on the context above. If not found, say you don't know."
        answer = query_llm(prompt, system="You are an expert energy advisor.", model=req.model)
        
        return {"answer": answer, "filename": _rag_state["filename"]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        gc.collect()

@router.delete("/clear")
def clear_index():
    _rag_state["indexed"] = False
    _rag_state["filename"] = None
    _rag_state["chunks"] = []
    _rag_state["vectorizer"] = None
    _rag_state["tfidf_matrix"] = None
    gc.collect()
    return {"success": True}
