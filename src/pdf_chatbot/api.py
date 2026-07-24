from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .core import KnowledgeBase


app = FastAPI(title="PDF Chatbot", version="0.1.0")
knowledge_base = KnowledgeBase()


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2_000)
    limit: int = Field(default=4, ge=1, le=10)


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "chunks": len(knowledge_base)}


@app.post("/documents")
async def upload_document(file: UploadFile = File(...)) -> dict[str, object]:
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(415, "Only PDF uploads are supported")
    data = await file.read(15 * 1024 * 1024 + 1)
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(413, "PDF is larger than 15 MB")
    try:
        count = knowledge_base.add_pdf_bytes(data, file.filename or "document.pdf")
    except Exception as exc:
        raise HTTPException(422, f"Could not read PDF: {exc}") from exc
    return {"filename": file.filename, "chunks_added": count, "total_chunks": len(knowledge_base)}


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, object]:
    if not len(knowledge_base):
        raise HTTPException(409, "Upload a PDF before asking a question")
    return knowledge_base.answer(request.question, request.limit)

