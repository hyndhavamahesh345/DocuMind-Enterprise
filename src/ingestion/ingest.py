import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
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
        print("ERROR: API keys missing (PINECONE_API_KEY or GOOGLE_API_KEY). Please check your .env file.")
        return

    pc = Pinecone(api_key=api_key)

    # Create index if it doesn't exist
    # Note: Gemini embeddings (text-embedding-004) use 768 dimensions
    if index_name not in pc.list_indexes().names():
        print(f"INFO: Creating index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=3072, 
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    # 2. Load Documents
    print("INFO: Loading documents from data/docs...")
    loader = DirectoryLoader('data/docs', glob="./*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    
    if not documents:
        print("WARNING: No PDF documents found in data/docs.")
        return

    # 3. Split Documents into Chunks
    print(f"INFO: Splitting {len(documents)} document pages into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"SUCCESS: Created {len(chunks)} chunks.")

    # 4. Create Embeddings and Store in Pinecone
    print("INFO: Uploading to Pinecone using Gemini Embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    vectorstore = PineconeVectorStore.from_documents(
        chunks, 
        embeddings, 
        index_name=index_name
    )
    
    print("SUCCESS: Ingestion complete!")

if __name__ == "__main__":
    ingest_docs()
