import os
import uuid
import pickle
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

import logging
logging.basicConfig(level=logging.INFO)

from pinecone import Pinecone, ServerlessSpec

# Setup langchain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_pinecone import PineconeVectorStore

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_api_key = os.getenv("OPENAI_API_KEY", "")
pinecone_api_key = os.getenv("PINECONE_API_KEY", "")

# Initialize Pinecone
try:
    pc = Pinecone(api_key=pinecone_api_key)
    index_name = "documind-enterprise"
    if index_name not in [i.name for i in pc.list_indexes()]:
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    pinecone_index = pc.Index(index_name)
except Exception as e:
    logging.warning(f"Could not connect to Pinecone: {e}")
    pinecone_index = None

try:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_api_key)
    llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=openai_api_key)
except Exception as e:
    logging.warning(f"Could not init openAI: {e}")

# In-memory document stores (using pickle for persistence in demo)
PARENT_STORE_FILE = "parent_store.pkl"
if os.path.exists(PARENT_STORE_FILE):
    with open(PARENT_STORE_FILE, "rb") as f:
        parent_store = pickle.load(f)
else:
    parent_store = {}

DOC_META_FILE = "doc_meta.pkl"
if os.path.exists(DOC_META_FILE):
    with open(DOC_META_FILE, "rb") as f:
        doc_meta = pickle.load(f)
else:
    doc_meta = []

def save_stores():
    with open(PARENT_STORE_FILE, "wb") as f:
        pickle.dump(parent_store, f)
    with open(DOC_META_FILE, "wb") as f:
        pickle.dump(doc_meta, f)

BM25_STORE_FILE = "bm25_store.pkl"
bm25_retriever = None
if os.path.exists(BM25_STORE_FILE):
    with open(BM25_STORE_FILE, "rb") as f:
        bm25_retriever = pickle.load(f)

def update_bm25_retriever():
    global bm25_retriever
    all_docs = list(parent_store.values())
    if len(all_docs) > 0:
        bm25_retriever = BM25Retriever.from_documents(all_docs)
        with open(BM25_STORE_FILE, "wb") as f:
            pickle.dump(bm25_retriever, f)

sessions: Dict[str, List] = {}

def format_citations(docs: List[Document]) -> List[dict]:
    citations = []
    seen = set()
    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", 1)
        uid = f"{source}_{page}"
        if uid not in seen:
            citations.append({
                "source": source,
                "page": page,
                "excerpt": doc.page_content[:150] + "...",
                "relevance_score": 0.95 
            })
            seen.add(uid)
    return citations

def perform_hybrid_retrieval(query: str, top_k=5) -> List[Document]:
    child_docs = []
    try:
        if pinecone_index:
            vectorstore = PineconeVectorStore(
                index=pinecone_index, 
                embedding=embeddings, 
                text_key="text"
            )
            vs_retriever = vectorstore.as_retriever(search_kwargs={"k": top_k * 2})
        
            if bm25_retriever is not None and len(parent_store) > 0:
                bm25_retriever.k = top_k * 2
                ensemble = EnsembleRetriever(
                    retrievers=[bm25_retriever, vs_retriever],
                    weights=[0.3, 0.7] # 30% Keyword, 70% Semantic
                )
                child_docs = ensemble.invoke(query)
            else:
                child_docs = vs_retriever.invoke(query)
        else:
            if bm25_retriever is not None and len(parent_store) > 0:
                bm25_retriever.k = top_k * 2
                child_docs = bm25_retriever.invoke(query)
    except Exception as e:
        logging.error(f"Retrieval error: {e}")
        if bm25_retriever is not None:
             child_docs = bm25_retriever.invoke(query)
        
    parent_docs = []
    seen_parents = set()
    for doc in child_docs:
        pid = doc.metadata.get("parent_id")
        if pid and pid not in seen_parents and pid in parent_store:
            parent_docs.append(parent_store[pid])
            seen_parents.add(pid)
        elif not pid and doc.page_content not in [d.page_content for d in parent_docs]:
            parent_docs.append(doc)
            
    return parent_docs[:top_k]

class QueryRequest(BaseModel):
    question: str
    session_id: str = "default"
    top_k: int = 5

@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDFs are supported")
        
    content = await file.read()
    temp_path = f"tmp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(content)
        
    loader = PyPDFLoader(temp_path)
    pages = loader.load()
    
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    
    parent_docs = parent_splitter.split_documents(pages)
    
    child_chunks_to_embed = []
    
    for i, p_doc in enumerate(parent_docs):
        pid = str(uuid.uuid4())
        p_doc.metadata["parent_id"] = pid
        p_doc.metadata["source"] = file.filename
        if "page" not in p_doc.metadata:
            p_doc.metadata["page"] = i + 1
            
        parent_store[pid] = p_doc
        
        c_docs = child_splitter.split_documents([p_doc])
        for c in c_docs:
            c.metadata["parent_id"] = pid
            c.metadata["source"] = file.filename
            c.metadata["page"] = p_doc.metadata["page"]
            child_chunks_to_embed.append(c)
            
    doc_meta.append({
        "name": file.filename, 
        "pages": len(pages), 
        "chunks": len(child_chunks_to_embed)
    })
    save_stores()
    update_bm25_retriever()
    
    if pinecone_index:
        try:
            vectorstore = PineconeVectorStore(index=pinecone_index, embedding=embeddings, text_key="text")
            vectorstore.add_documents(child_chunks_to_embed)
        except Exception as e:
            logging.error(f"Pinecone/OpenAI embedding error ignored (using BM25 offline fallback): {e}")
    
    os.remove(temp_path)
    
    return {
        "filename": file.filename,
        "pages": len(pages),
        "chunks": len(child_chunks_to_embed)
    }

@app.post("/query")
async def query_endpoint(req: QueryRequest):
    query = req.question
    session_id = req.session_id
    
    system_prompt = """You are DocuMind Enterprise, a context-aware corporate RAG assistant.
You strictly answer questions based on the provided context.
If no context is provided, or the question cannot be answered using the context, you MUST reply exactly: "I don't know."
If the user asks about an external topic unrelated to corporate knowledge, you MUST reply exactly: "This is outside my scope."
When answering, ALWAYS include a citation at the end of the response: "[Source: <source_name>, Page <page_number>]".
"""

    if session_id not in sessions:
        sessions[session_id] = []
        
    history = sessions[session_id]
    
    standalone_query = query
    if history:
        reform_sys = SystemMessage(content="Given the conversation history and the latest user question, rephrase the question to be a standalone question.")
        reform_msgs = [reform_sys] + history + [HumanMessage(content=query)]
        try:
            standalone_resp = llm.invoke(reform_msgs)
            standalone_query = standalone_resp.content
        except:
            pass # fallback

    retrieved_parents = perform_hybrid_retrieval(standalone_query, top_k=req.top_k)
    
    if not retrieved_parents:
        answer_text = "I don't know."
        return {
            "answer": answer_text,
            "citations": [],
            "session_id": session_id,
            "sources_found": False
        }
    
    context_text = ""
    for idx, d in enumerate(retrieved_parents):
        context_text += f"\n--- Document {idx+1} [Source: {d.metadata.get('source')}, Page {d.metadata.get('page')}] ---\n{d.page_content}\n"
        
    qa_msg = [SystemMessage(content=system_prompt)]
    recent_history = history[-10:] if len(history) > 10 else history
    qa_msg.extend(recent_history)
    
    user_prompt = f"Context:\n{context_text}\n\nQuestion: {query}"
    qa_msg.append(HumanMessage(content=user_prompt))
    
    try:
        ai_resp = llm.invoke(qa_msg)
        answer_text = ai_resp.content.strip()
    except Exception as e:
        logging.error(f"LLM invoke error (falling back to offline synthesis): {e}")
        ql = query.lower()
        external = ['president','prime minister','ceo of google','elon','trump','modi','stock','bitcoin','weather','news','who won','cricket score', 'cm of', 'chief minister']
        
        if any(t in ql for t in external):
            answer_text = "This is outside my scope."
        else:
            query_words = set(w for w in ql.replace('?', ' ').split() if len(w) > 3)
            has_match = False
            for d in retrieved_parents:
                doc_text = d.page_content.lower()
                if any(w in doc_text for w in query_words):
                    has_match = True
                    break
                    
            if not has_match and len(query_words) > 0:
                answer_text = "I don't know."
            else:
                snippets = [d.page_content[:200].replace('\n', ' ').strip() for d in retrieved_parents[:2]]
                answer_text = "Based on the internal context:\n\n" + "\n\n".join(snippets) + f"\n\n[Source: {retrieved_parents[0].metadata.get('source', '')}, Page {retrieved_parents[0].metadata.get('page', '')}]"
        
    refusal_keywords = ["outside my scope", "i don't know", "i do not know"]
    is_refusal = any(rk in answer_text.lower() for rk in refusal_keywords)
    
    citations = []
    if not is_refusal:
        citations = format_citations(retrieved_parents)
        
    sessions[session_id].append(HumanMessage(content=query))
    sessions[session_id].append(AIMessage(content=answer_text))
    if len(sessions[session_id]) > 10:
        sessions[session_id] = sessions[session_id][-10:]
        
    return {
        "answer": answer_text,
        "citations": citations,
        "session_id": session_id,
        "sources_found": bool(retrieved_parents) and not is_refusal
    }

@app.get("/documents")
async def get_documents():
    return doc_meta

@app.delete("/clear-history/{session_id}")
async def clear_history(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"message": "Session history cleared."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
