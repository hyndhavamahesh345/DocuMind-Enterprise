import json
import os
import logging
import shutil
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.ingestion.ingest import ingest_docs
from src.retrieval.engine import RetrievalEngine

# Initialize Limiter for Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="DocuMind Enterprise API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG Engine
engine = RetrievalEngine()

class Message(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    question: str
    history: Optional[List[Message]] = []

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "DocuMind-API"}

@app.get("/documents")
async def list_documents():
    docs_dir = "data/docs"
    if not os.path.exists(docs_dir):
        return {"documents": []}
    files = [f for f in os.listdir(docs_dir) if f.endswith('.pdf')]
    return {"documents": files}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    os.makedirs("data/docs", exist_ok=True)
    file_path = os.path.join("data/docs", file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Trigger the robust ingestion pipeline
    try:
        ingest_docs()
        return {"message": f"Successfully uploaded and ingested {file.filename}"}
    except Exception as e:
        print(f"UPLOAD ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/query")
@limiter.limit("5/minute")
async def ask_question(payload: QueryRequest, request: Request):
    """
    Streaming endpoint for the 'Typewriter effect'.
    """
    async def event_generator():
        # Convert Pydantic models to dicts for the engine
        chat_history = [m.model_dump() for m in payload.history]
        
        for token in engine.get_streaming_response(payload.question, chat_history):
            yield token

        # Yield sources at the end
        if hasattr(engine, 'last_context'):
            sources = {
                "sources": list(set([doc.metadata.get("source", "Unknown") for doc in engine.last_context])),
                "pages": list(set([doc.metadata.get("page", 0) for doc in engine.last_context]))
            }
            yield f"\n\nSOURCES: {json.dumps(sources)}"

    return StreamingResponse(event_generator(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
