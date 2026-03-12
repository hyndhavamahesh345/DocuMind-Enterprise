import os
from dotenv import load_dotenv
from langchain_community.document_loaders import UnstructuredPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

# Load environment variables
load_dotenv()

def ingest_docs():
    # 1. Initialize Pinecone
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key or not google_api_key:
        print("ERROR: API keys missing. Check your .env file.")
        return

    pc = Pinecone(api_key=api_key)

    # 2. Check/Create Index (Dimension 768 for Gemini text-embedding-004)
    if index_name not in [idx.name for idx in pc.list_indexes()]:
        print(f"INFO: Creating index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=768, 
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    # 3. Robust Loading with Unstructured.io
    print("INFO: Loading documents from data/docs using Unstructured...")
    loader = DirectoryLoader(
        'data/docs', 
        glob="./*.pdf", 
        loader_cls=UnstructuredPDFLoader,
        loader_kwargs={"mode": "elements", "strategy": "fast"}
    )
    documents = loader.load()
    
    if not documents:
        print("WARNING: No PDF documents found in data/docs.")
        return

    # 4. Advanced Chunking (RecursiveCharacterTextSplitter)
    print(f"INFO: Splitting {len(documents)} elements into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True # Crucial for citation accuracy
    )
    chunks = text_splitter.split_documents(documents)
    
    # 5. Embed and Upsert
    print(f"INFO: Uploading {len(chunks)} chunks to Pinecone...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    PineconeVectorStore.from_documents(
        chunks, 
        embeddings, 
        index_name=index_name
    )
    
    print("SUCCESS: Ingestion complete with robust parsing & Citations!")

if __name__ == "__main__":
    ingest_docs()
