"""
RAG Router — PDF upload, FAISS indexing, and question answering.
Based on app2.py (PDF RAG Chatbot feature).
"""
import os
import sys
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

router = APIRouter()

# Attempt to import RAG deps (may not be installed yet)
try:
    from PyPDF2 import PdfReader
    from langchain_community.embeddings import FastEmbedEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_community.llms import Ollama
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain.chains import RetrievalQA
    from langchain.llms.base import LLM
    from typing import Any, List, Mapping, Optional
    from modules.llm_agent import query_llm
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


class GroqLLM(LLM):
    model_name: str = "llama-3.1-8b-instant"

    @property
    def _llm_type(self) -> str:
        return "groq"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        # We ignore 'stop' for now as our query_llm is simple, 
        # but you can pass more params if needed.
        return query_llm(prompt, system="You are a helpful assistant answering questions based on provided PDF context.", model=self.model_name)

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"model_name": self.model_name}

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../uploaded")
FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), "../../faiss_index")
os.makedirs(UPLOAD_DIR, exist_ok=True)

_rag_state: dict = {"indexed": False, "filename": None, "qa_chain": None}
_embeddings = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        if not RAG_AVAILABLE:
            return None
        _embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    return _embeddings


def _extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    texts = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            texts.append(str(extracted))
    return "".join(texts)


def _build_qa_chain(model: str = "llama-3.1-8b-instant"):
    embeddings = _get_embeddings()
    vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    retriever = vector_store.as_retriever()
    llm = GroqLLM(model_name=model)
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff")
    return qa_chain


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
        raise HTTPException(status_code=503, detail="RAG dependencies not installed. Run: pip install PyPDF2 langchain langchain-community faiss-cpu fastembed")
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

        # Build FAISS index
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(text)
        embeddings = _get_embeddings()
        vector_store = FAISS.from_texts(chunks, embedding=embeddings)
        vector_store.save_local(FAISS_INDEX_PATH)

        # Build QA chain
        _rag_state["qa_chain"] = _build_qa_chain()
        _rag_state["indexed"] = True
        _rag_state["filename"] = file.filename

        return {"success": True, "filename": file.filename, "chunks": len(chunks)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class AskRequest(BaseModel):
    question: str
    model: Optional[str] = "llama-3.1-8b-instant"


@router.post("/ask")
def ask_question(req: AskRequest):
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG dependencies not installed.")
    if not _rag_state["indexed"]:
        raise HTTPException(status_code=400, detail="No PDF indexed. Upload a PDF first.")
    try:
        if _rag_state["qa_chain"] is None:
            _rag_state["qa_chain"] = _build_qa_chain(req.model or "llama-3.1-8b-instant")
        answer = _rag_state["qa_chain"].run(req.question)
        return {"answer": answer, "filename": _rag_state["filename"]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/clear")
def clear_index():
    _rag_state["indexed"] = False
    _rag_state["filename"] = None
    _rag_state["qa_chain"] = None
    if os.path.exists(FAISS_INDEX_PATH):
        shutil.rmtree(FAISS_INDEX_PATH, ignore_errors=True)
    return {"success": True}
