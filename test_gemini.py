import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

load_dotenv()

def test():
    print("Testing Embeddings...")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        v = embeddings.embed_query("hello")
        print(f"Embeddings OK. Dim: {len(v)}")
    except Exception as e:
        print(f"Embeddings FAILED: {e}")

    print("\nTesting LLM...")
    try:
        llm = ChatGoogleGenerativeAI(model="models/gemini-flash-latest")
        res = llm.invoke("Hi")
        print(f"LLM OK: {res.content}")
    except Exception as e:
        print(f"LLM FAILED: {e}")

if __name__ == "__main__":
    test()
