import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import UnstructuredPDFLoader, DirectoryLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

def manual_ingest():
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key or not google_api_key:
        print("ERROR: API keys missing.")
        return

    pc = Pinecone(api_key=api_key)
    
    # Check index
    existing_indexes = pc.list_indexes().names()
    if index_name not in existing_indexes:
        print(f"Creating index {index_name}...")
        pc.create_index(name=index_name, dimension=3072, metric="cosine", spec=ServerlessSpec(cloud="aws", region="us-east-1"))
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(2)
    
    index = pc.Index(index_name)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    print("Loading PDFs...")
    loader = DirectoryLoader('data/docs', glob="./*.pdf", loader_cls=UnstructuredPDFLoader)
    documents = loader.load()
    
    print(f"Ingesting {len(documents)} documents...")
    for i, doc in enumerate(documents):
        print(f"Processing doc {i}...")
        emb = embeddings.embed_query(doc.page_content)
        # Pinecone metadata must be a dict
        metadata = {
            "text": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page_number", 1)
        }
        index.upsert(vectors=[{"id": f"vec_{i}", "values": emb, "metadata": metadata}])
    
    print("SUCCESS: Manual ingestion complete!")

if __name__ == "__main__":
    manual_ingest()
