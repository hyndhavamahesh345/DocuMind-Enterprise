# DocuMind Enterprise - Context-Aware Corporate Brain

DocuMind Enterprise is a RAG (Retrieval-Augmented Generation) system designed to provide instant, accurate answers from corporate documents with page-level citations.

## 🚀 Features
- **Accurate Retrieval**: Uses Pinecone vector database and Google Gemini embeddings (`models/gemini-embedding-001`).
- **Hallucination Prevention**: Strictly answers based on provided context using Gemini 1.5 Flash.
- **Citations**: Provides page numbers and source document names.
- **Premium UI**: Modern, dark-mode chat interface included.

## 📁 Project Structure
- `data/docs/`: Put your PDF documents here for ingestion.
- `src/ingestion/ingest.py`: Script to process documents and upload to Pinecone.
- `src/retrieval/engine.py`: Logic for searching and generating answers using LCEL.
- `src/api/main.py`: FastAPI endpoints.
- `index.html`: Premium frontend interface.

## 🛠️ Setup
1. Clone the repository.
2. Create a `.env` file based on `.env.template` and add your **GOOGLE_API_KEY** and **PINECONE_API_KEY**.
3. Install dependencies: `pip install -r requirements.txt`
4. Run ingestion: `python src/ingestion/ingest.py`
5. Start API: `$env:PYTHONPATH="."; python src/api/main.py`
6. Open `index.html` in your browser to start chatting!
