from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.retrieval.engine import RetrievalEngine

app = FastAPI(title="DocuMind Enterprise API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RetrievalEngine()

class QueryRequest(BaseModel):
    question: str

@app.get("/")
async def root():
    return {"message": "Welcome to DocuMind Enterprise API"}

@app.post("/query")
async def ask_question(request: QueryRequest):
    try:
        response = engine.get_query_response(request.question)
        return {
            "answer": response["answer"],
            "sources": [doc.metadata.get("source", "Unknown") for doc in response["context"]],
            "pages": [doc.metadata.get("page", 0) for doc in response["context"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
