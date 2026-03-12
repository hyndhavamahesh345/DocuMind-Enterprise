# DocuMind Enterprise | Knowledge Hub

DocuMind Enterprise is a production-grade, locally-hosted Corporate Brain. It uses **Retrieval-Augmented Generation (RAG)**, empowered by Google's latest **Gemini** models and a Pinecone vector database, to allow employees to upload and instantly query company manuals, HR policies, and handbooks.

## 🚀 Key Features

*   **Dynamic Knowledge Base**: Upload PDFs directly from the UI. The server automatically chunks, embeds (using `gemini-embedding-001`), and syncs the data to the Pinecone index.
*   **Information Extraction Chat**: A split-view AI chat interface that streams answers back utilizing `gemini-flash-latest` for lightning-fast inference.
*   **Page-Level Citations**: Never hallucinate. Every extracted piece of information contains a linked citation tracing back to the exact PDF page.
*   **Rate-Limited API**: Robust FastAPI backend protected by SlowAPI to prevent spam and ensure stable resource consumption.
*   **Premium Next-Gen UI**: Built with pure HTML/CSS and glassmorphism styling for a developer-crafted, standalone knowledge hub experience.

## 🛠️ Architecture

*   **Frontend**: Vanilla HTML/CSS/JS (Lightweight, single-file `index.html`)
*   **Backend**: FastAPI, Uvicorn, Python
*   **AI Framework**: LangChain
*   **Vector Database**: Pinecone (Serverless)
*   **Models**: 
    *   Embeddings: `models/gemini-embedding-001` (3072 dimensions)
    *   LLM: `models/gemini-flash-latest`

## ⚙️ Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hyndhavamahesh345/DocuMind-Enterprise.git
   cd DocuMind-Enterprise
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory (use `.env.template` as a guide):
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX_NAME=documind-enterprise-gemini
   ```

4. **Run the Enterprise API & Hub:**
   ```bash
   python src/api/main.py
   ```
   *The application will automatically start a server on `http://127.0.0.1:8000`. Visiting this URL in your browser will load the complete Knowledge Hub UI.*

## 📂 Project Structure

*   `/src/api/main.py` - FastAPI server routing, rate limiting, and UI rendering.
*   `/src/ingestion/ingest.py` - Core logic for parsing PDFs (via Unstructured.io) and vectorizing.
*   `/src/retrieval/engine.py` - LangChain agent setup, History-Aware retrieval, and streaming response generator.
*   `index.html` - The unified Corporate Brain Dashboard view.
*   `data/docs/` - Auto-created directory where uploaded PDFs are stored for processing.

## 🚀 Usage

1. Open `http://127.0.0.1:8000`.
2. Click **Sync New Manual** to upload your own corporate PDFs.
3. Once the sync completes, ask questions in the chat to extract insights perfectly cited from your documents!
