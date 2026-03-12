import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from src.retrieval.engine import RetrievalEngine
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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

engine = RetrievalEngine()

class Message(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    question: str
    history: Optional[List[Message]] = []

@app.get("/")
async def root():
    return {"message": "DocuMind Enterprise API Online"}

@app.post("/query")
@limiter.limit("5/minute")
async def ask_question(request: QueryRequest, req: Request):
    """
    Streaming endpoint for the 'Typewriter effect'.
    """
    async def event_generator():
        # Convert Pydantic models to dicts for the engine
        chat_history = [m.model_dump() for m in request.history]
        
        for token in engine.get_streaming_response(request.question, chat_history):
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
