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

    # 2. Check/Create Index (Dimension 3072 for gemini-embedding-001)
    existing_indexes = pc.list_indexes().names()
    if index_name in existing_indexes:
        index_desc = pc.describe_index(index_name)
        if index_desc.dimension != 3072:
            print(f"WARNING: Dimension mismatch (found {index_desc.dimension}, need 3072). Recreating index...")
            pc.delete_index(index_name)
            import time
            while index_name in pc.list_indexes().names():
                time.sleep(2)
            existing_indexes = pc.list_indexes().names()

    if index_name not in existing_indexes:
        print(f"INFO: Creating index: {index_name}...")
        pc.create_index(
            name=index_name,
            dimension=3072, 
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    # Wait for index to be ready
    import time
    print("INFO: Checking index readiness...")
    while not pc.describe_index(index_name).status['ready']:
        time.sleep(5)
    print("SUCCESS: Index is ready!")

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
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    index = pc.Index(index_name)
    
    vectors = []
    for i, chunk in enumerate(chunks):
        content = chunk.page_content
        # Metadata must be a clean dictionary for Pinecone
        metadata = {
            "text": content,
            "source": chunk.metadata.get("source", "Unknown"),
            "page": chunk.metadata.get("page", 0),
            "start_index": chunk.metadata.get("start_index", 0)
        }
        
        # Embed the content
        emb = embeddings.embed_query(content)
        vectors.append({
            "id": f"chunk_{i}_{int(time.time())}", 
            "values": emb, 
            "metadata": metadata
        })
        
        # Upsert in batches of 50
        if len(vectors) >= 50:
            index.upsert(vectors=vectors)
            vectors = []
            
    if vectors:
        index.upsert(vectors=vectors)
    
    print("SUCCESS: Ingestion complete with robust parsing & Citations!")

if __name__ == "__main__":
    ingest_docs()
